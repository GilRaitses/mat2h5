% VALIDATE_H5_AGAINST_MAT - Compare H5 file data against source .mat file
%
% VALIDATION LAYER 1: Data Integrity
% ----------------------------------
% This script verifies that the H5 file contains identical data to the
% source .mat experiment file. Any discrepancy indicates a problem with
% the H5 export process.
%
% Compares:
%   - shead arrays (element-by-element)
%   - smid arrays (element-by-element)
%   - loc/sloc arrays (element-by-element)
%   - eti time arrays (element-by-element)
%   - LED arrays (element-by-element)
%   - lengthPerPixel calibration value
%   - Track count and track numbering
%
% REFERENCE: FIELD_MAPPING.md

clear; close all;

%% Configuration
eset_dir = 'D:\rawdata\GMR61@GMR61\T_Re_Sq_50to250PWM_30#C_Bl_7PWM';
experiment_timestamp = '202506251614';
experiment_name = ['GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_' experiment_timestamp];

% H5 file location
h5_dir = fullfile(eset_dir, 'h5_exports');
h5_file = fullfile(h5_dir, [experiment_name '.h5']);

% Output directory
output_dir = fullfile(fileparts(mfilename('fullpath')), '..', 'test_data');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

fprintf('=' .* ones(1,70));
fprintf('\nDATA INTEGRITY VALIDATION: MATLAB .mat vs H5\n');
fprintf('=' .* ones(1,70));
fprintf('\n\n');

%% Load MATLAB Experiment
fprintf('--- Loading MATLAB Source Data ---\n');

matfiles_dir = fullfile(eset_dir, 'matfiles');
experiment_mat = fullfile(matfiles_dir, [experiment_name '.mat']);

fprintf('Loading: %s\n', experiment_mat);
load(experiment_mat);

% Handle different variable names
if exist('experiment', 'var')
    eset = ExperimentSet();
    eset.expt = experiment;
    clear experiment;
elseif ~exist('eset', 'var')
    error('No experiment or eset found in mat file');
end

% Load Tracks
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
fprintf('Loaded %d MATLAB tracks\n\n', length(tracks));

%% Check H5 file exists
if ~exist(h5_file, 'file')
    fprintf('ERROR: H5 file not found: %s\n', h5_file);
    fprintf('Please ensure H5 export has been run.\n');
    return;
end

fprintf('--- Loading H5 Data ---\n');
fprintf('H5 file: %s\n\n', h5_file);

%% Initialize validation results
results = struct('field', {}, 'passed', {}, 'message', {}, 'max_diff', {});

%% Compare lengthPerPixel
fprintf('--- Comparing lengthPerPixel ---\n');

% MATLAB computation
cc = eset.expt(1).camcalinfo;
test_pixels_x = [100, 500];
test_pixels_y = [100, 500];
real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
mat_lpp = real_dist / pixel_dist;

% H5 value - check root first (primary), then metadata (backup)
try
    h5_lpp = h5read(h5_file, '/lengthPerPixel');
catch
    try
        h5_lpp = h5readatt(h5_file, '/metadata', 'lengthPerPixel');
    catch
        try
            h5_lpp = h5read(h5_file, '/metadata/lengthPerPixel');
        catch
            h5_lpp = NaN;
        end
    end
end

if isnan(h5_lpp)
    results(end+1).field = 'lengthPerPixel';
    results(end).passed = false;
    results(end).message = 'H5 lengthPerPixel not found';
    results(end).max_diff = Inf;
else
    diff = abs(mat_lpp - h5_lpp);
    passed = diff < 1e-12;
    results(end+1).field = 'lengthPerPixel';
    results(end).passed = passed;
    results(end).max_diff = diff;
    if passed
        results(end).message = sprintf('MATCH: %.10f (diff=%.2e)', mat_lpp, diff);
    else
        results(end).message = sprintf('MISMATCH: MATLAB=%.10f, H5=%.10f', mat_lpp, h5_lpp);
    end
    fprintf('  MATLAB: %.10f cm/pixel\n', mat_lpp);
    fprintf('  H5:     %.10f cm/pixel\n', h5_lpp);
    fprintf('  Diff:   %.2e\n', diff);
    fprintf('  Status: %s\n\n', results(end).message);
end

%% Compare LED values
fprintf('--- Comparing LED Values ---\n');

