function turn_events = detect_turn_events(times, HeadUnitVec, angle_threshold, min_frames)
% DETECT_TURN_EVENTS Detect turn/reorientation events from heading angle changes
%
%   ORIGINAL MASON SCRIPT: Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m
%   Location: scripts/2025-11-20/mason's scritps/
%
%   Original turn detection (from Mason's script):
%       theta = acos(CosThetaFactor);
%       TurnFactor1 = pi/4;   % 45 degrees
%       TurnFactor2 = 3*pi/4; % 135 degrees
%       % Turn detected when: TurnFactor1 < abs(theta) < TurnFactor2
%
%   Note: Mason's scripts detect TURN EVENTS (binary), not turn RATE.
%   Turn rate computation is in separate scripts (binReorientationTimesWithCycles.m).
%
%   turn_events = detect_turn_events(times, HeadUnitVec, angle_threshold, min_frames)
%
%   A turn is detected when the cumulative heading angle change exceeds
%   the threshold within a sliding window.
%
%   Inputs:
%       times           - Time array, shape (1, N)
%       HeadUnitVec     - Normalized heading vectors, shape (2, N)
%       angle_threshold - Minimum angle change (degrees), default 45.0
%       min_frames      - Minimum frames between detected turns, default 3
%
%   Outputs:
%       turn_events - Struct array with fields:
%           .idx          - Index of turn
%           .time         - Time of turn
%           .angle_change - Magnitude of angle change (degrees)
%           .direction    - 'left' or 'right'
%
%   Reference: Mason Klein's behavior analysis methods
%   Documentation: scripts/2025-11-24/mason_script_4_behavior_analysis.qmd
%   Python equivalent: engineer_data.detect_turn_events()

if nargin < 3
    angle_threshold = 45.0;
end
if nargin < 4
    min_frames = 3;
end

% Initialize output
turn_events = struct('idx', {}, 'time', {}, 'angle_change', {}, 'direction', {});

if size(HeadUnitVec, 2) < min_frames
    return;
end

% Compute heading angles (radians)
angles = atan2(HeadUnitVec(2, :), HeadUnitVec(1, :));

% Unwrap angles to handle -pi to pi discontinuity
angles_unwrapped = unwrap(angles);

% Compute angle changes (radians to degrees)
angle_diff = diff(angles_unwrapped);
angle_diff_deg = rad2deg(angle_diff);

i = 1;
max_window = 30;  % Maximum frames to look ahead

while i <= length(angle_diff) - min_frames
    % Look for cumulative angle change exceeding threshold
    cumsum_angle = 0;
    found = false;
    
    for j = i:min(i + max_window - 1, length(angle_diff))
        cumsum_angle = cumsum_angle + angle_diff_deg(j);
        
        if abs(cumsum_angle) >= angle_threshold
            if cumsum_angle > 0
                direction = 'left';
            else
                direction = 'right';
            end
            
            turn_events(end+1).idx = i;
            turn_events(end).time = times(i);
            turn_events(end).angle_change = abs(cumsum_angle);
            turn_events(end).direction = direction;
            
            i = j + min_frames;  % Skip ahead to avoid double-counting
            found = true;
            break;
        end
    end
    
    if ~found
        i = i + 1;
    end
end

end

%% Test Harness
function test_detect_turn_events()
    % Test case 1: No turns (constant heading)
    times = 0:0.1:10;
    N = length(times);
    HeadUnitVec = [ones(1, N); zeros(1, N)];  % Always pointing right
    
    turn_events = detect_turn_events(times, HeadUnitVec, 45.0);
    
    assert(isempty(turn_events), 'Test 1 failed: should have no turns');
    fprintf('Test 1 passed: no turns (constant heading)\n');
    
    % Test case 2: Single 90 degree left turn
    times = 0:0.1:5;
    N = length(times);
    HeadUnitVec = zeros(2, N);
    
    % First half: pointing right [1, 0]
    HeadUnitVec(1, 1:25) = 1;
    HeadUnitVec(2, 1:25) = 0;
    
    % Second half: pointing up [0, 1] (90 degree left turn)
    HeadUnitVec(1, 26:end) = 0;
    HeadUnitVec(2, 26:end) = 1;
    
    turn_events = detect_turn_events(times, HeadUnitVec, 45.0);
    
    assert(length(turn_events) >= 1, 'Test 2 failed: should detect turn');
    assert(strcmp(turn_events(1).direction, 'left'), 'Test 2 failed: should be left turn');
    fprintf('Test 2 passed: single left turn\n');
    
    % Test case 3: Single 90 degree right turn
    times = 0:0.1:5;
    N = length(times);
    HeadUnitVec = zeros(2, N);
    
    % First half: pointing right [1, 0]
    HeadUnitVec(1, 1:25) = 1;
    HeadUnitVec(2, 1:25) = 0;
    
    % Second half: pointing down [0, -1] (90 degree right turn)
    HeadUnitVec(1, 26:end) = 0;
    HeadUnitVec(2, 26:end) = -1;
    
    turn_events = detect_turn_events(times, HeadUnitVec, 45.0);
    
    assert(length(turn_events) >= 1, 'Test 3 failed: should detect turn');
    assert(strcmp(turn_events(1).direction, 'right'), 'Test 3 failed: should be right turn');
    fprintf('Test 3 passed: single right turn\n');
    
    % Test case 4: Small turn below threshold
    times = 0:0.1:5;
    N = length(times);
    angles = linspace(0, deg2rad(30), N);  % Only 30 degree turn
    HeadUnitVec = [cos(angles); sin(angles)];
    
    turn_events = detect_turn_events(times, HeadUnitVec, 45.0);
    
    assert(isempty(turn_events), 'Test 4 failed: small turn should be ignored');
    fprintf('Test 4 passed: small turn below threshold\n');
    
    fprintf('\nAll tests passed for detect_turn_events!\n');
end

