% LOAD_EXPERIMENT_AND_COMPUTE - Load experiment and compute validation outputs
%
% ORIGINAL MASON SCRIPTS REFERENCED:
%   - Just_ReverseCrawl_Matlab.m (SpeedRunVel computation)
%   - Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m (reversal detection)
%   Location: scripts/2025-11-20/mason's scritps/
%   Documentation: scripts/2025-11-24/mason_scripts_documentation.qmd
%
% This script loads actual experiment data and computes:
%   - SpeedRunVel for each track (using Mason's dot product method)
%   - Reversal detection (SpeedRunVel < 0 for >= 3 seconds)
%   - LED-derived ton/toff stimulus windows
%
% The outputs are saved for comparison with the Python pipeline.
%
% Experiment: GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_202506251614

clear; close all;

%% Configuration
eset_dir = 'D:\rawdata\GMR61@GMR61\T_Re_Sq_50to250PWM_30#C_Bl_7PWM';
experiment_timestamp = '202506251614';
experiment_name = ['GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_' experiment_timestamp];

% Output directory
output_dir = fullfile(fileparts(mfilename('fullpath')), '..', 'test_data');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

fprintf('=== MATLAB Validation: Load Experiment ===\n\n');
fprintf('ESET Directory: %s\n', eset_dir);
fprintf('Experiment: %s\n\n', experiment_name);

%% Load Experiment
matfiles_dir = fullfile(eset_dir, 'matfiles');
experiment_mat = fullfile(matfiles_dir, [experiment_name '.mat']);

fprintf('Loading experiment from: %s\n', experiment_mat);
load(experiment_mat);

% Handle different variable names
if exist('experiment', 'var')
    eset = ExperimentSet();
    eset.expt = experiment;
    clear experiment;
elseif ~exist('eset', 'var')
    error('No experiment or eset found in mat file');
end

%% Load Tracks
tracks_dir = fullfile(matfiles_dir, ['GMR61@GMR61_' experiment_timestamp ' - tracks']);
fprintf('Loading tracks from: %s\n', tracks_dir);

track_files = dir(fullfile(tracks_dir, 'track*.mat'));
tracks = [];
for t = 1:length(track_files)
    load(fullfile(tracks_dir, track_files(t).name));
    if exist('track', 'var')
        tracks = [tracks, track];
        clear track;
    end
end
eset.expt(1).track = tracks;
fprintf('Loaded %d tracks\n\n', length(tracks));

%% Get Camera Calibration (lengthPerPixel)
if isprop(eset.expt(1), 'camcalinfo') && ~isempty(eset.expt(1).camcalinfo)
    cc = eset.expt(1).camcalinfo;
    test_pixels_x = [100, 500];
    test_pixels_y = [100, 500];
    real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
    real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
    pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
    real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
    lengthPerPixel = real_dist / pixel_dist;
    fprintf('lengthPerPixel: %.6f cm/pixel\n\n', lengthPerPixel);
else
    error('No camera calibration found');
end

%% Get LED Values (for stimulus timing)
fprintf('--- Loading LED Values ---\n');

% Get globalQuantity LED values
if ~isempty(eset.expt(1).globalQuantity)
    field_names = {eset.expt(1).globalQuantity.fieldname};
    
    led1_idx = strcmp(field_names, 'led1Val');
    led2_idx = strcmp(field_names, 'led2Val');
    
    if any(led1_idx)
        GQled1Val = eset.expt(1).globalQuantity(led1_idx);
        led1_xdata = GQled1Val.xData;
        led1_ydata = GQled1Val.yData;
        fprintf('LED1 data: %d points, range [%.1f, %.1f]\n', length(led1_ydata), min(led1_ydata), max(led1_ydata));
    end
    
    if any(led2_idx)
        GQled2Val = eset.expt(1).globalQuantity(led2_idx);
        led2_xdata = GQled2Val.xData;
        led2_ydata = GQled2Val.yData;
        fprintf('LED2 data: %d points, range [%.1f, %.1f]\n', length(led2_ydata), min(led2_ydata), max(led2_ydata));
    end
else
    warning('No globalQuantity found');
end

%% Create ton/toff from LED values
% Stimulus period and timing
tperiod = 15;  % seconds
fprintf('\nStimulus period: %d seconds\n', tperiod);

% Create combined LED signal for ton/toff detection
led_combined = led1_ydata + led2_ydata;

%% Select a specific track for validation by TRACK NUMBER (not array index)
% CRITICAL: Use track.trackNum for identity, NOT array position
% See FIELD_MAPPING.md for explanation

target_track_num = 1;  % The track NUMBER we want
validation_track_idx = [];

% Find track by number
for i = 1:length(eset.expt(1).track)
    if eset.expt(1).track(i).trackNum == target_track_num
        validation_track_idx = i;
        break;
    end
end

if isempty(validation_track_idx)
    % Fallback: use first track but warn
    warning('Track number %d not found. Using first track instead.', target_track_num);
    validation_track_idx = 1;
    target_track_num = eset.expt(1).track(1).trackNum;
end

t = eset.expt(1).track(validation_track_idx);
actual_track_num = t.trackNum;

fprintf('\n--- Computing SpeedRunVel for Track Number %d (array index %d) ---\n', actual_track_num, validation_track_idx);
fprintf('Track has %d points\n', t.npts);
fprintf('Start frame: %d, End frame: %d\n', t.startFrame, t.endFrame);

%% Compute SpeedRunVel using the exact same method as engineer_data.py

% Get time
times = t.dq.eti;
fprintf('Time range: %.2f to %.2f seconds\n', times(1), times(end));

% Get positions (in pixels)
pos = t.getDerivedQuantity('sloc');
xpos_pixels = pos(1,:);
ypos_pixels = pos(2,:);

% Convert to cm
xpos = xpos_pixels * lengthPerPixel;
ypos = ypos_pixels * lengthPerPixel;

% Get head and midpoint positions
shead = t.dq.shead;  % 2 x N
smid = t.dq.smid;    % 2 x N

%% Step 1: Compute HeadUnitVec
HeadVec = shead - smid;
norms = sqrt(HeadVec(1,:).^2 + HeadVec(2,:).^2);
norms(norms == 0) = 1.0;  % Avoid division by zero
HeadUnitVec = HeadVec ./ norms;

%% Step 2: Compute VelocityVec and SpeedRun
N = length(times);
dx = diff(xpos);
dy = diff(ypos);
dt = diff(times);

distance = sqrt(dx.^2 + dy.^2);

% SpeedRun
SpeedRun = zeros(1, N-1);
valid_dt = dt > 0;
SpeedRun(valid_dt) = distance(valid_dt) ./ dt(valid_dt);

% VelocityVec (normalized)
VelocityVec = zeros(2, N-1);
valid_dist = distance > 0;
VelocityVec(1, valid_dist) = dx(valid_dist) ./ distance(valid_dist);
VelocityVec(2, valid_dist) = dy(valid_dist) ./ distance(valid_dist);

%% Step 3: Compute CosThetaFactor (dot product)
CosThetaFactor = sum(VelocityVec .* HeadUnitVec(:, 1:N-1), 1);

%% Step 4: Compute SpeedRunVel
SpeedRunVel = SpeedRun .* CosThetaFactor;

fprintf('SpeedRunVel computed: %d values\n', length(SpeedRunVel));
fprintf('SpeedRunVel range: [%.4f, %.4f]\n', min(SpeedRunVel), max(SpeedRunVel));
fprintf('Negative SpeedRunVel points: %d (%.1f%%)\n', sum(SpeedRunVel < 0), 100*sum(SpeedRunVel < 0)/length(SpeedRunVel));

%% Step 5: Detect Reversals (SpeedRunVel < 0 for >= 3 seconds)
min_duration = 3.0;
times_srv = times(1:end-1);  % Times for SpeedRunVel

reversal_mask = SpeedRunVel < 0;
reversals = struct('start_idx', {}, 'end_idx', {}, 'start_time', {}, 'end_time', {}, 'duration', {});

in_reversal = false;
start_idx = [];
start_time = [];

for i = 1:length(reversal_mask)
    if reversal_mask(i) && ~in_reversal
        in_reversal = true;
        start_idx = i;
        start_time = times_srv(i);
    elseif ~reversal_mask(i) && in_reversal
        in_reversal = false;
        if ~isempty(start_idx)
            duration = times_srv(i) - start_time;
            if duration >= min_duration
                reversals(end+1).start_idx = start_idx;
                reversals(end).end_idx = i - 1;
                reversals(end).start_time = start_time;
                reversals(end).end_time = times_srv(i-1);
                reversals(end).duration = duration;
            end
        end
        start_idx = [];
    end
end

% Handle reversal at end
if in_reversal && ~isempty(start_idx)
    duration = times_srv(end) - start_time;
    if duration >= min_duration
        reversals(end+1).start_idx = start_idx;
        reversals(end).end_idx = length(SpeedRunVel);
        reversals(end).start_time = start_time;
        reversals(end).end_time = times_srv(end);
        reversals(end).duration = duration;
    end
end

fprintf('\nReversals detected: %d\n', length(reversals));
for r = 1:length(reversals)
    fprintf('  Reversal %d: t=%.2f to %.2f (%.2f s)\n', r, ...
        reversals(r).start_time, reversals(r).end_time, reversals(r).duration);
end

%% Save validation outputs
fprintf('\n--- Saving Validation Data ---\n');

validation_data = struct();
validation_data.experiment_name = experiment_name;
validation_data.track_num = actual_track_num;  % Use track NUMBER not index
validation_data.track_array_idx = validation_track_idx;  % For debugging only
validation_data.lengthPerPixel = lengthPerPixel;

% Input data
validation_data.inputs.times = times;
validation_data.inputs.xpos_pixels = xpos_pixels;
validation_data.inputs.ypos_pixels = ypos_pixels;
validation_data.inputs.shead = shead;
validation_data.inputs.smid = smid;

% LED data
validation_data.led.led1_xdata = led1_xdata;
validation_data.led.led1_ydata = led1_ydata;
validation_data.led.led2_xdata = led2_xdata;
validation_data.led.led2_ydata = led2_ydata;
validation_data.led.tperiod = tperiod;

% Intermediate computations
validation_data.intermediate.HeadUnitVec = HeadUnitVec;
validation_data.intermediate.VelocityVec = VelocityVec;
validation_data.intermediate.SpeedRun = SpeedRun;
validation_data.intermediate.CosThetaFactor = CosThetaFactor;

% Final outputs
validation_data.outputs.SpeedRunVel = SpeedRunVel;
validation_data.outputs.times_srv = times_srv;
validation_data.outputs.num_reversals = length(reversals);
if ~isempty(reversals)
    validation_data.outputs.reversal_start_times = [reversals.start_time];
    validation_data.outputs.reversal_end_times = [reversals.end_time];
    validation_data.outputs.reversal_durations = [reversals.duration];
else
    validation_data.outputs.reversal_start_times = [];
    validation_data.outputs.reversal_end_times = [];
    validation_data.outputs.reversal_durations = [];
end

% Save as .mat
mat_output = fullfile(output_dir, 'matlab_validation_output.mat');
save(mat_output, 'validation_data');
fprintf('Saved MATLAB output to: %s\n', mat_output);

% Also save key arrays as simple format for Python comparison
simple_output = fullfile(output_dir, 'matlab_speedrunvel.csv');
writematrix([times_srv', SpeedRunVel'], simple_output);
fprintf('Saved SpeedRunVel CSV to: %s\n', simple_output);

fprintf('\n=== MATLAB Validation Complete ===\n');
fprintf('Track %d from %s\n', validation_track_idx, experiment_name);
fprintf('SpeedRunVel: %d values\n', length(SpeedRunVel));
fprintf('Reversals: %d detected\n', length(reversals));

