function renderFrame(obj, ax, data, frame_idx, selected_tracks)
    % renderFrame - Render complete frame with all visualization layers
    %
    % Inputs:
    %   ax              - Axes handle to draw on
    %   data            - Data struct from DataManager
    %   frame_idx       - Frame number to render
    %   selected_tracks - Logical array of which tracks to show
    %
    % Rendering layers (in order):
    %   1. FID images (if enabled)
    %   2. Track trails (if enabled)
    %   3. Contours (if enabled)
    %   4. White dots (if enabled)
    %   5. Track numbers (if enabled)
    %
    % Example:
    %   renderer = Renderer();
    %   renderer.renderFrame(ax, data, 1000, true(1, data.num_tracks));
    %
    % See also: Renderer, renderFID, renderTrail, renderContour
    
    % Clear axes and prepare
    cla(ax);
    hold(ax, 'on');
    
    % LAYER 1: FID Images
    if obj.params.show_fid
        obj.renderFID(ax, data, frame_idx, selected_tracks);
    end
    
    % LAYER 2: Track Trails
    if obj.params.show_trails
        obj.renderTrail(ax, data, frame_idx, selected_tracks);
    end
    
    % LAYER 3: Contours (Oct 2 method)
    if obj.params.show_contour
        obj.renderContour(ax, data, frame_idx, selected_tracks);
    end
    
    % LAYER 4: White Dots
    if obj.params.show_dots
        obj.renderDots(ax, data, frame_idx, selected_tracks);
    end
    
    % LAYER 5: Track Numbers
    if obj.params.show_numbers
        obj.renderNumbers(ax, data, frame_idx, selected_tracks);
    end
    
    % Configure axes appearance
    obj.configureAxes(ax, frame_idx, data.num_frames);
end

