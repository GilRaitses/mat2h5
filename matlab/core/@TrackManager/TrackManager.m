classdef TrackManager < handle
    % TrackManager - Handles track selection and manipulation
    %
    % This class manages which tracks are selected for visualization
    % and provides utilities for track data access.
    %
    % Properties:
    %   selected_tracks - Logical array of selected tracks
    %   num_tracks      - Total number of tracks
    %
    % Methods:
    %   selectAll    - Select all tracks
    %   deselectAll  - Deselect all tracks
    %   toggleTrack  - Toggle selection of a specific track
    %   selectTracks - Select specific tracks by index
    %   getTrackData - Get data for a specific track
    %
    % Example:
    %   tm = TrackManager(12);  % 12 tracks
    %   tm.selectAll();
    %   tm.toggleTrack(5);  % Deselect track 5
    %
    % See also: BehavioralVideoExplorer, DataManager
    %
    % 2025-10-16 - Created for class refactor
    
    properties
        selected_tracks  % Logical array of selected tracks
        num_tracks       % Total number of tracks
    end
    
    methods
        function obj = TrackManager(num_tracks)
            % Constructor - initialize track manager
            %
            % Input:
            %   num_tracks - Number of tracks in experiment
            
            if nargin < 1
                num_tracks = 0;
            end
            
            obj.num_tracks = num_tracks;
            obj.selected_tracks = true(1, num_tracks);  % All selected by default
        end
        
        function selectAll(obj)
            % selectAll - Select all tracks
            obj.selected_tracks(:) = true;
        end
        
        function deselectAll(obj)
            % deselectAll - Deselect all tracks
            obj.selected_tracks(:) = false;
        end
        
        function toggleTrack(obj, track_idx)
            % toggleTrack - Toggle selection of a specific track
            %
            % Input:
            %   track_idx - Track index to toggle
            
            if track_idx >= 1 && track_idx <= obj.num_tracks
                obj.selected_tracks(track_idx) = ~obj.selected_tracks(track_idx);
            end
        end
        
        function selectTracks(obj, track_indices)
            % selectTracks - Select specific tracks by index
            %
            % Input:
            %   track_indices - Array of track indices to select
            
            obj.deselectAll();
            for i = 1:length(track_indices)
                idx = track_indices(i);
                if idx >= 1 && idx <= obj.num_tracks
                    obj.selected_tracks(idx) = true;
                end
            end
        end
        
        function track_data = getTrackData(obj, data, track_idx, frame_idx)
            % getTrackData - Get data for a specific track at a frame
            %
            % Inputs:
            %   data      - Data struct from DataManager
            %   track_idx - Track index
            %   frame_idx - Frame index
            %
            % Output:
            %   track_data - Struct with track information
            
            track_data = struct();
            
            if track_idx < 1 || track_idx > length(data.tracks)
                return;
            end
            
            track = data.tracks(track_idx);
            
            track_data.track_idx = track_idx;
            track_data.num_frames = length(track.pt);
            track_data.color = data.colormap(track_idx, :);
            
            if frame_idx >= 1 && frame_idx <= length(track.pt)
                pt = track.pt(frame_idx);
                track_data.head = pt.head;
                track_data.tail = pt.tail;
                track_data.mid = pt.mid;
                track_data.contour = pt.contour;
                
                if ~isempty(pt.mid)
                    track_data.position = pt.mid;
                elseif ~isempty(pt.head) && ~isempty(pt.tail)
                    track_data.position = [(pt.head(1) + pt.tail(1))/2; 
                                           (pt.head(2) + pt.tail(2))/2];
                else
                    track_data.position = [];
                end
            end
        end
        
        function count = getSelectedCount(obj)
            % getSelectedCount - Get number of selected tracks
            count = sum(obj.selected_tracks);
        end
    end
end

