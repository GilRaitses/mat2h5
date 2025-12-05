% RUN_VALIDATION_SUITE - Run all validation tests and generate test vectors
%
% This script:
% 1. Runs unit tests for each function
% 2. Generates standardized test vectors
% 3. Saves test vectors to test_data/ for Python comparison
%
% Usage:
%   cd('scripts/2025-12-04/mat2h5/validation/matlab');
%   run_validation_suite;
%
% Output:
%   ../test_data/test_vectors.mat - MATLAB test vectors
%   ../test_data/test_vectors.json - JSON test vectors for Python

fprintf('===============================================\n');
fprintf('VALIDATION SUITE FOR ENGINEER_DATA PIPELINE\n');
fprintf('===============================================\n\n');

%% Run Unit Tests
fprintf('--- Running Unit Tests ---\n\n');

try
    fprintf('Testing compute_heading_unit_vector...\n');
    test_compute_heading_unit_vector();
catch ME
    fprintf('FAILED: %s\n', ME.message);
end

try
    fprintf('\nTesting compute_velocity_and_speed...\n');
    test_compute_velocity_and_speed();
catch ME
    fprintf('FAILED: %s\n', ME.message);
end

try
    fprintf('\nTesting compute_speedrunvel...\n');
    test_compute_speedrunvel();
catch ME
    fprintf('FAILED: %s\n', ME.message);
end

try
    fprintf('\nTesting detect_reversals...\n');
    test_detect_reversals();
catch ME
    fprintf('FAILED: %s\n', ME.message);
end

try
    fprintf('\nTesting detect_turn_events...\n');
    test_detect_turn_events();
catch ME
    fprintf('FAILED: %s\n', ME.message);
end

try
    fprintf('\nTesting rate_from_time_corrected...\n');
    test_rate_from_time_corrected();
catch ME
    fprintf('FAILED: %s\n', ME.message);
end

%% Generate Test Vectors for Cross-Language Comparison
fprintf('\n--- Generating Test Vectors ---\n\n');

test_vectors = struct();

% Test vector 1: Heading unit vector
fprintf('Generating test vector 1: heading_unit_vector...\n');
tv1.name = 'heading_unit_vector';
tv1.inputs.shead = [1, 2, 3, 4, 5; 1, 2, 3, 4, 5];
tv1.inputs.smid = [0, 1, 2, 3, 4; 0, 1, 2, 3, 4];
tv1.outputs.HeadUnitVec = compute_heading_unit_vector(tv1.inputs.shead, tv1.inputs.smid);
test_vectors.heading_unit_vector = tv1;

% Test vector 2: Velocity and speed
fprintf('Generating test vector 2: velocity_and_speed...\n');
tv2.name = 'velocity_and_speed';
tv2.inputs.xpos = [0, 1, 3, 6, 10];
tv2.inputs.ypos = [0, 1, 2, 3, 4];
tv2.inputs.times = [0, 1, 2, 3, 4];
[tv2.outputs.VelocityVec, tv2.outputs.speed] = compute_velocity_and_speed(...
    tv2.inputs.xpos, tv2.inputs.ypos, tv2.inputs.times);
test_vectors.velocity_and_speed = tv2;

% Test vector 3: SpeedRunVel (full pipeline test)
fprintf('Generating test vector 3: speedrunvel...\n');
tv3.name = 'speedrunvel';
tv3.inputs.shead = [2, 3, 4, 5, 6; 0, 0, 0, 0, 0];
tv3.inputs.smid = [1, 2, 3, 4, 5; 0, 0, 0, 0, 0];
tv3.inputs.xpos = [0, 1, 2, 3, 4];
tv3.inputs.ypos = [0, 0, 0, 0, 0];
tv3.inputs.times = [0, 1, 2, 3, 4];
tv3.inputs.lengthPerPixel = 1.0;
[tv3.outputs.SpeedRunVel, tv3.outputs.times_out] = compute_speedrunvel(...
    tv3.inputs.shead, tv3.inputs.smid, tv3.inputs.xpos, tv3.inputs.ypos, ...
    tv3.inputs.times, tv3.inputs.lengthPerPixel);
test_vectors.speedrunvel = tv3;

% Test vector 4: Reversal detection
fprintf('Generating test vector 4: reversals...\n');
tv4.name = 'reversals';
times = 0:0.1:20;
SpeedRunVel = ones(size(times));
SpeedRunVel(21:71) = -1;   % Reversal 1: t=2 to t=7 (5 seconds)
SpeedRunVel(121:161) = -1; % Reversal 2: t=12 to t=16 (4 seconds)
tv4.inputs.times = times;
tv4.inputs.SpeedRunVel = SpeedRunVel;
tv4.inputs.min_duration = 3.0;
reversals = detect_reversals(tv4.inputs.times, tv4.inputs.SpeedRunVel, tv4.inputs.min_duration);
tv4.outputs.num_reversals = length(reversals);
tv4.outputs.reversal_start_times = [reversals.start_time];
tv4.outputs.reversal_durations = [reversals.duration];
test_vectors.reversals = tv4;

