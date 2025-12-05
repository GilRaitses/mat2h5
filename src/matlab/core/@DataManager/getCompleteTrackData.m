function track_export = getCompleteTrackData(obj, track_id)
    % getCompleteTrackData - Export COMPLETE track structure to HDF5-friendly format
    %
    % Mirrors the original MAGAT track structure for complete data preservation.
    % Uses concatenated arrays for variable-length data (contours, spine).
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %
    % Returns:
    %   track_export - Complete track data structure
    
    if track_id < 1 || track_id > length(obj.tracks)
        error('DataManager:InvalidTrack', 'Track ID %d out of range', track_id);
    end
    
    track = obj.tracks(track_id);
    num_frames = length(track.pt);
    
    track_export = struct();
    
    % === TRACK-LEVEL METADATA ===
    track_export.metadata = struct();
    track_export.metadata.npts = track.npts;
    track_export.metadata.nt = track.nt;
    track_export.metadata.locInFile = track.locInFile;
    if isprop(track, 'trackNum')
        track_export.metadata.trackNum = track.trackNum;
    end
    if isprop(track, 'startFrame')
        track_export.metadata.startFrame = track.startFrame;
    end
    if isprop(track, 'endFrame')
        track_export.metadata.endFrame = track.endFrame;
    end
    
    % === LOGICAL/STATE ARRAYS ===
    track_export.state = struct();
    
    if ~isempty(track.headSwing) && length(track.headSwing) > 0
        track_export.state.headSwing = track.headSwing;
    end
    
    if ~isempty(track.isrun) && length(track.isrun) > 0
        track_export.state.isrun = track.isrun;
    end
    
    if ~isempty(track.iscollision) && length(track.iscollision) > 0
        track_export.state.iscollision = track.iscollision;
    end
    
    % === POINT DATA (pt) - Fixed and variable length ===
    track_export.points = struct();
    
    % Pre-allocate fixed arrays
    track_export.points.mid = zeros(num_frames, 2);
    track_export.points.head = zeros(num_frames, 2);
    track_export.points.tail = zeros(num_frames, 2);
    track_export.points.loc = zeros(num_frames, 2);
    track_export.points.area = zeros(num_frames, 1);
    
    % Variable-length data (concatenated)
    all_contour_pts = [];
    contour_idx = zeros(num_frames + 1, 1);
    all_spine_pts = [];
    spine_idx = zeros(num_frames + 1, 1);
    
    % Collect point data
    for i = 1:num_frames
        pt = track.pt(i);
        
        % Fixed-size arrays
        track_export.points.mid(i, :) = pt.mid';
        track_export.points.head(i, :) = pt.head';
        track_export.points.tail(i, :) = pt.tail';
        
        if ~isempty(pt.loc)
            track_export.points.loc(i, :) = pt.loc';
        end
        
        if ~isempty(pt.area)
            track_export.points.area(i) = pt.area;
        end
        
        % Variable-length contours
        if ~isempty(pt.contour)
            c = pt.contour';  % N × 2
            all_contour_pts = [all_contour_pts; c];
        end
        contour_idx(i + 1) = size(all_contour_pts, 1);
        
        % Variable-length spine
        if ~isempty(pt.spine)
            s = pt.spine';  % Typically 11 × 2
            all_spine_pts = [all_spine_pts; s];
        end
        spine_idx(i + 1) = size(all_spine_pts, 1);
    end
    
    % Store concatenated data
    track_export.points.contour_points = all_contour_pts;
    track_export.points.contour_indices = contour_idx;
    track_export.points.spine_points = all_spine_pts;
    track_export.points.spine_indices = spine_idx;
    
    % === DERIVED QUANTITIES (dq) - ALL FIELDS FROM single_track_summary.txt ===
    track_export.derived = struct();
    
    if ~isempty(track.dq)
        % Export ALL dq fields systematically
        dq_fields = fieldnames(track.dq);
        
        for i = 1:length(dq_fields)
            field_name = dq_fields{i};
            if ~isempty(track.dq.(field_name))
                track_export.derived.(field_name) = track.dq.(field_name);
            end
        end
        
        % Ensure we have key fields from reference doc:
        % iloc, sloc, vel, speed, nspeed, vnorm, theta, nvel, ihtValid
        % pathLength, displacement, deltatheta, ddtheta, acc, curv
        % ispine, spineTheta, sspineTheta, ihead, imid, itail
        % shead, smid, vel_dp, spineLength
        % gassp, dgassp, vocppm, dvocppm, eti (if present)
    end
    
    % === DERIVATION RULES (dr) ===
    track_export.derivation_rules = struct();
    
    % track.dr is a DerivationRules object, use isprop instead of isfield
    if ~isempty(track.dr)
        if isprop(track.dr, 'interpTime'), track_export.derivation_rules.interpTime = track.dr.interpTime; end
        if isprop(track.dr, 'smoothTime'), track_export.derivation_rules.smoothTime = track.dr.smoothTime; end
        if isprop(track.dr, 'derivTime'), track_export.derivation_rules.derivTime = track.dr.derivTime; end
    end
    
    % === SEGMENT OPTIONS (so) ===
    track_export.segment_options = struct();
    
    % track.so is a MaggotSegmentOptions object, use isprop instead of isfield
    if ~isempty(track.so)
        if isprop(track.so, 'curv_cut'), track_export.segment_options.curv_cut = track.so.curv_cut; end
        if isprop(track.so, 'theta_cut'), track_export.segment_options.theta_cut = track.so.theta_cut; end
        if isprop(track.so, 'minRunTime'), track_export.segment_options.minRunTime = track.so.minRunTime; end
        if isprop(track.so, 'minRunLength'), track_export.segment_options.minRunLength = track.so.minRunLength; end
    end
    
    % === SUMMARY ===
    track_export.num_frames = num_frames;
    track_export.num_contour_points = size(all_contour_pts, 1);
    track_export.num_spine_points = size(all_spine_pts, 1);
end

