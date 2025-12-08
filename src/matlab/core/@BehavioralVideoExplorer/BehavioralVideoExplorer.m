classdef BehavioralVideoExplorer < handle
    % BehavioralVideoExplorer - Main application class for behavioral video analysis
    %
    % This class coordinates all components of the behavioral video explorer
    % system, providing a clean interface for data loading, visualization,
    % and export operations.
    %
    % Properties:
    %   DataManager   - Handles data loading and preprocessing
    %   Renderer      - Handles visualization and rendering
    %   TrackManager  - Handles track selection and manipulation
    %   CacheManager  - Handles frame caching for performance
    %   ExportManager - Handles export operations
    %
    % Methods:
    %   loadExperiment          - Load experiment data
    %   renderFrame             - Render a specific frame
    %   buildCache              - Pre-render frames for scrubbing
    %   exportIntegrationMatrix - Export stimulus response matrix
    %   selectTracks            - Select specific tracks
    %   getInfo                 - Get application state information
    %
    % Example:
    %   % Create application
    %   app = BehavioralVideoExplorer();
    %   
    %   % Load experiment
    %   app.loadExperiment(mat_file, tracks_dir, bin_file);
    %   
    %   % Configure rendering
    %   app.setRenderParams('show_fid', true, 'show_trails', true);
    %   
    %   % Create visualization
    %   fig = figure();
    %   ax = axes(fig);
    %   app.renderFrame(ax, 1000);
    %   
    %   % Export integration matrix
    %   app.exportIntegrationMatrix(1, 'matrix_track1.png');
    %
    % See also: DataManager, Renderer, TrackManager, CacheManager, ExportManager
    %
    % 2025-10-16 - Refactored from monolithic BehavioralVideoExplorer.m
    
    properties
        DataManager   % Data loading and preprocessing
        Renderer      % Visualization and rendering
        TrackManager  % Track selection and manipulation
        CacheManager  % Frame caching for performance
        ExportManager % Export operations
    end
    
    methods
        function app = BehavioralVideoExplorer()
            % Constructor - Initialize all managers
            %
            % Example:
            %   app = BehavioralVideoExplorer();
            
            fprintf('=== Behavioral Video Explorer ===\n');
            fprintf('Initializing managers...\n');
            
            % Initialize all managers
            app.DataManager = DataManager();
            app.Renderer = Renderer();
            app.TrackManager = TrackManager();
            app.CacheManager = CacheManager();
            app.ExportManager = ExportManager();
            
            fprintf('[OK] All managers initialized\n');
        end
        
        function loadExperiment(app, mat_file, tracks_dir, bin_file)
            % loadExperiment - Load experiment data
            %
            % Inputs:
            %   mat_file   - Path to experiment MAT file
            %   tracks_dir - Path to tracks directory
            %   bin_file   - Path to binary FID file
            %
            % Example:
            %   app.loadExperiment(mat_file, tracks_dir, bin_file);
            
            app.DataManager.loadExperiment(mat_file, tracks_dir, bin_file);
            
            % Update track manager with number of tracks
            num_tracks = app.DataManager.num_tracks;
            app.TrackManager = TrackManager(num_tracks);
            
            fprintf('[OK] Experiment loaded successfully\n');
        end
        
        function setRenderParams(app, varargin)
            % setRenderParams - Set rendering parameters
            %
            % Inputs:
            %   varargin - Name-value pairs for rendering parameters
            %     'trail_length'  - Number of frames for trail (default: 600)
            %     'show_fid'      - Show FID layer (default: true)
            %     'show_trails'   - Show trail layer (default: true)
            %     'show_contour'  - Show contour layer (default: false)
            %     'show_dots'     - Show white dots (default: true)
            %     'show_numbers'  - Show track numbers (default: true)
            %
            % Example:
            %   app.setRenderParams('show_fid', true, 'trail_length', 600);
            
            % Parse name-value pairs
            for i = 1:2:length(varargin)
                param_name = varargin{i};
                param_value = varargin{i+1};
                app.Renderer.params.(param_name) = param_value;
            end
        end
        
        function renderFrame(app, ax, frame_idx)
            % renderFrame - Render a specific frame
            %
            % Inputs:
            %   ax        - Axes handle to render on
            %   frame_idx - Frame number to render
            %
            % Example:
            %   fig = figure();
            %   ax = axes(fig);
            %   app.renderFrame(ax, 1000);
            
            app.Renderer.renderFrame(ax, app.DataManager, frame_idx, ...
                app.TrackManager.selected_tracks);
        end
        
        function buildCache(app, progress_callback)
            % buildCache - Pre-render frames for instant scrubbing
            %
            % Input:
            %   progress_callback - Optional function handle for progress
            %
            % Example:
            %   app.buildCache(@(msg) fprintf('%s\n', msg));
            
            if nargin < 2
                progress_callback = [];
            end
            
            app.CacheManager.buildCache(app.Renderer, app.DataManager, ...
                app.TrackManager.selected_tracks, progress_callback);
        end
        
        function showCached(app, ax, frame_idx)
            % showCached - Display cached frame
            %
            % Inputs:
            %   ax        - Axes handle
            %   frame_idx - Frame number
            %
            % Example:
            %   app.showCached(ax, 1000);
            
            app.CacheManager.showCached(ax, frame_idx);
        end
        
        function exportIntegrationMatrix(app, track_idx, output_path)
            % exportIntegrationMatrix - Export stimulus response matrix
            %
            % Inputs:
            %   track_idx   - Track number to analyze
            %   output_path - Path to save PNG file (optional)
            %
            % Example:
            %   app.exportIntegrationMatrix(1, 'matrix_track1.png');
            
            if nargin < 3
                output_path = '';
            end
            
            app.ExportManager.exportIntegrationMatrix(app.Renderer, ...
                app.DataManager, track_idx, output_path);
        end
        
        function selectTracks(app, track_indices)
            % selectTracks - Select specific tracks by index
            %
            % Input:
            %   track_indices - Array of track indices to select
            %
            % Example:
            %   app.selectTracks([1, 3, 5]);
            
            app.TrackManager.selectTracks(track_indices);
        end
        
        function selectAll(app)
            % selectAll - Select all tracks
            app.TrackManager.selectAll();
        end
        
        function deselectAll(app)
            % deselectAll - Deselect all tracks
            app.TrackManager.deselectAll();
        end
        
        function info = getInfo(app)
            % getInfo - Get application state information
            %
            % Output:
            %   info - Struct with application state
            %
            % Example:
            %   info = app.getInfo();
            %   fprintf('Tracks: %d, Frames: %d\n', info.num_tracks, info.num_frames);
            
            info = struct();
            info.num_tracks = app.DataManager.num_tracks;
            info.num_frames = app.DataManager.num_frames;
            info.selected_count = app.TrackManager.getSelectedCount();
            info.cache_info = app.CacheManager.getCacheInfo();
            info.render_params = app.Renderer.params;
        end
    end
end

