function buildCache(obj, renderer, data, selected_tracks, progress_callback)
    % buildCache - Pre-render frames as image stack for instant scrubbing
    %
    % This creates a cache of rendered frame images in memory, allowing
    % instant scrubbing without re-rendering. Uses adaptive sampling
    % (every 10th frame by default) to balance speed and quality.
    %
    % Inputs:
    %   renderer          - Renderer object
    %   data              - Data struct from DataManager
    %   selected_tracks   - Logical array of which tracks to render
    %   progress_callback - Optional function handle for progress updates
    %
    % The cache uses TRANSPARENT backgrounds to enable layering.
    %
    % Example:
    %   cm = CacheManager();
    %   cm.buildCache(renderer, data, selected_tracks, @(msg) fprintf('%s\n', msg));
    %
    % See also: CacheManager, getCached, showCached
    
    if nargin < 5
        progress_callback = [];
    end
    
    fprintf('=== CACHE MANAGER: Pre-rendering frames ===\n');
    fprintf('Total frames: %d\n', data.num_frames);
    
    % Create invisible figure for rendering with TRANSPARENT background
    temp_fig = figure('Visible', 'off', 'Position', [0 0 800 600], 'Color', 'none');
    temp_ax = axes('Parent', temp_fig, 'Position', [0.1 0.1 0.8 0.8], ...
                   'Color', 'none', 'XColor', 'w', 'YColor', 'w');
    hold(temp_ax, 'on');
    axis(temp_ax, 'equal');
    set(temp_ax, 'YDir', 'normal');
    
    % Pre-allocate cache
    obj.cache = struct();
    obj.cache.frames = cell(1, data.num_frames);
    obj.cache.xlim = renderer.params.xlim;
    obj.cache.ylim = renderer.params.ylim;
    obj.cache.params = renderer.params;
    obj.cache.num_frames = data.num_frames;
    
    % Adaptive sampling: Render every Nth frame
    sample_interval = 10;
    obj.cache.sample_interval = sample_interval;
    
    tic;
    rendered_count = 0;
    
    for frame_idx = 1:sample_interval:data.num_frames
        try
            % Render frame to temp axes
            cla(temp_ax);
            renderer.renderFrame(temp_ax, data, frame_idx, selected_tracks);
            drawnow;
            
            % Capture frame as image
            frame_img = getframe(temp_ax);
            obj.cache.frames{frame_idx} = frame_img;
            
            rendered_count = rendered_count + 1;
        catch err
            fprintf('Warning: Frame %d failed: %s\n', frame_idx, err.message);
            obj.cache.frames{frame_idx} = [];
        end
        
        % Progress update every 100 frames
        if mod(rendered_count, 100) == 0
            elapsed = toc;
            fps = rendered_count / elapsed;
            eta = (data.num_frames / sample_interval - rendered_count) / fps;
            
            msg = sprintf('Caching frames: %d/%d (%.1f fps, ETA: %.0fs)', ...
                rendered_count, ceil(data.num_frames/sample_interval), fps, eta);
            
            if ~isempty(progress_callback)
                progress_callback(msg);
            end
            fprintf('%s\n', msg);
        end
    end
    
    % Close temp figure
    close(temp_fig);
    
    elapsed_total = toc;
    obj.cache.render_time = elapsed_total;
    
    fprintf('[OK] Frame cache complete: %d frames in %.1f seconds (%.1f fps)\n', ...
        rendered_count, elapsed_total, rendered_count/elapsed_total);
end

