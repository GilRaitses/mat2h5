% example_usage.m - Example usage of BehavioralVideoExplorer class
%
% This script demonstrates basic usage of the refactored class structure.
%
% 2025-10-16 - Created for class refactor

clear; close all; clc;

%% 1. Create Application
fprintf('Creating BehavioralVideoExplorer...\n');
app = BehavioralVideoExplorer();

%% 2. Load Experiment
fprintf('Loading experiment data...\n');

% Define paths
mat_file = 'D:\mechanosensation\Devindi''s Data\250\T_Re_Sq_0to250PWM_30#C_Bl_7PWM\matfiles\GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202509051201.mat';
tracks_dir = 'D:\mechanosensation\Devindi''s Data\250\T_Re_Sq_0to250PWM_30#C_Bl_7PWM\matfiles\GMR61@GMR61_202509051201 - tracks';
bin_file = 'D:\rawdata\GMR61@GMR61\T_Re_Sq_0to250PWM_30#C_Bl_7PWM\GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202509051201.bin';

app.loadExperiment(mat_file, tracks_dir, bin_file);

%% 3. Configure Rendering
fprintf('Configuring rendering parameters...\n');
app.setRenderParams('show_fid', true, ...
                    'show_trails', true, ...
                    'show_contour', false, ...
                    'trail_length', 600);

%% 4. Render a Frame
fprintf('Rendering frame...\n');
fig = figure('Name', 'Behavioral Video Explorer', ...
             'Position', [100 100 1000 800], ...
             'Color', 'k');
ax = axes('Parent', fig);

% Render frame 1000
app.renderFrame(ax, 1000);

%% 5. Select Specific Tracks
fprintf('Selecting specific tracks...\n');
app.selectTracks([6, 9, 11]);  % Tracks from Oct 2 reference

% Re-render with selected tracks
app.renderFrame(ax, 1000);

%% 6. Export Integration Matrix
fprintf('Exporting integration matrix...\n');
app.exportIntegrationMatrix(1, 'example_integration_matrix.png');

%% 7. Get Application Info
info = app.getInfo();
fprintf('\n=== Application Info ===\n');
fprintf('Tracks: %d\n', info.num_tracks);
fprintf('Frames: %d\n', info.num_frames);
fprintf('Selected: %d\n', info.selected_count);
fprintf('========================\n');

fprintf('\n[OK] Example complete!\n');

