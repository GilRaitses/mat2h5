function frame_info = getFrameData(obj, frame_idx)
    % getFrameData - Get all track positions at a specific frame
    %
    % Inputs:
    %   frame_idx - Frame index (1-indexed)
    %
    % Returns:
    %   frame_info - Struct with frame number and track data (as cell array)
    
    frame_info = struct();
    frame_info.frame = frame_idx;
    frame_info.track_ids = [];
    frame_info.centers = [];
    frame_info.has_contours = [];
    
    for tid = 1:length(obj.tracks)
        track = obj.tracks(tid);
        if frame_idx <= length(track.pt) && ~isempty(track.pt(frame_idx).mid)
            frame_info.track_ids(end+1) = tid;
            frame_info.centers(end+1,:) = track.pt(frame_idx).mid';
            frame_info.has_contours(end+1) = ~isempty(track.pt(frame_idx).contour);
        end
    end
end