% Test vector 5: Turn rate (corrected)
fprintf('Generating test vector 5: turn_rate...\n');
tv5.name = 'turn_rate';
tv5.inputs.event_times = [1.2, 2.5, 4.1, 5.8, 7.3, 8.9, 10.2, 11.5, 13.1, 14.2];
tv5.inputs.total_duration = 15;
tv5.inputs.bin_size = 1.0;
[tv5.outputs.rate, tv5.outputs.time_bins, tv5.outputs.counts] = ...
    rate_from_time_corrected(tv5.inputs.event_times, tv5.inputs.total_duration, tv5.inputs.bin_size);
test_vectors.turn_rate = tv5;

% Test vector 6: Realistic track data simulation
fprintf('Generating test vector 6: realistic_track...\n');
tv6.name = 'realistic_track';
N = 1000;  % 1000 frames at 20 fps = 50 seconds
dt = 0.05;  % 20 fps
times = (0:N-1) * dt;

% Simulate larva movement: forward, then reverse, then forward
% Phase 1 (0-15s): Forward crawling
% Phase 2 (15-25s): Reverse crawl
% Phase 3 (25-50s): Forward crawling with turns

% Generate head and midpoint positions
shead = zeros(2, N);
smid = zeros(2, N);
xpos = zeros(1, N);
ypos = zeros(1, N);

angle = 0;  % Initial heading
x = 0; y = 0;
for i = 1:N
    % Heading points in direction of angle
    shead(1, i) = x + cos(angle);
    shead(2, i) = y + sin(angle);
    smid(1, i) = x;
    smid(2, i) = y;
    
    % Position
    xpos(i) = x;
    ypos(i) = y;
    
    % Update position based on phase
    t = times(i);
    if t < 15
        % Forward crawling
        speed = 0.1;  % cm/frame
        x = x + speed * cos(angle);
        y = y + speed * sin(angle);
    elseif t < 25
        % Reverse crawling (move backward relative to head)
        speed = 0.05;
        x = x - speed * cos(angle);
        y = y - speed * sin(angle);
    else
        % Forward with occasional turns
        speed = 0.08;
        if mod(floor(t), 5) == 0 && mod(i, 100) < 20
            angle = angle + 0.1;  % Turn left
        end
        x = x + speed * cos(angle);
        y = y + speed * sin(angle);
    end
end

tv6.inputs.shead = shead;
tv6.inputs.smid = smid;
tv6.inputs.xpos = xpos;
tv6.inputs.ypos = ypos;
tv6.inputs.times = times;
tv6.inputs.lengthPerPixel = 1.0;

% Compute outputs
[tv6.outputs.SpeedRunVel, tv6.outputs.times_out] = compute_speedrunvel(...
    tv6.inputs.shead, tv6.inputs.smid, tv6.inputs.xpos, tv6.inputs.ypos, ...
    tv6.inputs.times, tv6.inputs.lengthPerPixel);
tv6.outputs.reversals = detect_reversals(tv6.outputs.times_out, tv6.outputs.SpeedRunVel, 3.0);
tv6.outputs.num_reversals = length(tv6.outputs.reversals);

test_vectors.realistic_track = tv6;

%% Save Test Vectors
fprintf('\n--- Saving Test Vectors ---\n\n');

% Create output directory
output_dir = '../test_data';
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

% Save as .mat file
mat_file = fullfile(output_dir, 'test_vectors.mat');
save(mat_file, 'test_vectors');
fprintf('Saved MATLAB test vectors to: %s\n', mat_file);

% Save as JSON (for Python)
json_file = fullfile(output_dir, 'test_vectors.json');
json_str = jsonencode(test_vectors);
fid = fopen(json_file, 'w');
fprintf(fid, '%s', json_str);
fclose(fid);
fprintf('Saved JSON test vectors to: %s\n', json_file);

%% Summary
fprintf('\n===============================================\n');
fprintf('VALIDATION SUITE COMPLETE\n');
fprintf('===============================================\n');
fprintf('\nTest vectors saved to:\n');
fprintf('  - %s (for MATLAB)\n', mat_file);
fprintf('  - %s (for Python)\n', json_file);
fprintf('\nNext step: Run compare_outputs.py to validate Python implementation.\n');

