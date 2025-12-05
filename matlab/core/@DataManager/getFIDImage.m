function fid_image = getFIDImage(obj, track_id, frame_idx)
    % getFIDImage - Render FID image for a single frame using proven Oct 2 method
    %
    % Uses drawTrackImage with FID binary (proven working from multiTrackReverseCrawl.m)
    %
    % Inputs:
    %   track_id - Track ID (1-indexed)
    %   frame_idx - Frame index (1-indexed)
    %
    % Returns:
    %   fid_image - Grayscale image matrix (H×W uint8) or empty if unavailable
    
    if track_id < 1 || track_id > length(obj.tracks)
        fid_image = [];
        return;
    end
    
    track = obj.tracks(track_id);
    
    if frame_idx < 1 || frame_idx > length(track.pt)
        fid_image = [];
        return;
    end
    
    pt = track.pt(frame_idx);
    
    if isempty(pt.mid) || obj.fid <= 0
        fid_image = [];
        return;
    end
    
    try
        % SUPPRESS ALL OUTPUT
        warning('off', 'all');
        
        % Create offscreen figure (completely silent)
        fig = figure('Visible', 'off', 'Position', [0 0 100 50], ...
                    'CreateFcn', '', 'DeleteFcn', '');
        ax = axes(fig, 'Position', [0 0 1 1], ...
                 'CreateFcn', '', 'DeleteFcn', '');
        hold(ax, 'on');
        
        % Disable all property displays
        set(0, 'ShowHiddenHandles', 'off');
        
        % PROVEN METHOD from multiTrackReverseCrawl.m lines 121-127
        pt.drawTrackImage(obj.camcalinfo, 'fid', obj.fid, ...
            'Axes', ax, 'pretty', true, ...
            'drawSpine', false, 'drawHeadArrow', false, ...
            'drawContour', false);
        
        % Set proper axis limits for consistent crop
        axis(ax, 'tight');
        axis(ax, 'equal');
        
        % Capture frame
        frame_data = getframe(ax);
        img = frame_data.cdata;
        
        % Convert to grayscale
        if size(img, 3) == 3
            img = rgb2gray(img);
        end
        
        fid_image = img;
        
        % Cleanup
        close(fig);
        
    catch ME
        % Return empty on error
        fid_image = [];
        try
            close(fig);
        catch
        end
    end
end

