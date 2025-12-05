function expt_data = getCompleteExperiment(obj)
    % getCompleteExperiment - Export COMPLETE experiment structure
    %
    % Mirrors the full MAGAT experiment hierarchy including:
    % - Global experiment fields (fname, camcalinfo, etc.)
    % - globalQuantity (all fields including LED)
    % - Derivation rules (dr)
    % - Segment options (so)
    % - All track data
    %
    % Returns:
    %   expt_data - Complete experiment structure for HDF5 export
    
    expt_data = struct();
    
    % === EXPERIMENT-LEVEL METADATA ===
    expt_data.experiment = struct();
    
    if ~isempty(obj.eset) && ~isempty(obj.eset.expt)
        expt = obj.eset.expt(1);
        
        % File names
        if isfield(expt, 'fname') || isprop(expt, 'fname')
            expt_data.experiment.fname = expt.fname;
        end
        if isfield(expt, 'timfname') || isprop(expt, 'timfname')
            expt_data.experiment.timfname = expt.timfname;
        end
        
        % Camera calibration
        if (isfield(expt, 'camcalinfo') || isprop(expt, 'camcalinfo')) && ~isempty(expt.camcalinfo)
            cal = expt.camcalinfo;
            expt_data.camera_calibration = struct();
            
            if isfield(cal, 'realx'), expt_data.camera_calibration.realx = cal.realx; end
            if isfield(cal, 'realy'), expt_data.camera_calibration.realy = cal.realy; end
            if isfield(cal, 'camx'), expt_data.camera_calibration.camx = cal.camx; end
            if isfield(cal, 'camy'), expt_data.camera_calibration.camy = cal.camy; end
        end
        
        % Elapsed time
        if (isfield(expt, 'elapsedTime') || isprop(expt, 'elapsedTime')) && ~isempty(expt.elapsedTime)
            expt_data.experiment.elapsedTime = expt.elapsedTime;
        end
        
        % === GLOBAL QUANTITIES (ALL FIELDS) ===
        if (isfield(expt, 'globalQuantity') || isprop(expt, 'globalQuantity')) && ~isempty(expt.globalQuantity)
            expt_data.global_quantities = struct();
            gq = expt.globalQuantity;
            
            fprintf('Exporting %d global quantities...\n', length(gq));
            
            % Export ALL globalQuantity fields
            for i = 1:length(gq)
                if isfield(gq(i), 'fieldname') && ~isempty(gq(i).fieldname)
                    field_name = gq(i).fieldname;
                    
                    % Store as struct to preserve ALL metadata
                    gq_data = struct();
                    gq_data.fieldname = field_name;
                    gq_data.index = i;  % Preserve order
                    
                    % Get all available fields from this global quantity
                    if isfield(gq(i), 'yData') && ~isempty(gq(i).yData)
                        gq_data.yData = gq(i).yData;
                        gq_data.yData_length = length(gq(i).yData);
                    end
                    if isfield(gq(i), 'xData') && ~isempty(gq(i).xData)
                        gq_data.xData = gq(i).xData;
                    end
                    if isfield(gq(i), 'units') && ~isempty(gq(i).units)
                        gq_data.units = gq(i).units;
                    end
                    if isfield(gq(i), 'derivtype') && ~isempty(gq(i).derivtype)
                        gq_data.derivtype = gq(i).derivtype;
                    end
                    if isfield(gq(i), 'description') && ~isempty(gq(i).description)
                        gq_data.description = gq(i).description;
                    end
                    
                    % Store with sanitized field name (HDF5-safe)
                    safe_name = strrep(field_name, ' ', '_');
                    safe_name = strrep(safe_name, '-', '_');
                    safe_name = strrep(safe_name, '(', '');
                    safe_name = strrep(safe_name, ')', '');
                    
                    expt_data.global_quantities.(safe_name) = gq_data;
                    
                    fprintf('  - %s (%d values)\n', field_name, length(gq(i).yData));
                end
            end
        end
        
        % === DERIVATION RULES (experiment-level) ===
        if (isfield(expt, 'dr') || isprop(expt, 'dr')) && ~isempty(expt.dr)
            expt_data.derivation_rules = struct();
            dr = expt.dr;
            
            if isfield(dr, 'interpTime'), expt_data.derivation_rules.interpTime = dr.interpTime; end
            if isfield(dr, 'smoothTime'), expt_data.derivation_rules.smoothTime = dr.smoothTime; end
            if isfield(dr, 'derivTime'), expt_data.derivation_rules.derivTime = dr.derivTime; end
        end
        
        % === SEGMENT OPTIONS (experiment-level) ===
        if (isfield(expt, 'so') || isprop(expt, 'so')) && ~isempty(expt.so)
            expt_data.segment_options = struct();
            so = expt.so;
            
            if isfield(so, 'curv_cut'), expt_data.segment_options.curv_cut = so.curv_cut; end
            if isfield(so, 'autoset_curv_cut'), expt_data.segment_options.autoset_curv_cut = so.autoset_curv_cut; end
            if isfield(so, 'theta_cut'), expt_data.segment_options.theta_cut = so.theta_cut; end
            if isfield(so, 'speed_field'), expt_data.segment_options.speed_field = so.speed_field; end
            if isfield(so, 'stop_speed_cut'), expt_data.segment_options.stop_speed_cut = so.stop_speed_cut; end
            if isfield(so, 'start_speed_cut'), expt_data.segment_options.start_speed_cut = so.start_speed_cut; end
            if isfield(so, 'aligned_dp'), expt_data.segment_options.aligned_dp = so.aligned_dp; end
            if isfield(so, 'minRunTime'), expt_data.segment_options.minRunTime = so.minRunTime; end
            if isfield(so, 'minRunLength'), expt_data.segment_options.minRunLength = so.minRunLength; end
            if isfield(so, 'headswing_start'), expt_data.segment_options.headswing_start = so.headswing_start; end
            if isfield(so, 'headswing_stop'), expt_data.segment_options.headswing_stop = so.headswing_stop; end
            if isfield(so, 'smoothBodyFromPeriFreq'), expt_data.segment_options.smoothBodyFromPeriFreq = so.smoothBodyFromPeriFreq; end
            if isfield(so, 'smoothBodyTime'), expt_data.segment_options.smoothBodyTime = so.smoothBodyTime; end
        end
        
        % === ADDITIONAL METADATA ===
        if (isfield(expt, 'metadata') || isprop(expt, 'metadata')) && ~isempty(expt.metadata)
            expt_data.experiment.additional_metadata = expt.metadata;
        end
        
        if (isfield(expt, 'savedTrackDir') || isprop(expt, 'savedTrackDir')) && ~isempty(expt.savedTrackDir)
            expt_data.experiment.savedTrackDir = expt.savedTrackDir;
        end
        if (isfield(expt, 'savedTrackRelDir') || isprop(expt, 'savedTrackRelDir')) && ~isempty(expt.savedTrackRelDir)
            expt_data.experiment.savedTrackRelDir = expt.savedTrackRelDir;
        end
    end
    
    % === SUMMARY INFO ===
    expt_data.num_tracks = obj.num_tracks;
    expt_data.num_frames = obj.num_frames;
    
    % Include detected stimuli for convenience
    if ~isempty(obj.led_data)
        stim_onsets = obj.detectStimuli();
        expt_data.stimulus_onsets = stim_onsets;
    end
end

