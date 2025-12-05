classdef DataManager < handle
    % DataManager - Handles data loading and preprocessing for behavioral video analysis
    %
    % This class manages experiment data loading, track interpolation, and
    % stimulus detection. It serves as the data access layer for the 
    % BehavioralVideoExplorer application.
    %
    % Properties:
    %   eset        - ExperimentSet object
    %   tracks      - Array of Track objects (interpolated)
    %   fid         - File ID for binary FID data
    %   camcalinfo  - Camera calibration info
    %   num_tracks  - Number of tracks in experiment
    %   num_frames  - Total frames in experiment
    %   colormap    - Color map for track visualization
    %   led_data    - LED stimulus data (if available)
    %
    % Methods:
    %   loadExperiment  - Load experiment from MAT, tracks, and FID files
    %   detectStimuli   - Detect stimulus onset times from LED data
    %
    % Example:
    %   dm = DataManager();
    %   dm.loadExperiment(mat_file, tracks_dir, bin_file);
    %   stim_times = dm.detectStimuli();
    %
    % See also: BehavioralVideoExplorer, Renderer, CacheManager
    %
    % 2025-10-16 - Refactored from DataLoader.m
    
    properties
        eset           % ExperimentSet object
        tracks         % Track array (interpolated)
        fid            % File ID for binary FID
        camcalinfo     % Camera calibration info
        num_tracks     % Number of tracks
        num_frames     % Total frames
        colormap       % Track color map
        led_data       % LED stimulus data
    end
    
    methods
        function obj = DataManager()
            % Constructor - initializes empty DataManager
            obj.eset = [];
            obj.tracks = [];
            obj.fid = -1;
            obj.camcalinfo = [];
            obj.num_tracks = 0;
            obj.num_frames = 0;
            obj.colormap = [];
            obj.led_data = [];
        end
        
        % External method signatures (implemented in separate files)
        loadExperiment(obj, mat_file, tracks_dir, bin_file)
        stim_times = detectStimuli(obj)
    end
    
    methods (Access = private)
        % Private helper methods implemented in this file
        function tracks = loadTracksFromFolder(~, tracks_dir)
            % Load all track*.mat files from directory
            tracks = [];
            track_files = dir(fullfile(tracks_dir, 'track*.mat'));
            
            if isempty(track_files)
                return;
            end
            
            % Sort numerically
            nums = zeros(length(track_files), 1);
            for i = 1:length(track_files)
                [~, name, ~] = fileparts(track_files(i).name);
                num = str2double(regexp(name, '\d+', 'match', 'once'));
                if ~isnan(num)
                    nums(i) = num;
                end
            end
            [~, idx] = sort(nums);
            track_files = track_files(idx);
            
            % Load each track file
            for i = 1:length(track_files)
                try
                    track_data = load(fullfile(tracks_dir, track_files(i).name));
                    fields = fieldnames(track_data);
                    for j = 1:length(fields)
                        if isa(track_data.(fields{j}), 'Track') || ...
                           isa(track_data.(fields{j}), 'MaggotTrack')
                            if isempty(tracks)
                                tracks = track_data.(fields{j});
                            else
                                tracks(end+1) = track_data.(fields{j});
                            end
                            break;
                        end
                    end
                catch
                    % Skip invalid track files
                end
            end
        end
        
        function interpolated_tracks = preprocessTrackInterpolation(~, tracks)
            % Align raw track.pt with smoothed sloc timeline
            % Prevents drift between raw and smoothed data
            interpolated_tracks = tracks;
            
            for tIdx = 1:length(tracks)
                track = tracks(tIdx);
                sloc = track.getDerivedQuantity('sloc');
                reference_length = size(sloc, 2);
                pt_length = length(track.pt);
                
                if pt_length < reference_length
                    interpolated_tracks(tIdx) = interpolateTrackPoints(track, reference_length);
                end
            end
            
            function interpolated_track = interpolateTrackPoints(track, target_length)
                % Interpolate head/tail/contour data to match target timeline
                interpolated_track = track;
                pt_length = length(track.pt);
                
                if pt_length >= target_length
                    return;
                end
                
                existing_frames = 1:pt_length;
                target_frames = 1:target_length;
                
                % Extract and interpolate head positions
                head_x = zeros(1, pt_length);
                head_y = zeros(1, pt_length);
                tail_x = zeros(1, pt_length);
                tail_y = zeros(1, pt_length);
                
                for i = 1:pt_length
                    if ~isempty(track.pt(i).head)
                        head_x(i) = track.pt(i).head(1);
                        head_y(i) = track.pt(i).head(2);
                    elseif i > 1
                        head_x(i) = head_x(i-1);
                        head_y(i) = head_y(i-1);
                    end
                    
                    if ~isempty(track.pt(i).tail)
                        tail_x(i) = track.pt(i).tail(1);
                        tail_y(i) = track.pt(i).tail(2);
                    elseif i > 1
                        tail_x(i) = tail_x(i-1);
                        tail_y(i) = tail_y(i-1);
                    end
                end
                
                % Perform interpolation
                interp_head_x = interp1(existing_frames, head_x, target_frames, 'linear', 'extrap');
                interp_head_y = interp1(existing_frames, head_y, target_frames, 'linear', 'extrap');
                interp_tail_x = interp1(existing_frames, tail_x, target_frames, 'linear', 'extrap');
                interp_tail_y = interp1(existing_frames, tail_y, target_frames, 'linear', 'extrap');
                
                % Extend track.pt array
                for i = (pt_length+1):target_length
                    new_pt = track.pt(end);
                    new_pt.head = [interp_head_x(i); interp_head_y(i)];
                    new_pt.tail = [interp_tail_x(i); interp_tail_y(i)];
                    new_pt.mid = [(interp_head_x(i) + interp_tail_x(i))/2; 
                                  (interp_head_y(i) + interp_tail_y(i))/2];
                    
                    % Scale contour
                    if ~isempty(track.pt(end).contour)
                        last_contour = track.pt(end).contour;
                        last_center = mean(last_contour, 2);
                        new_pt.contour = last_contour + (new_pt.mid - last_center);
                    end
                    
                    interpolated_track.pt(i) = new_pt;
                end
                
                % Maintain experiment reference
                if isprop(track, 'expt') && ~isempty(track.expt)
                    interpolated_track.expt = track.expt;
                end
                
                interpolated_track.npts = target_length;
            end
        end
    end
end

