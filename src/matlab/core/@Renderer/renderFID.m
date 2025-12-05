function renderFID(obj, ax, data, frame_idx, selected_tracks)
    % renderFID - Render FID (Feature ID) images for selected tracks
    %
    % Uses the validated method from Oct 2 multiTrackReverseCrawl.m:
    % drawTrackImage() with 'pretty' option, no spine, no arrow, no contour
    %
    % Inputs:
    %   ax              - Axes handle
    %   data            - Data struct from DataManager
    %   frame_idx       - Frame number
    %   selected_tracks - Logical array of which tracks to show
    %
    % See also: Renderer, renderFrame
    
    for tIdx = 1:data.num_tracks
        if selected_tracks(tIdx) && frame_idx <= length(data.tracks(tIdx).pt)
            try
                % Oct 2 validated method: drawTrackImage with 'pretty' option
                data.tracks(tIdx).pt(frame_idx).drawTrackImage(data.camcalinfo, ...
                    'fid', data.fid, ...
                    'Axes', ax, ...
                    'pretty', true, ...
                    'drawSpine', false, ...
                    'drawHeadArrow', false, ...
                    'drawContour', false);
            catch
                % Silent error handling for speed
            end
        end
    end
end

