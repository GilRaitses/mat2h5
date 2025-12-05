function renderDots(obj, ax, data, frame_idx, selected_tracks)
    % renderDots - Render white dots at current track positions
    %
    % Inputs:
    %   ax              - Axes handle
    %   data            - Data struct from DataManager
    %   frame_idx       - Frame number
    %   selected_tracks - Logical array of which tracks to show
    %
    % See also: Renderer, renderFrame, renderNumbers
    
    for tIdx = 1:data.num_tracks
        if selected_tracks(tIdx) && frame_idx <= length(data.tracks(tIdx).pt)
            current_pt = data.tracks(tIdx).pt(frame_idx);
            
            % Get position
            if ~isempty(current_pt.mid)
                pos_x = current_pt.mid(1);
                pos_y = current_pt.mid(2);
            elseif ~isempty(current_pt.head) && ~isempty(current_pt.tail)
                pos_x = (current_pt.head(1) + current_pt.tail(1)) / 2;
                pos_y = (current_pt.head(2) + current_pt.tail(2)) / 2;
            else
                continue;
            end
            
            % White dot at current position
            plot(ax, pos_x, pos_y, 'w.', 'MarkerSize', 8);
        end
    end
end

