classdef Renderer < handle
    % Renderer - Handles all visualization and rendering for behavioral video
    %
    % This class encapsulates all rendering logic, including FID images,
    % trails, contours, and overlays. It uses the validated methods from
    % the October 2 multiTrackReverseCrawl.m script.
    %
    % Properties:
    %   params - Rendering parameters struct
    %
    % Methods:
    %   renderFrame   - Render complete frame with all layers
    %   renderFID     - Render FID images for tracks
    %   renderTrail   - Render track trails
    %   renderContour - Render track contours (Oct 2 method)
    %   renderDots    - Render white dots at current positions
    %   renderNumbers - Render track numbers with transparency
    %
    % Example:
    %   renderer = Renderer();
    %   renderer.renderFrame(ax, data, frame_idx, selected_tracks);
    %
    % See also: BehavioralVideoExplorer, DataManager, CacheManager
    %
    % 2025-10-16 - Refactored from FrameRenderer.m
    
    properties
        params  % Rendering parameters
    end
    
    methods
        function obj = Renderer(params)
            % Constructor - initialize renderer with parameters
            %
            % Input:
            %   params - Optional parameter struct with fields:
            %     .trail_length   - Number of frames for trail (default: 600)
            %     .xlim           - X-axis limits (default: [5.7 19.0])
            %     .ylim           - Y-axis limits (default: [6.2 18.8])
            %     .show_fid       - Show FID layer (default: true)
            %     .show_trails    - Show trail layer (default: true)
            %     .show_contour   - Show contour layer (default: false)
            %     .show_dots      - Show white dots (default: true)
            %     .show_numbers   - Show track numbers (default: true)
            
            if nargin < 1
                params = struct();
            end
            
            % Set default parameters
            if ~isfield(params, 'trail_length'), params.trail_length = 600; end
            if ~isfield(params, 'xlim'), params.xlim = [5.7, 19.0]; end
            if ~isfield(params, 'ylim'), params.ylim = [6.2, 18.8]; end
            if ~isfield(params, 'show_fid'), params.show_fid = true; end
            if ~isfield(params, 'show_trails'), params.show_trails = true; end
            if ~isfield(params, 'show_contour'), params.show_contour = false; end
            if ~isfield(params, 'show_dots'), params.show_dots = true; end
            if ~isfield(params, 'show_numbers'), params.show_numbers = true; end
            
            obj.params = params;
        end
        
        % External method signatures (implemented in separate files)
        renderFrame(obj, ax, data, frame_idx, selected_tracks)
        renderFID(obj, ax, data, frame_idx, selected_tracks)
        renderTrail(obj, ax, data, frame_idx, selected_tracks)
        renderContour(obj, ax, data, frame_idx, selected_tracks)
        renderDots(obj, ax, data, frame_idx, selected_tracks)
        renderNumbers(obj, ax, data, frame_idx, selected_tracks)
    end
    
    methods (Access = private)
        function configureAxes(obj, ax, frame_idx, num_frames)
            % Configure axes appearance and limits
            set(ax, 'Color', 'k');
            axis(ax, 'equal');
            xlim(ax, obj.params.xlim);
            ylim(ax, obj.params.ylim);
            set(ax, 'XColor', 'w', 'YColor', 'w');
            xlabel(ax, 'X Position (cm)', 'Color', 'w');
            ylabel(ax, 'Y Position (cm)', 'Color', 'w');
            title(ax, sprintf('Frame %d / %d', frame_idx, num_frames), ...
                'Color', 'w', 'FontSize', 14);
        end
    end
end

