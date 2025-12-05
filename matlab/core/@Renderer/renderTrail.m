function renderTrail(obj, ax, data, frame_idx, selected_tracks)
    % renderTrail - Render track trails (historical path)
    %
    % Trails show the last N frames of track movement using the mid point
    % of each track position. Default trail length is 600 frames.
    %
    % Inputs:
    %   ax              - Axes handle
    %   data            - Data struct from DataManager
    %   frame_idx       - Current frame number
    %   selected_tracks - Logical array of which tracks to show
    %
    % See also: Renderer, renderFrame
    
    for tIdx = 1:data.num_tracks
        if selected_tracks(tIdx) && frame_idx <= length(data.tracks(tIdx).pt)
            track = data.tracks(tIdx);
            cTrack = data.colormap(tIdx, :);
            
            % Calculate trail window
            trail_start = max(1, frame_idx - obj.params.trail_length);
            trail_frames = trail_start:frame_idx;
            
            % Extract trail coordinates
            trail_x = [];
            trail_y = [];
            
            for i = 1:length(trail_frames)
                t_frame = trail_frames(i);
                if t_frame <= length(track.pt)
                    pt = track.pt(t_frame);
                    if ~isempty(pt.mid)
                        trail_x(end+1) = pt.mid(1);
                        trail_y(end+1) = pt.mid(2);
                    elseif ~isempty(pt.head) && ~isempty(pt.tail)
                        trail_x(end+1) = (pt.head(1) + pt.tail(1)) / 2;
                        trail_y(end+1) = (pt.head(2) + pt.tail(2)) / 2;
                    end
                end
            end
            
            % Plot trail if sufficient points
            if length(trail_x) > 1
                plot(ax, trail_x, trail_y, '-', 'LineWidth', 1.5, 'Color', cTrack);
            end
        end
    end
end

