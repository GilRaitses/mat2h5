function reversals = detect_reversals(times, SpeedRunVel, min_duration)
% DETECT_REVERSALS Detect reverse crawl events from SpeedRunVel time series
%
%   ORIGINAL MASON SCRIPT: Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m
%   Location: scripts/2025-11-20/mason's scritps/
%
%   Original detection logic:
%       % A reversal is when the larva moves backward (SpeedRunVel < 0)
%       % The duration threshold filters out brief noise/wobbles
%       reversal_mask = SpeedRunVel < 0;
%       % Find contiguous negative regions >= min_duration
%
%   The 3-second minimum duration is based on Mason's observation that
%   shorter negative SpeedRunVel periods are typically noise or brief
%   hesitations, not true reverse crawling behavior.
%
%   reversals = detect_reversals(times, SpeedRunVel, min_duration)
%
%   A reversal is defined as a continuous period where SpeedRunVel < 0
%   lasting at least min_duration seconds.
%
%   Inputs:
%       times        - Time array, shape (1, N)
%       SpeedRunVel  - Signed velocity array, shape (1, N)
%       min_duration - Minimum duration for reversal (seconds), default 3.0
%
%   Outputs:
%       reversals - Struct array with fields:
%           .start_idx   - Start index
%           .end_idx     - End index
%           .start_time  - Start time
%           .end_time    - End time
%           .duration    - Duration in seconds
%           .mean_speed  - Mean absolute speed during reversal
%
%   Reference: Mason Klein's reverse crawl detection method
%   Documentation: scripts/2025-11-24/mason_script_4_behavior_analysis.qmd
%   Python equivalent: engineer_data.detect_reversals()

if nargin < 3
    min_duration = 3.0;
end

% Ensure row vectors
times = times(:)';
SpeedRunVel = SpeedRunVel(:)';

if isempty(times) || isempty(SpeedRunVel)
    reversals = struct('start_idx', {}, 'end_idx', {}, 'start_time', {}, ...
                       'end_time', {}, 'duration', {}, 'mean_speed', {});
    return;
end

reversals = struct('start_idx', {}, 'end_idx', {}, 'start_time', {}, ...
                   'end_time', {}, 'duration', {}, 'mean_speed', {});

in_reversal = false;
start_idx = [];
start_time = [];

for i = 1:length(SpeedRunVel)
    is_negative = SpeedRunVel(i) < 0;
    
    if is_negative && ~in_reversal
        % Start of reversal
        in_reversal = true;
        start_idx = i;
        start_time = times(i);
        
    elseif ~is_negative && in_reversal
        % End of reversal
        in_reversal = false;
        if ~isempty(start_idx)
            duration = times(i) - start_time;
            if duration >= min_duration
                mean_speed = mean(abs(SpeedRunVel(start_idx:i-1)));
                reversals(end+1).start_idx = start_idx;
                reversals(end).end_idx = i - 1;
                reversals(end).start_time = start_time;
                reversals(end).end_time = times(i - 1);
                reversals(end).duration = duration;
                reversals(end).mean_speed = mean_speed;
            end
        end
        start_idx = [];
    end
end

% Handle reversal extending to end of data
if in_reversal && ~isempty(start_idx)
    duration = times(end) - start_time;
    if duration >= min_duration
        mean_speed = mean(abs(SpeedRunVel(start_idx:end)));
        reversals(end+1).start_idx = start_idx;
        reversals(end).end_idx = length(SpeedRunVel);
        reversals(end).start_time = start_time;
        reversals(end).end_time = times(end);
        reversals(end).duration = duration;
        reversals(end).mean_speed = mean_speed;
    end
end

end

%% Test Harness
function test_detect_reversals()
    % Test case 1: No reversals (all positive)
    times = 0:0.1:10;
    SpeedRunVel = ones(size(times));
    
    reversals = detect_reversals(times, SpeedRunVel, 3.0);
    
    assert(isempty(reversals), 'Test 1 failed: should have no reversals');
    fprintf('Test 1 passed: no reversals (all positive)\n');
    
    % Test case 2: Single long reversal
    times = 0:0.1:10;
    SpeedRunVel = ones(size(times));
    SpeedRunVel(21:71) = -1;  % Negative from t=2 to t=7 (5 seconds)
    
    reversals = detect_reversals(times, SpeedRunVel, 3.0);
    
    assert(length(reversals) == 1, 'Test 2 failed: should have 1 reversal');
    assert(abs(reversals(1).duration - 5.0) < 0.2, 'Test 2 failed: duration should be ~5s');
    fprintf('Test 2 passed: single long reversal\n');
    
    % Test case 3: Short reversal (below threshold)
    times = 0:0.1:10;
    SpeedRunVel = ones(size(times));
    SpeedRunVel(21:31) = -1;  % Negative from t=2 to t=3 (1 second, below threshold)
    
    reversals = detect_reversals(times, SpeedRunVel, 3.0);
    
    assert(isempty(reversals), 'Test 3 failed: short reversal should be ignored');
    fprintf('Test 3 passed: short reversal ignored\n');
    
    % Test case 4: Multiple reversals
    times = 0:0.1:20;
    SpeedRunVel = ones(size(times));
    SpeedRunVel(11:51) = -1;   % Reversal 1: t=1 to t=5 (4 seconds)
    SpeedRunVel(101:151) = -1; % Reversal 2: t=10 to t=15 (5 seconds)
    
    reversals = detect_reversals(times, SpeedRunVel, 3.0);
    
    assert(length(reversals) == 2, 'Test 4 failed: should have 2 reversals');
    fprintf('Test 4 passed: multiple reversals\n');
    
    % Test case 5: Reversal at end of data
    times = 0:0.1:10;
    SpeedRunVel = ones(size(times));
    SpeedRunVel(61:end) = -1;  % Negative from t=6 to end (4 seconds)
    
    reversals = detect_reversals(times, SpeedRunVel, 3.0);
    
    assert(length(reversals) == 1, 'Test 5 failed: should detect reversal at end');
    fprintf('Test 5 passed: reversal at end of data\n');
    
    fprintf('\nAll tests passed for detect_reversals!\n');
end