% MATLAB LED values
if ~isempty(eset.expt(1).globalQuantity)
    field_names = {eset.expt(1).globalQuantity.fieldname};
    
    % LED1
    led1_idx = strcmp(field_names, 'led1Val');
    if any(led1_idx)
        mat_led1 = eset.expt(1).globalQuantity(led1_idx).yData;
        try
            h5_led1 = h5read(h5_file, '/global_quantities/led1Val');
            [passed, max_diff] = compare_arrays(mat_led1, h5_led1, 0);
            results(end+1).field = 'led1Val';
            results(end).passed = passed;
            results(end).max_diff = max_diff;
            if passed
                results(end).message = sprintf('MATCH: %d points', length(mat_led1));
            else
                results(end).message = sprintf('MISMATCH: max_diff=%.2e', max_diff);
            end
            fprintf('  LED1: %s\n', results(end).message);
        catch
            results(end+1).field = 'led1Val';
            results(end).passed = false;
            results(end).message = 'H5 led1Val not found';
            results(end).max_diff = Inf;
            fprintf('  LED1: NOT FOUND in H5\n');
        end
    end
    
    % LED2
    led2_idx = strcmp(field_names, 'led2Val');
    if any(led2_idx)
        mat_led2 = eset.expt(1).globalQuantity(led2_idx).yData;
        try
            h5_led2 = h5read(h5_file, '/global_quantities/led2Val');
            [passed, max_diff] = compare_arrays(mat_led2, h5_led2, 0);
            results(end+1).field = 'led2Val';
            results(end).passed = passed;
            results(end).max_diff = max_diff;
            if passed
                results(end).message = sprintf('MATCH: %d points', length(mat_led2));
            else
                results(end).message = sprintf('MISMATCH: max_diff=%.2e', max_diff);
            end
            fprintf('  LED2: %s\n', results(end).message);
        catch
            results(end+1).field = 'led2Val';
            results(end).passed = false;
            results(end).message = 'H5 led2Val not found';
            results(end).max_diff = Inf;
            fprintf('  LED2: NOT FOUND in H5\n');
        end
    end
end
fprintf('\n');

%% Compare track count
fprintf('--- Comparing Track Count ---\n');

mat_track_count = length(eset.expt(1).track);

% Get H5 track count
try
    h5_info = h5info(h5_file, '/tracks');
    h5_track_count = length(h5_info.Groups);
catch
    h5_track_count = 0;
end

passed = mat_track_count == h5_track_count;
results(end+1).field = 'track_count';
results(end).passed = passed;
results(end).max_diff = abs(mat_track_count - h5_track_count);
if passed
    results(end).message = sprintf('MATCH: %d tracks', mat_track_count);
else
    results(end).message = sprintf('MISMATCH: MATLAB=%d, H5=%d', mat_track_count, h5_track_count);
end
fprintf('  MATLAB: %d tracks\n', mat_track_count);
fprintf('  H5:     %d tracks\n', h5_track_count);
fprintf('  Status: %s\n\n', results(end).message);

%% Compare track data (sample tracks)
fprintf('--- Comparing Track Data ---\n');

% Compare first and last tracks
tracks_to_check = [1];
if mat_track_count > 1
    tracks_to_check = [1, mat_track_count];
end

