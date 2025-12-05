function frame_img = getCached(obj, frame_idx)
    % getCached - Retrieve cached frame image
    %
    % If the exact frame is not cached, returns the nearest cached frame.
    %
    % Input:
    %   frame_idx - Frame index to retrieve
    %
    % Output:
    %   frame_img - Cached frame image struct or []
    %
    % See also: CacheManager, buildCache, showCached
    
    if isempty(obj.cache.frames)
        frame_img = [];
        return;
    end
    
    if frame_idx < 1 || frame_idx > length(obj.cache.frames)
        frame_img = [];
        return;
    end
    
    % Check if exact frame is cached
    if ~isempty(obj.cache.frames{frame_idx})
        frame_img = obj.cache.frames{frame_idx};
        return;
    end
    
    % Find nearest cached frame
    sample_interval = obj.cache.sample_interval;
    nearest_idx = round(frame_idx / sample_interval) * sample_interval;
    
    if nearest_idx < 1
        nearest_idx = sample_interval;
    end
    
    if nearest_idx > length(obj.cache.frames)
        nearest_idx = length(obj.cache.frames);
    end
    
    if ~isempty(obj.cache.frames{nearest_idx})
        frame_img = obj.cache.frames{nearest_idx};
    else
        frame_img = [];
    end
end

