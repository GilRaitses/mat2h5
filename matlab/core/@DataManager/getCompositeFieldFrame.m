function frame_image = getCompositeFieldFrame(obj, frame_idx)
    % getCompositeFieldFrame - Render FULL FIELD frame with ALL tracks
    %
    % Like multiTrackReverseCrawl - renders all tracks onto ONE frame
    % Much faster than rendering each track separately!
    %
    % Inputs:
    %   frame_idx - Frame index (1-indexed)
    %
    % Returns:
    %   frame_image - Composite image with all tracks (grayscale uint8)
    
    if obj.fid <= 0
        frame_image = [];
        return;
    end
    
    try
        % SUPPRESS OUTPUT
        warning('off', 'all');
        
        % Create offscreen figure for full field
        fig = figure('Visible', 'off', 'Position', [0 0 800 600]);
        ax = axes(fig, 'Position', [0 0 1 1]);
        hold(ax, 'on');
        
        % Draw ALL tracks' FID patches onto this ONE frame
        for tid = 1:length(obj.tracks)
            if frame_idx <= length(obj.tracks(tid).pt)
                try
                    % PROVEN METHOD: drawTrackImage for each track on same axis
                    obj.tracks(tid).pt(frame_idx).drawTrackImage(obj.camcalinfo, ...
                        'fid', obj.fid, 'Axes', ax, 'pretty', true, ...
                        'drawSpine', false, 'drawHeadArrow', false, ...
                        'drawContour', false);
                catch
                    % Skip if track has no data at this frame
                end
            end
        end
        
        % Set full field limits
        xlim(ax, [5.7, 19.0]);
        ylim(ax, [6.2, 18.8]);
        axis(ax, 'equal');
        set(ax, 'Color', 'k');
        
        % Capture composite frame
        frame_data = getframe(ax);
        img = frame_data.cdata;
        
        % Convert to grayscale
        if size(img, 3) == 3
            img = rgb2gray(img);
        end
        
        frame_image = img;
        
        close(fig);
        
    catch ME
        frame_image = [];
        try
            close(fig);
        catch
        end
    end
end

