"""
rate_from_time_corrected.py - Compute event rate using non-overlapping bins

ORIGINAL SCRIPT: rate_from_time.m
Location: Matlab-Track-Analysis-MirnaLab/user specific/yiming/rate_from_time.m
Also used in: load_multi_data_gr21a.m (line 325)

Original code:
    function r = rate_from_time(t, T, s, b)
    m = fix(T/s);
    r = zeros(1, m + 1);
    for j = 0 : m
        tleft = mod(j*s-b, T);  % periodic boundary condition
        tright = mod(j*s, T);
        if tleft>tright
            r(j+1) = nnz(t >= tleft | t < tright ) / b;
        else
            r(j+1) = nnz(t >= tleft & t < tright ) / b;
        end
    end

PROBLEM: When stepsize (s) < binsize (b), bins OVERLAP, causing
each event to be counted multiple times. This inflates turn rates
to hundreds per minute instead of realistic values.

This is a CORRECTED version that uses NON-OVERLAPPING bins of size bin_size.
Rate = counts / bin_size (events per second)

MATLAB equivalent: src/validation/reference/rate_from_time_corrected.m
"""

import numpy as np
from typing import Tuple


def rate_from_time_corrected(
    event_times: np.ndarray,
    total_duration: float,
    bin_size: float,
    normalize_by_time: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute event rate using non-overlapping bins.
    
    Args:
        event_times: Array of event times (seconds)
        total_duration: Total observation duration (seconds)
        bin_size: Size of each time bin (seconds)
        normalize_by_time: If True, rate is per second; if False, raw count
    
    Returns:
        rate: Event rate per bin (events/second if normalized)
        time_bins: Center of each time bin
        counts: Raw event count per bin
    
    Example:
        event_times = [1.5, 3.2, 3.8, 7.1]
        rate, bins, counts = rate_from_time_corrected(event_times, 10, 2)
        # bins = [1, 3, 5, 7, 9]
        # counts = [1, 2, 0, 1, 0] (events in each 2-second bin)
        # rate = counts / 2 = [0.5, 1, 0, 0.5, 0] events/second
    """
    event_times = np.asarray(event_times).ravel()
    
    # Create non-overlapping bins
    bin_edges = np.arange(0, total_duration + bin_size, bin_size)
    n_bins = len(bin_edges) - 1
    
    if n_bins < 1:
        return np.array([]), np.array([]), np.array([])
    
    # Compute bin centers
    time_bins = bin_edges[:-1] + bin_size / 2
    
    # Count events in each bin
    counts, _ = np.histogram(event_times, bins=bin_edges)
    
    # Compute rate
    if normalize_by_time:
        rate = counts / bin_size  # events per second
    else:
        rate = counts.astype(float)  # raw counts
    
    return rate, time_bins, counts


def compare_with_original():
    """
    Demonstrate the difference between original and corrected versions.
    """
    # Generate sample event times (10 events in 15 second period)
    event_times = np.array([1.2, 2.5, 4.1, 5.8, 7.3, 8.9, 10.2, 11.5, 13.1, 14.2])
    T = 15  # period
    
    # Original parameters (from load_multi_data_gr21a.m)
    stepsize = 0.1
    binsize = 0.5
    
    # Compute using original method (emulated)
    m = int(T / stepsize)
    r_original = np.zeros(m + 1)
    for j in range(m + 1):
        tleft = (j * stepsize - binsize) % T
        tright = (j * stepsize) % T
        if tleft > tright:
            r_original[j] = np.sum((event_times >= tleft) | (event_times < tright)) / binsize
        else:
            r_original[j] = np.sum((event_times >= tleft) & (event_times < tright)) / binsize
    
    # Compute using corrected method
    r_corrected, time_bins, counts = rate_from_time_corrected(event_times, T, 1.0)
    
    # Display comparison
    print('\n=== RATE COMPARISON ===')
    print(f'Event times: {event_times}')
    print(f'Total events: {len(event_times)}\n')
    
    print(f'ORIGINAL METHOD (stepsize={stepsize}, binsize={binsize}):')
    print(f'  Mean rate: {np.mean(r_original):.2f} events/second')
    print(f'  Max rate: {np.max(r_original):.2f} events/second')
    print(f'  Sum (with overlap): {np.sum(r_original) * stepsize:.2f}\n')
    
    print('CORRECTED METHOD (bin_size=1.0):')
    print(f'  Mean rate: {np.mean(r_corrected):.2f} events/second')
    print(f'  Max rate: {np.max(r_corrected):.2f} events/second')
    print(f'  Total events verified: {np.sum(counts)}\n')
    
    print('EXPECTED:')
    print(f'  Mean rate should be ~{len(event_times)/T:.2f} events/second')


def test_rate_from_time_corrected():
    """Run unit tests for rate_from_time_corrected."""
    
    # Test case 1: Uniform events
    event_times = np.array([0.5, 1.5, 2.5, 3.5, 4.5])  # 5 events, 1 per second
    rate, bins, counts = rate_from_time_corrected(event_times, 5, 1.0)
    
    assert len(counts) == 5, 'Test 1 failed: should have 5 bins'
    assert np.all(counts == 1), 'Test 1 failed: each bin should have 1 event'
    assert np.all(np.abs(rate - 1.0) < 1e-10), 'Test 1 failed: rate should be 1.0'
    print('Test 1 passed: uniform events')
    
    # Test case 2: Clustered events
    event_times = np.array([1.1, 1.2, 1.3, 1.4])  # 4 events all in second bin
    rate, bins, counts = rate_from_time_corrected(event_times, 5, 1.0)
    
    assert counts[0] == 0, 'Test 2 failed: first bin should be empty'
    assert counts[1] == 4, 'Test 2 failed: second bin should have 4 events'
    print('Test 2 passed: clustered events')
    
    # Test case 3: No events
    event_times = np.array([])
    rate, bins, counts = rate_from_time_corrected(event_times, 5, 1.0)
    
    assert np.all(counts == 0), 'Test 3 failed: all counts should be 0'
    assert np.all(rate == 0), 'Test 3 failed: all rates should be 0'
    print('Test 3 passed: no events')
    
    # Test case 4: Verify no double counting
    event_times = np.array([2.5])  # Single event at t=2.5
    rate, bins, counts = rate_from_time_corrected(event_times, 5, 1.0)
    
    assert np.sum(counts) == 1, 'Test 4 failed: event should be counted exactly once'
    assert counts[2] == 1, 'Test 4 failed: event should be in bin 3 (2-3s)'
    print('Test 4 passed: no double counting')
    
    # Test case 5: Different bin sizes
    event_times = np.array([0.5, 1.5, 2.5, 3.5])
    rate, bins, counts = rate_from_time_corrected(event_times, 4, 2.0)
    
    assert len(counts) == 2, 'Test 5 failed: should have 2 bins'
    assert np.all(counts == 2), 'Test 5 failed: each 2s bin should have 2 events'
    print('Test 5 passed: different bin sizes')
    
    print('\nAll tests passed for rate_from_time_corrected!')


if __name__ == '__main__':
    test_rate_from_time_corrected()
    print()
    compare_with_original()

