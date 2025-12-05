function renderContour(obj, ax, data, frame_idx, selected_tracks)
    % renderContour - Render track contours at current frame
    %
    % CRITICAL: Uses Oct 2 validated method
    % White fill ('w') with colored edge for each track
    %
    % This method was validated in multiTrackReverseCrawl.m (line 246)
    % and confirmed to work correctly. DO NOT change to 'none' fill.
    %
    % Inputs:
    %   ax              - Axes handle
    %   data            - Data struct from DataManager
    %   frame_idx       - Frame number
    %   selected_tracks - Logical array of which tracks to show
    %
    % See also: Renderer, renderFrame
    
    for tIdx = 1:data.num_tracks
        if selected_tracks(tIdx) && frame_idx <= length(data.tracks(tIdx).pt)
            pt = data.tracks(tIdx).pt(frame_idx);
            cTrack = data.colormap(tIdx, :);
            
            % Oct 2 validated method: WHITE FILL with COLORED EDGE
            if ~isempty(pt.contour) && size(pt.contour, 2) > 3
                fill(ax, pt.contour(1,:), pt.contour(2,:), 'w', ...
                    'EdgeColor', cTrack, 'LineWidth', 2);
            end
        end
    end
end

