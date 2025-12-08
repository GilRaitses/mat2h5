function exportIntegrationMatrix(obj, renderer, data, track_idx, output_path)
    % exportIntegrationMatrix - Generate stimulus response matrix
    %
    % Creates an 8x8 grid showing all stimulus cycles for a single track.
    % Each cell shows -3 to +8 second window around stimulus onset.
    %
    % Inputs:
    %   renderer    - Renderer object for visualization
    %   data        - Data struct from DataManager
    %   track_idx   - Track number to analyze
    %   output_path - Path to save PNG file
    %
    % This method has been validated to correctly process 40 stimulus
    % cycles in the reference experiment.
    %
    % Example:
    %   em = ExportManager();
    %   em.exportIntegrationMatrix(renderer, data, 1, 'matrix_track1.png');
    %
    % See also: ExportManager, DataManager.detectStimuli
    
    fprintf('=== EXPORT MANAGER: Integration Matrix ===\n');
    fprintf('Track: %d\n', track_idx);
    
    % Detect stimulus onsets from LED data
    fprintf('Detecting stimulus cycles...\n');
    
    % Use DataManager to detect stimuli if it's available
    if isa(data, 'DataManager')
        stim_times = data.detectStimuli();
    else
        % Fallback: detect directly from led_data field
        stim_times = detectStimulusOnsets(data.led_data);
    end
    
    num_cycles = length(stim_times);
    fprintf('Found %d stimulus cycles\n', num_cycles);
    
    if num_cycles == 0
        warning('ExportManager:NoStimuli', 'No stimulus cycles detected');
        return;
    end
    
    % Calculate grid dimensions
    grid_cols = 8;
    grid_rows = ceil(num_cycles / grid_cols);
    fprintf('Grid layout: %d x %d\n', grid_rows, grid_cols);
    
    % Create figure
    fig = figure('Name', sprintf('Integration Matrix - Track %d', track_idx), ...
                 'Position', [50 50 1400 1000], ...
                 'Color', 'k');
    
    % Integration window parameters
    fps = 10;  % Approximate frame rate
    pre_sec = 3;   % 3 seconds before
    post_sec = 8;  % 8 seconds after
    pre_frames = pre_sec * fps;
    post_frames = post_sec * fps;
    
    % Get track and color
    if isa(data, 'DataManager')
        track = data.tracks(track_idx);
        track_color = data.colormap(track_idx, :);
        num_frames = data.num_frames;
    else
        track = data.tracks(track_idx);
        track_color = data.colormap(track_idx, :);
        num_frames = data.num_frames;
    end
    
    % Render each stimulus cycle
    for cycle_idx = 1:num_cycles
        % Create subplot
        subplot(grid_rows, grid_cols, cycle_idx);
        ax = gca;
        hold(ax, 'on');
        set(ax, 'Color', 'k', 'XColor', 'w', 'YColor', 'w');
        
        % Get stimulus onset frame
        stim_frame = stim_times(cycle_idx);
        window_start = max(1, stim_frame - pre_frames);
        window_end = min(num_frames, stim_frame + post_frames);
        
        fprintf('  Cycle %d: frames %d to %d (stim at %d)\n', ...
            cycle_idx, window_start, window_end, stim_frame);
        
        % Extract trail for this window
        trail_x = [];
        trail_y = [];
        
        for f = window_start:window_end
            if f <= length(track.pt)
                pt = track.pt(f);
                if ~isempty(pt.mid)
                    trail_x(end+1) = pt.mid(1);
                    trail_y(end+1) = pt.mid(2);
                elseif ~isempty(pt.head) && ~isempty(pt.tail)
                    trail_x(end+1) = (pt.head(1) + pt.tail(1)) / 2;
                    trail_y(end+1) = (pt.head(2) + pt.tail(2)) / 2;
                end
            end
        end
        
        % Plot trail
        if length(trail_x) > 1
            plot(ax, trail_x, trail_y, '-', 'Color', track_color, 'LineWidth', 1.5);
        end
        
        % Draw contour at stimulus onset (Oct 2 method)
        if stim_frame <= length(track.pt)
            pt_stim = track.pt(stim_frame);
            if ~isempty(pt_stim.contour) && size(pt_stim.contour, 2) > 3
                % Oct 2 validated method: white fill with colored edge
                fill(ax, pt_stim.contour(1,:), pt_stim.contour(2,:), 'w', ...
                    'EdgeColor', track_color, 'LineWidth', 2);
            end
            
            % Mark stimulus onset position
            if ~isempty(pt_stim.mid)
                plot(ax, pt_stim.mid(1), pt_stim.mid(2), 'r*', 'MarkerSize', 12, 'LineWidth', 2);
            end
        end
        
        % Set axis limits to zoomed level
        if ~isempty(trail_x) && ~isempty(trail_y)
            x_center = mean(trail_x);
            y_center = mean(trail_y);
            zoom_range = 2.0;  % ±2cm view
            xlim(ax, [x_center - zoom_range, x_center + zoom_range]);
            ylim(ax, [y_center - zoom_range, y_center + zoom_range]);
        end
        
        axis(ax, 'equal');
        
        % Title with cycle number and time
        title(ax, sprintf('Cycle %d (f=%d)', cycle_idx, stim_frame), ...
            'Color', 'w', 'FontSize', 9);
        
        % Remove tick labels for cleaner look
        set(ax, 'XTickLabel', [], 'YTickLabel', []);
    end
    
    % Overall title
    sgtitle(sprintf('Track %d - Integration Matrix (%d Stimulus Cycles)', ...
        track_idx, num_cycles), 'Color', 'w', 'FontSize', 14, 'FontWeight', 'bold');
    
    % Save figure if output path provided
    if nargin >= 5 && ~isempty(output_path)
        fprintf('Saving to: %s\n', output_path);
        exportgraphics(fig, output_path, 'Resolution', 300);
        fprintf('[OK] Integration matrix saved\n');
    end
    
    fprintf('[OK] Integration matrix rendered\n');
    fprintf('=== COMPLETE ===\n');
end

function stim_times = detectStimulusOnsets(led_data)
    % detectStimulusOnsets - Detect stimulus onset times from LED data
    % (Fallback version for when DataManager is not used)
    
    if isempty(led_data) || length(led_data) < 100
        stim_times = [];
        return;
    end
    
    % Use 50% of max as threshold (works better for PWM signals)
    threshold = max(led_data) * 0.5;
    stim_signal = led_data > threshold;
    
    % Find rising edges
    diff_signal = diff([0, stim_signal]);
    onsets = find(diff_signal == 1);
    
    % Debounce: Remove onsets too close together
    min_interval = 100;  % frames (~10 seconds at 10fps)
    stim_times = [];
    last_onset = -inf;
    
    for i = 1:length(onsets)
        if onsets(i) - last_onset >= min_interval
            stim_times(end+1) = onsets(i);
            last_onset = onsets(i);
        end
    end
end

