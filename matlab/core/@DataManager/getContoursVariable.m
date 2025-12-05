function contours_cell = getContoursVariable(obj, track_id)
    % getContoursVariable - Get all contours with variable lengths (no truncation)
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %
    % Returns:
    %   contours_cell - Cell array where each cell contains the contour for that frame
    %                   Each contour is a 2×N matrix (variable N)
    %                   Empty cells for frames without contours
    
    if track_id < 1 || track_id > length(obj.tracks)
        error('DataManager:InvalidTrack', 'Track ID %d out of range', track_id);
    end
    
    track = obj.tracks(track_id);
    num_frames = length(track.pt);
    
    % Create cell array to store variable-length contours
    contours_cell = cell(num_frames, 1);
    
    for i = 1:num_frames
        if ~isempty(track.pt(i).contour)
            % Store as-is (2 × N matrix, variable N)
            contours_cell{i} = track.pt(i).contour;
        else
            % Empty cell for missing contours
            contours_cell{i} = [];
        end
    end
end

