function contour_data = getContours(obj, track_id)
    % getContours - Get all contour data for a track
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %
    % Returns:
    %   contour_data - Struct with:
    %     .max_length - Maximum contour points
    %     .lengths - Array of contour lengths per frame
    %     .contours_padded - (num_frames, max_length, 2) array (NaN-padded)
    
    if track_id < 1 || track_id > length(obj.tracks)
        error('DataManager:InvalidTrack', 'Track ID %d out of range', track_id);
    end
    
    track = obj.tracks(track_id);
    num_frames = length(track.pt);
    
    % First pass: find max contour length
    max_length = 0;
    lengths = zeros(num_frames, 1);
    
    for i = 1:num_frames
        if ~isempty(track.pt(i).contour)
            lengths(i) = size(track.pt(i).contour, 2);
            max_length = max(max_length, lengths(i));
        end
    end
    
    contour_data = struct();
    contour_data.max_length = max_length;
    contour_data.lengths = lengths;
    
    if max_length == 0
        % No contours
        contour_data.contours_padded = [];
        return;
    end
    
    % Second pass: create padded array
    contours_padded = NaN(num_frames, max_length, 2);
    
    for i = 1:num_frames
        if ~isempty(track.pt(i).contour)
            c = track.pt(i).contour;  % 2 x N matrix
            num_pts = size(c, 2);
            contours_padded(i, 1:num_pts, 1) = c(1, :);  % x coords
            contours_padded(i, 1:num_pts, 2) = c(2, :);  % y coords
        end
    end
    
    contour_data.contours_padded = contours_padded;
end

