function dq_info = listDerivedQuantities(obj, track_id)
% listDerivedQuantities - List available derived quantities for a track
%
% Returns struct with names and sizes of all available derived quantities
%
% 2025-10-20

    track = obj.tracks(track_id);
    
    % Common derived quantities to check
    test_names = {'sloc', 'v', 'S', 'dir', 'spineAngle', 'bodyAngle', ...
                  'angSpeed', 'curvature', 'speed', 'omega', 'pathLength', ...
                  'ecc', 'midline', 'spine', 'head', 'tail'};
    
    dq_info = struct();
    dq_info.available = {};
    dq_info.shapes = {};
    dq_info.descriptions = {};
    
    for i = 1:length(test_names)
        qty_name = test_names{i};
        try
            data = track.getDerivedQuantity(qty_name);
            if ~isempty(data)
                dq_info.available{end+1} = qty_name;
                dq_info.shapes{end+1} = size(data);
                
                % Add descriptions
                switch qty_name
                    case 'sloc'
                        desc = 'Smoothed location (x,y)';
                    case 'v'
                        desc = 'Velocity vector (vx,vy)';
                    case 'S'
                        desc = 'Arc length along path';
                    case 'dir'
                        desc = 'Direction angle';
                    case 'spineAngle'
                        desc = 'Spine curvature angle';
                    case 'bodyAngle'
                        desc = 'Body orientation';
                    case 'curvature'
                        desc = 'Path curvature';
                    case 'speed'
                        desc = 'Speed magnitude';
                    case 'midline'
                        desc = 'Spine midline points';
                    case 'spine'
                        desc = 'Spine curve data';
                    otherwise
                        desc = 'Computed metric';
                end
                dq_info.descriptions{end+1} = desc;
            end
        catch
            % Quantity not available
        end
    end
    
    dq_info.count = length(dq_info.available);
end
