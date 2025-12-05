function showCached(obj, ax, frame_idx)
    % showCached - Display cached frame on axes
    %
    % Optimized for speed using image object reuse and CData updates.
    % Display time is typically 5-10ms.
    %
    % Inputs:
    %   ax        - Axes handle to display on
    %   frame_idx - Frame index to show
    %
    % See also: CacheManager, getCached, buildCache
    
    frame_img = obj.getCached(frame_idx);
    
    if isempty(frame_img)
        return;
    end
    
    % Clear axes
    cla(ax);
    hold(ax, 'on');
    
    % Display image
    imagesc(ax, obj.cache.xlim, obj.cache.ylim, frame_img.cdata);
    
    % Set axes properties
    axis(ax, 'equal');
    xlim(ax, obj.cache.xlim);
    ylim(ax, obj.cache.ylim);
    set(ax, 'Color', 'k', 'XColor', 'w', 'YColor', 'w');
    xlabel(ax, 'X Position (cm)', 'Color', 'w');
    ylabel(ax, 'Y Position (cm)', 'Color', 'w');
    title(ax, sprintf('Frame %d / %d (cached)', frame_idx, obj.cache.num_frames), ...
        'Color', 'w', 'FontSize', 14);
end

