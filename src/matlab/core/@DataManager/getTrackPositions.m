function positions = getTrackPositions(obj, track_id, start_frame, end_frame)
    % getTrackPositions - Extract positions for a specific track
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %   start_frame - Start frame (1-indexed)
    %   end_frame - End frame (1-indexed)
    %
    % Returns:
    %   positions - Nx2 array of [x, y] positions (or NaN for missing)
    
    if track_id < 1 || track_id > length(obj.tracks)
        error('DataManager:InvalidTrack', 'Track ID %d out of range', track_id);
    end
    
    track = obj.tracks(track_id);
    positions = [];
    
    for i = start_frame:end_frame
        if i <= length(track.pt) && ~isempty(track.pt(i).mid)
            positions = [positions; track.pt(i).mid'];  % Transpose to row vector
        else
            positions = [positions; NaN, NaN];
        end
    end
end

