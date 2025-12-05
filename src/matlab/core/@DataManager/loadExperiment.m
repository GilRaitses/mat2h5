function loadExperiment(obj, mat_file, tracks_dir, bin_file)
    % loadExperiment - Load experiment data from MAT, tracks, and FID files
    %
    % Inputs:
    %   mat_file   - Path to experiment MAT file
    %   tracks_dir - Path to tracks directory
    %   bin_file   - Path to binary FID file
    %
    % This method:
    %   1. Loads ExperimentSet from MAT file
    %   2. Loads tracks from directory
    %   3. Performs track interpolation (critical!)
    %   4. Opens FID binary
    %   5. Extracts LED stimulus data
    %   6. Generates color map
    %
    % Example:
    %   dm = DataManager();
    %   dm.loadExperiment(mat_file, tracks_dir, bin_file);
    %
    % See also: DataManager, detectStimuli
    
    fprintf('=== DATA MANAGER: Loading Experiment ===\n');
    
    % Load experiment
    fprintf('Loading experiment: %s\n', mat_file);
    obj.eset = ExperimentSet.fromMatFiles({mat_file});
    obj.eset.expt(1).fname = bin_file;
    
    % Load tracks
    fprintf('Loading tracks from: %s\n', tracks_dir);
    obj.tracks = obj.loadTracksFromFolder(tracks_dir);
    
    if isempty(obj.tracks)
        error('DataManager:NoTracks', 'No tracks loaded from directory');
    end
    
    % Link tracks to experiment
    for k = 1:numel(obj.tracks)
        obj.tracks(k).expt = obj.eset.expt(1);
    end
    obj.eset.expt(1).track = obj.tracks;
    
    fprintf('✓ Loaded %d tracks\n', length(obj.tracks));
    
    % CRITICAL: Interpolate tracks to prevent drift
    fprintf('Interpolating tracks...\n');
    obj.tracks = obj.preprocessTrackInterpolation(obj.tracks);
    fprintf('✓ Interpolation complete\n');
    
    % Open FID binary (if method exists)
    obj.fid = -1;
    obj.camcalinfo = [];
    if ismethod(obj.eset.expt(1), 'openDataFile')
        try
            obj.eset.expt(1).openDataFile;
            obj.fid = obj.eset.expt(1).fid;
            obj.camcalinfo = obj.eset.expt(1).camcalinfo;
            
            if obj.fid > 0
                fprintf('✓ FID opened: %d\n', obj.fid);
            else
                warning('DataManager:FIDError', 'FID access failed');
            end
        catch ME
            warning('DataManager:FIDError', 'FID access failed: %s', ME.message);
        end
    else
        % Method doesn't exist - skip FID (not needed for H5 export)
        fprintf('  openDataFile method not available (skipping - not needed for H5 export)\n');
    end
    
    % Get LED stimulus data
    obj.led_data = [];
    try
        % Check if globalQuantity exists
        if isprop(obj.eset.expt(1), 'globalQuantity') && ~isempty(obj.eset.expt(1).globalQuantity)
            led_idx = find(strcmpi({obj.eset.expt(1).globalQuantity.fieldname}, 'led1Val'));
            if ~isempty(led_idx)
                obj.led_data = obj.eset.expt(1).globalQuantity(led_idx).yData;
                fprintf('✓ LED data loaded: %d frames\n', length(obj.led_data));
            end
        end
    catch ME
        fprintf('  No LED data available: %s\n', ME.message);
    end
    
    % Determine frame count
    obj.num_frames = 0;
    for i = 1:length(obj.tracks)
        obj.num_frames = max(obj.num_frames, length(obj.tracks(i).pt));
    end
    
    % Generate color map
    obj.num_tracks = length(obj.tracks);
    obj.colormap = lines(obj.num_tracks);
    
    fprintf('=== DATA LOADED SUCCESSFULLY ===\n');
    fprintf('Tracks: %d, Frames: %d\n', obj.num_tracks, obj.num_frames);
end

