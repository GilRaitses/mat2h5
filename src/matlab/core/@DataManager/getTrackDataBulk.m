function track_data = getTrackDataBulk(obj, track_id)
    % getTrackDataBulk - Efficiently export all body data for a track
    %
    % Returns all data in concatenated format for efficient HDF5 storage.
    % Uses concatenated arrays with indices for variable-length data (contours, spine).
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %
    % Returns:
    %   track_data - Struct with:
    %     .mid: (N, 2) - Midpoint positions
    %     .head: (N, 2) - Head positions
    %     .tail: (N, 2) - Tail positions
    %     .contours_concat: (total_contour_pts, 2) - All contours concatenated
    %     .contour_indices: (N+1, 1) - Start index for each frame
    %     .spines_concat: (total_spine_pts, 2) - All spines concatenated
    %     .spine_indices: (N+1, 1) - Start index for each frame
    %     .derived: Struct with speed, theta, curv arrays
    
    if track_id < 1 || track_id > length(obj.tracks)
        error('DataManager:InvalidTrack', 'Track ID %d out of range', track_id);
    end
    
    track = obj.tracks(track_id);
    num_frames = length(track.pt);
    
    % === SIMPLE ARRAYS (Fixed size per frame) ===
    
    % Pre-allocate
    mid_pts = zeros(num_frames, 2);
    head_pts = zeros(num_frames, 2);
    tail_pts = zeros(num_frames, 2);
    
    % === VARIABLE-LENGTH DATA (Concatenated format) ===
    
    % Contours
    all_contour_pts = [];
    contour_idx = zeros(num_frames + 1, 1);  % +1 for final index
    contour_idx(1) = 0;
    
    % Spines
    all_spine_pts = [];
    spine_idx = zeros(num_frames + 1, 1);
    spine_idx(1) = 0;
    
    % === COLLECT DATA ===
    
    for i = 1:num_frames
        pt = track.pt(i);
        
        % Simple points (transpose to row vector)
        if ~isempty(pt.mid)
            mid_pts(i, :) = pt.mid';
        else
            mid_pts(i, :) = [NaN, NaN];
        end
        
        if ~isempty(pt.head)
            head_pts(i, :) = pt.head';
        else
            head_pts(i, :) = [NaN, NaN];
        end
        
        if ~isempty(pt.tail)
            tail_pts(i, :) = pt.tail';
        else
            tail_pts(i, :) = [NaN, NaN];
        end
        
        % Contours (variable length)
        if ~isempty(pt.contour)
            c = pt.contour';  % Transpose to N × 2
            all_contour_pts = [all_contour_pts; c];
        end
        contour_idx(i + 1) = size(all_contour_pts, 1);
        
        % Spine (typically 11 points, but handle variability)
        if ~isempty(pt.spine)
            s = pt.spine';  % Transpose to 11 × 2
            all_spine_pts = [all_spine_pts; s];
        end
        spine_idx(i + 1) = size(all_spine_pts, 1);
    end
    
    % === PACKAGE DATA ===
    
    track_data = struct();
    
    % Simple arrays
    track_data.mid = mid_pts;
    track_data.head = head_pts;
    track_data.tail = tail_pts;
    
    % Concatenated arrays
    track_data.contours_concat = all_contour_pts;
    track_data.contour_indices = contour_idx;
    track_data.spines_concat = all_spine_pts;
    track_data.spine_indices = spine_idx;
    
    % === DERIVED QUANTITIES (Tier 1 only) ===
    
    track_data.derived = struct();
    
    % Check if derived quantities exist
    if ~isempty(track.dq)
        % Speed
        if isfield(track.dq, 'speed') && ~isempty(track.dq.speed)
            track_data.derived.speed = track.dq.speed';
        end
        
        % Direction (theta)
        if isfield(track.dq, 'theta') && ~isempty(track.dq.theta)
            track_data.derived.direction = track.dq.theta';
        end
        
        % Curvature
        if isfield(track.dq, 'curv') && ~isempty(track.dq.curv)
            track_data.derived.curvature = track.dq.curv';
        end
    end
    
    % === METADATA ===
    
    track_data.num_frames = num_frames;
    track_data.num_contour_points = size(all_contour_pts, 1);
    track_data.num_spine_points = size(all_spine_pts, 1);
end

