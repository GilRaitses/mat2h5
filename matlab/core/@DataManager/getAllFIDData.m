function fid_data = getAllFIDData(obj, track_id)
    % getAllFIDData - Extract ALL FID image data at once (no rendering!)
    %
    % Gets imData from all pt structures if available.
    % Much faster than rendering 24,000 times!
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %
    % Returns:
    %   fid_data - Struct with:
    %     .has_imData: true if imData exists
    %     .imData_cell: Cell array of images (empty if no imData)
    %     .imOffsets: (N, 2) array of offsets
    
    if track_id < 1 || track_id > length(obj.tracks)
        error('DataManager:InvalidTrack', 'Track ID %d out of range', track_id);
    end
    
    track = obj.tracks(track_id);
    num_frames = length(track.pt);
    
    fid_data = struct();
    fid_data.has_imData = false;
    fid_data.imData_cell = cell(num_frames, 1);
    fid_data.imOffsets = zeros(num_frames, 2);
    
    % Check if first frame has imData
    if ~isempty(track.pt(1).imData) && length(track.pt(1).imData) > 0
        fid_data.has_imData = true;
        
        % Extract ALL imData at once
        for i = 1:num_frames
            if ~isempty(track.pt(i).imData)
                fid_data.imData_cell{i} = track.pt(i).imData;
            end
            
            if ~isempty(track.pt(i).imOffset)
                fid_data.imOffsets(i, :) = track.pt(i).imOffset;
            end
        end
    end
end