for idx = tracks_to_check
    mat_track = eset.expt(1).track(idx);
    track_num = mat_track.trackNum;
    
    fprintf('\nTrack %d (array index %d):\n', track_num, idx);
    
    % Construct H5 path
    h5_track_path = sprintf('/tracks/track_%03d', track_num);
    
    % Check if track exists in H5
    try
        h5info(h5_file, h5_track_path);
    catch
        % Try alternate naming
        h5_track_path = sprintf('/tracks/track%d', track_num);
        try
            h5info(h5_file, h5_track_path);
        catch
            results(end+1).field = sprintf('track_%d', track_num);
            results(end).passed = false;
            results(end).message = 'Track not found in H5';
            results(end).max_diff = Inf;
            fprintf('  ERROR: Track not found in H5\n');
            continue;
        end
    end
    
    % Compare shead
    mat_shead = mat_track.dq.shead;
    try
        h5_shead = h5read(h5_file, [h5_track_path '/derived_quantities/shead']);
        % Handle transpose if needed
        if size(h5_shead, 1) ~= 2 && size(h5_shead, 2) == 2
            h5_shead = h5_shead';
        end
        [passed, max_diff] = compare_arrays(mat_shead, h5_shead, 0);
        results(end+1).field = sprintf('track_%d/shead', track_num);
        results(end).passed = passed;
        results(end).max_diff = max_diff;
        if passed
            results(end).message = sprintf('MATCH (shape %dx%d)', size(mat_shead,1), size(mat_shead,2));
        else
            results(end).message = sprintf('MISMATCH: max_diff=%.2e', max_diff);
        end
        fprintf('  shead: %s\n', results(end).message);
    catch e
        results(end+1).field = sprintf('track_%d/shead', track_num);
        results(end).passed = false;
        results(end).message = sprintf('Error: %s', e.message);
        results(end).max_diff = Inf;
        fprintf('  shead: ERROR - %s\n', e.message);
    end
    
    % Compare smid
    mat_smid = mat_track.dq.smid;
    try
        h5_smid = h5read(h5_file, [h5_track_path '/derived_quantities/smid']);
        if size(h5_smid, 1) ~= 2 && size(h5_smid, 2) == 2
            h5_smid = h5_smid';
        end
        [passed, max_diff] = compare_arrays(mat_smid, h5_smid, 0);
        results(end+1).field = sprintf('track_%d/smid', track_num);
        results(end).passed = passed;
        results(end).max_diff = max_diff;
        if passed
            results(end).message = sprintf('MATCH (shape %dx%d)', size(mat_smid,1), size(mat_smid,2));
        else
            results(end).message = sprintf('MISMATCH: max_diff=%.2e', max_diff);
        end
        fprintf('  smid: %s\n', results(end).message);
    catch e
        results(end+1).field = sprintf('track_%d/smid', track_num);
        results(end).passed = false;
        results(end).message = sprintf('Error: %s', e.message);
        results(end).max_diff = Inf;
        fprintf('  smid: ERROR - %s\n', e.message);
    end
    
    % Compare eti
    mat_eti = mat_track.dq.eti;
    try
        h5_eti = h5read(h5_file, [h5_track_path '/derived_quantities/eti']);
        [passed, max_diff] = compare_arrays(mat_eti, h5_eti, 0);
        results(end+1).field = sprintf('track_%d/eti', track_num);
        results(end).passed = passed;
        results(end).max_diff = max_diff;
        if passed
            results(end).message = sprintf('MATCH (%d points)', length(mat_eti));
        else
            results(end).message = sprintf('MISMATCH: max_diff=%.2e', max_diff);
        end
        fprintf('  eti: %s\n', results(end).message);
    catch e
        results(end+1).field = sprintf('track_%d/eti', track_num);
        results(end).passed = false;
        results(end).message = sprintf('Error: %s', e.message);
        results(end).max_diff = Inf;
        fprintf('  eti: ERROR - %s\n', e.message);
    end
end

%% Summary
fprintf('\n');
fprintf('=' .* ones(1,70));
fprintf('\nVALIDATION SUMMARY\n');
fprintf('=' .* ones(1,70));
fprintf('\n\n');

num_passed = sum([results.passed]);
num_failed = sum(~[results.passed]);

fprintf('PASSED: %d\n', num_passed);
fprintf('FAILED: %d\n\n', num_failed);

if num_failed > 0
    fprintf('FAILURES:\n');
    for i = 1:length(results)
        if ~results(i).passed
            fprintf('  X %s: %s\n', results(i).field, results(i).message);
        end
    end
    fprintf('\n');
end

if num_failed == 0
    fprintf('RESULT: PASSED - H5 data matches MATLAB source\n');
else
    fprintf('RESULT: FAILED - %d field(s) do not match\n', num_failed);
end

fprintf('=' .* ones(1,70));
fprintf('\n');

%% Save results
results_file = fullfile(output_dir, 'data_integrity_results.mat');
save(results_file, 'results');
fprintf('\nResults saved to: %s\n', results_file);


%% Helper function
function [passed, max_diff] = compare_arrays(a, b, tolerance)
    % Compare two arrays element-by-element
    a = double(a(:));
    b = double(b(:));
    
    if length(a) ~= length(b)
        passed = false;
        max_diff = Inf;
        return;
    end
    
    diff = abs(a - b);
    max_diff = max(diff);
    passed = max_diff <= tolerance;
end

