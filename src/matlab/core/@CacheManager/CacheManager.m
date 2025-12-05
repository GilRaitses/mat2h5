classdef CacheManager < handle
    % CacheManager - Manages frame caching for instant scrubbing
    %
    % This class handles pre-rendering frames to enable instant video scrubbing.
    % It creates a cache of rendered images with transparent backgrounds.
    %
    % Properties:
    %   cache - Struct containing cached frames
    %     .frames       - Cell array of rendered images
    %     .xlim         - X-axis limits used
    %     .ylim         - Y-axis limits used
    %     .params       - Parameters used for rendering
    %     .num_frames   - Number of cached frames
    %     .sample_interval - Frame sampling interval
    %
    % Methods:
    %   buildCache     - Pre-render frames
    %   getCached      - Retrieve cached frame
    %   showCached     - Display cached frame on axes
    %   clearCache     - Clear cache to free memory
    %
    % Example:
    %   cm = CacheManager();
    %   cm.buildCache(renderer, data, selected_tracks);
    %   cm.showCached(ax, 1000);
    %
    % See also: BehavioralVideoExplorer, Renderer
    %
    % 2025-10-16 - Refactored from FrameCache.m
    
    properties
        cache  % Cache struct
    end
    
    methods
        function obj = CacheManager()
            % Constructor - initialize empty cache
            obj.cache = struct();
            obj.cache.frames = {};
            obj.cache.num_frames = 0;
        end
        
        % External method signatures (implemented in separate files)
        buildCache(obj, renderer, data, selected_tracks, progress_callback)
        frame_img = getCached(obj, frame_idx)
        showCached(obj, ax, frame_idx)
        
        function clearCache(obj)
            % clearCache - Clear cache to free memory
            obj.cache.frames = {};
            obj.cache.num_frames = 0;
        end
        
        function is_cached = isCached(obj, frame_idx)
            % isCached - Check if a frame is cached
            %
            % Input:
            %   frame_idx - Frame index to check
            %
            % Output:
            %   is_cached - True if frame is cached
            
            if isempty(obj.cache.frames) || frame_idx < 1
                is_cached = false;
                return;
            end
            
            if frame_idx > length(obj.cache.frames)
                is_cached = false;
                return;
            end
            
            is_cached = ~isempty(obj.cache.frames{frame_idx});
        end
        
        function info = getCacheInfo(obj)
            % getCacheInfo - Get information about cache status
            %
            % Output:
            %   info - Struct with cache information
            
            info = struct();
            info.total_frames = obj.cache.num_frames;
            info.cached_count = 0;
            
            if ~isempty(obj.cache.frames)
                for i = 1:length(obj.cache.frames)
                    if ~isempty(obj.cache.frames{i})
                        info.cached_count = info.cached_count + 1;
                    end
                end
            end
            
            info.cache_percentage = (info.cached_count / info.total_frames) * 100;
            
            if isfield(obj.cache, 'sample_interval')
                info.sample_interval = obj.cache.sample_interval;
            else
                info.sample_interval = 1;
            end
            
            if isfield(obj.cache, 'render_time')
                info.render_time = obj.cache.render_time;
            else
                info.render_time = 0;
            end
        end
    end
end

