function [rate, time_bins, counts] = rate_from_time_corrected(event_times, total_duration, bin_size, normalize_by_time)
% RATE_FROM_TIME_CORRECTED Compute event rate using non-overlapping bins
%
%   ORIGINAL SCRIPT: rate_from_time.m
%   Location: Matlab-Track-Analysis-MirnaLab/user specific/yiming/rate_from_time.m
%   Also used in: load_multi_data_gr21a.m (line 325)
%
%   Original code:
%       function r = rate_from_time(t, T, s, b)
%       m = fix(T/s);
%       r = zeros(1, m + 1);
%       for j = 0 : m
%           tleft = mod(j*s-b, T);  % periodic boundary condition
%           tright = mod(j*s, T);
%           if tleft>tright
%               r(j+1) = nnz(t >= tleft | t < tright ) / b;
%           else
%               r(j+1) = nnz(t >= tleft & t < tright ) / b;
%           end
%       end
%
%   PROBLEM: When stepsize (s) < binsize (b), bins OVERLAP, causing
%   each event to be counted multiple times. This inflates turn rates
%   to hundreds per minute instead of realistic values.
%
%   [rate, time_bins, counts] = rate_from_time_corrected(event_times, total_duration, bin_size, normalize_by_time)
%
%   This is a CORRECTED version of rate_from_time.m that avoids the
%   oversampling issue in the original (which used overlapping bins).
%
%   CORRECTION:
%   This version uses NON-OVERLAPPING bins of size bin_size.
%   Rate = counts / (bin_size * n_observations)  or
%   Rate = counts / bin_size  (if normalize_by_time = false)
%
%   Inputs:
%       event_times      - Array of event times (seconds)
%       total_duration   - Total observation duration (seconds)
%       bin_size         - Size of each time bin (seconds)
%       normalize_by_time - If true, rate is per second; if false, raw count
%                          Default: true
%
%   Outputs:
%       rate      - Event rate per bin (events/second if normalized)
%       time_bins - Center of each time bin
%       counts    - Raw event count per bin
%
%   Example:
%       event_times = [1.5, 3.2, 3.8, 7.1];
%       [rate, bins, counts] = rate_from_time_corrected(event_times, 10, 2);
%       % bins = [1, 3, 5, 7, 9]
%       % counts = [1, 2, 0, 1, 0] (events in each 2-second bin)
%       % rate = counts / 2 = [0.5, 1, 0, 0.5, 0] events/second
%
%   Reference: Corrected version for Mason Klein analysis
%   Python equivalent: engineer_data.rate_from_time_corrected()

if nargin < 4
    normalize_by_time = true;
end

% Ensure row vector
event_times = event_times(:)';

% Create non-overlapping bins
bin_edges = 0:bin_size:total_duration;
n_bins = length(bin_edges) - 1;

if n_bins < 1
    rate = [];
    time_bins = [];
    counts = [];
    return;
end

% Compute bin centers
time_bins = bin_edges(1:end-1) + bin_size/2;

% Count events in each bin
counts = histcounts(event_times, bin_edges);

% Compute rate
if normalize_by_time
    rate = counts / bin_size;  % events per second
else
    rate = counts;  % raw counts
end

end

%% Comparison with original rate_from_time
function compare_with_original()
    % Demonstrate the difference between original and corrected versions
    
    % Generate sample event times (10 events in 15 second period)
    event_times = [1.2, 2.5, 4.1, 5.8, 7.3, 8.9, 10.2, 11.5, 13.1, 14.2];
    T = 15;  % period
    
    % Original parameters (from load_multi_data_gr21a.m)
    stepsize = 0.1;
    binsize = 0.5;
    
    % Compute using original method (emulated)
    m = fix(T/stepsize);
    r_original = zeros(1, m + 1);
    for j = 0:m
        tleft = mod(j*stepsize - binsize, T);
        tright = mod(j*stepsize, T);
        if tleft > tright
            r_original(j+1) = nnz(event_times >= tleft | event_times < tright) / binsize;
        else
            r_original(j+1) = nnz(event_times >= tleft & event_times < tright) / binsize;
        end
    end
    
    % Compute using corrected method
    [r_corrected, time_bins, counts] = rate_from_time_corrected(event_times, T, 1.0);
    
    % Display comparison
    fprintf('\n=== RATE COMPARISON ===\n');
    fprintf('Event times: %s\n', mat2str(event_times));
    fprintf('Total events: %d\n\n', length(event_times));
    
    fprintf('ORIGINAL METHOD (stepsize=%.1f, binsize=%.1f):\n', stepsize, binsize);
    fprintf('  Mean rate: %.2f events/second\n', mean(r_original));
    fprintf('  Max rate: %.2f events/second\n', max(r_original));
    fprintf('  Sum (with overlap): %.2f\n\n', sum(r_original) * stepsize);
    
    fprintf('CORRECTED METHOD (bin_size=1.0):\n');
    fprintf('  Mean rate: %.2f events/second\n', mean(r_corrected));
    fprintf('  Max rate: %.2f events/second\n', max(r_corrected));
    fprintf('  Total events verified: %d\n\n', sum(counts));
    
    fprintf('EXPECTED:\n');
    fprintf('  Mean rate should be ~%.2f events/second\n', length(event_times)/T);
end

%% Test Harness
function test_rate_from_time_corrected()
    % Test case 1: Uniform events
    event_times = [0.5, 1.5, 2.5, 3.5, 4.5];  % 5 events, 1 per second
    [rate, bins, counts] = rate_from_time_corrected(event_times, 5, 1.0);
    
    assert(length(counts) == 5, 'Test 1 failed: should have 5 bins');
    assert(all(counts == 1), 'Test 1 failed: each bin should have 1 event');
    assert(all(abs(rate - 1.0) < 1e-10), 'Test 1 failed: rate should be 1.0');
    fprintf('Test 1 passed: uniform events\n');
    
    % Test case 2: Clustered events
    event_times = [1.1, 1.2, 1.3, 1.4];  % 4 events all in second bin
    [rate, bins, counts] = rate_from_time_corrected(event_times, 5, 1.0);
    
    assert(counts(1) == 0, 'Test 2 failed: first bin should be empty');
    assert(counts(2) == 4, 'Test 2 failed: second bin should have 4 events');
    fprintf('Test 2 passed: clustered events\n');
    
    % Test case 3: No events
    event_times = [];
    [rate, bins, counts] = rate_from_time_corrected(event_times, 5, 1.0);
    
    assert(all(counts == 0), 'Test 3 failed: all counts should be 0');
    assert(all(rate == 0), 'Test 3 failed: all rates should be 0');
    fprintf('Test 3 passed: no events\n');
    
    % Test case 4: Verify no double counting
    event_times = [2.5];  % Single event at t=2.5
    [rate, bins, counts] = rate_from_time_corrected(event_times, 5, 1.0);
    
    assert(sum(counts) == 1, 'Test 4 failed: event should be counted exactly once');
    assert(counts(3) == 1, 'Test 4 failed: event should be in bin 3 (2-3s)');
    fprintf('Test 4 passed: no double counting\n');
    
    % Test case 5: Different bin sizes
    event_times = [0.5, 1.5, 2.5, 3.5];
    [rate, bins, counts] = rate_from_time_corrected(event_times, 4, 2.0);
    
    assert(length(counts) == 2, 'Test 5 failed: should have 2 bins');
    assert(all(counts == 2), 'Test 5 failed: each 2s bin should have 2 events');
    fprintf('Test 5 passed: different bin sizes\n');
    
    fprintf('\nAll tests passed for rate_from_time_corrected!\n');
end

