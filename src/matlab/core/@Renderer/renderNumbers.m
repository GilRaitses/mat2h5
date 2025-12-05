function renderNumbers(obj, ax, data, frame_idx, selected_tracks)
    % renderNumbers - Render track numbers with 50% transparency
    %
    % Inputs:
    %   ax              - Axes handle
    %   data            - Data struct from DataManager
    %   frame_idx       - Frame number
    %   selected_tracks - Logical array of which tracks to show
    %
    % See also: Renderer, renderFrame, renderDots
    
    for tIdx = 1:data.num_tracks
        if selected_tracks(tIdx) && frame_idx <= length(data.tracks(tIdx).pt)
            current_pt = data.tracks(tIdx).pt(frame_idx);
            cTrack = data.colormap(tIdx, :);
            
            % Get position
            if ~isempty(current_pt.mid)
                label_x = current_pt.mid(1);
                label_y = current_pt.mid(2);
            elseif ~isempty(current_pt.head) && ~isempty(current_pt.tail)
                label_x = (current_pt.head(1) + current_pt.tail(1)) / 2;
                label_y = (current_pt.head(2) + current_pt.tail(2)) / 2;
            else
                continue;
            end
            
            % Track number with 50% opacity
            h = text(ax, label_x, label_y, sprintf('%d', tIdx), ...
                'Color', cTrack, ...
                'FontSize', 18, ...
                'FontWeight', 'bold', ...
                'HorizontalAlignment', 'left', ...
                'VerticalAlignment', 'bottom');
            h.Color(4) = 0.5;  % 50% opacity
        end
    end
end

