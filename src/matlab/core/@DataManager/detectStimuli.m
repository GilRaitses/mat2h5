function stim_times = detectStimuli(obj)
    % detectStimuli - Detect stimulus onset times from LED data
    %
    % Uses 50% threshold method with debouncing to find stimulus onsets.
    % This method has been validated to correctly identify 40 cycles in
    % the reference experiment.
    %
    % Output:
    %   stim_times - Array of frame indices where stimuli begin
    %
    % Algorithm:
    %   1. Threshold at 50% of max LED value
    %   2. Find rising edges
    %   3. Debounce with 100-frame minimum interval (~10s at 10fps)
    %
    % Example:
    %   dm = DataManager();
    %   dm.loadExperiment(...);
    %   stim_times = dm.detectStimuli();
    %   fprintf('Found %d stimulus cycles\n', length(stim_times));
    %
    % See also: DataManager, loadExperiment
    
    if isempty(obj.led_data) || length(obj.led_data) < 100
        stim_times = [];
        warning('DataManager:NoLED', 'No LED data available for stimulus detection');
        return;
    end
    
    % Use 50% of max as threshold (works better for PWM signals)
    threshold = max(obj.led_data) * 0.5;
    stim_signal = obj.led_data > threshold;
    
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
    
    fprintf('DataManager: Detected %d stimulus onsets\n', length(stim_times));
end

