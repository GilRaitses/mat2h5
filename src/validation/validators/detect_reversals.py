"""
detect_reversals.py - Detect reverse crawl events from SpeedRunVel

ORIGINAL MASON SCRIPT: Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m
Location: scripts/2025-11-20/mason's scritps/

Original detection logic:
    % A reversal is when the larva moves backward (SpeedRunVel < 0)
    % The duration threshold filters out brief noise/wobbles
    reversal_mask = SpeedRunVel < 0;
    % Find contiguous negative regions >= min_duration

The 3-second minimum duration is based on Mason's observation that
shorter negative SpeedRunVel periods are typically noise or brief
hesitations, not true reverse crawling behavior.

A reversal is defined as a continuous period where SpeedRunVel < 0
lasting at least min_duration seconds.

Documentation: scripts/2025-11-24/mason_script_4_behavior_analysis.qmd
MATLAB equivalent: src/validation/reference/detect_reversals.m
"""

import numpy as np
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Reversal:
    """Represents a single reverse crawl event."""
    start_idx: int
    end_idx: int
    start_time: float
    end_time: float
    duration: float
    mean_speed: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'start_idx': self.start_idx,
            'end_idx': self.end_idx,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'mean_speed': self.mean_speed
        }


def detect_reversals(
    times: np.ndarray,
    speedrunvel: np.ndarray,
    min_duration: float = 3.0
) -> List[Reversal]:
    """
    Detect reverse crawl events from SpeedRunVel time series.
    
    A reversal is defined as a continuous period where SpeedRunVel < 0
    lasting at least min_duration seconds.
    
    Args:
        times: Time array
        speedrunvel: Signed velocity array
        min_duration: Minimum duration for reversal (seconds)
    
    Returns:
        List of Reversal objects
    """
    times = np.asarray(times).ravel()
    speedrunvel = np.asarray(speedrunvel).ravel()
    
    if len(times) == 0 or len(speedrunvel) == 0:
        return []
    
    reversals = []
    in_reversal = False
    start_idx = None
    start_time = None
    
    for i in range(len(speedrunvel)):
        is_negative = speedrunvel[i] < 0
        
        if is_negative and not in_reversal:
            # Start of reversal
            in_reversal = True
            start_idx = i
            start_time = times[i]
        
        elif not is_negative and in_reversal:
            # End of reversal
            in_reversal = False
            if start_idx is not None:
                duration = times[i] - start_time
                if duration >= min_duration:
                    mean_speed = np.abs(np.mean(speedrunvel[start_idx:i]))
                    reversals.append(Reversal(
                        start_idx=start_idx,
                        end_idx=i - 1,
                        start_time=start_time,
                        end_time=times[i - 1],
                        duration=duration,
                        mean_speed=mean_speed
                    ))
            start_idx = None
    
    # Handle reversal extending to end of data
    if in_reversal and start_idx is not None:
        duration = times[-1] - start_time
        if duration >= min_duration:
            mean_speed = np.abs(np.mean(speedrunvel[start_idx:]))
            reversals.append(Reversal(
                start_idx=start_idx,
                end_idx=len(speedrunvel) - 1,
                start_time=start_time,
                end_time=times[-1],
                duration=duration,
                mean_speed=mean_speed
            ))
    
    return reversals


def test_detect_reversals():
    """Run unit tests for detect_reversals."""
    
    # Test case 1: No reversals (all positive)
    times = np.arange(0, 10.1, 0.1)
    speedrunvel = np.ones(len(times))
    
    reversals = detect_reversals(times, speedrunvel, 3.0)
    
    assert len(reversals) == 0, 'Test 1 failed: should have no reversals'
    print('Test 1 passed: no reversals (all positive)')
    
    # Test case 2: Single long reversal
    times = np.arange(0, 10.1, 0.1)
    speedrunvel = np.ones(len(times))
    speedrunvel[20:71] = -1  # Negative from t=2 to t=7 (5 seconds)
    
    reversals = detect_reversals(times, speedrunvel, 3.0)
    
    assert len(reversals) == 1, 'Test 2 failed: should have 1 reversal'
    assert abs(reversals[0].duration - 5.0) < 0.2, 'Test 2 failed: duration should be ~5s'
    print('Test 2 passed: single long reversal')
    
    # Test case 3: Short reversal (below threshold)
    times = np.arange(0, 10.1, 0.1)
    speedrunvel = np.ones(len(times))
    speedrunvel[20:31] = -1  # Negative from t=2 to t=3 (1 second, below threshold)
    
    reversals = detect_reversals(times, speedrunvel, 3.0)
    
    assert len(reversals) == 0, 'Test 3 failed: short reversal should be ignored'
    print('Test 3 passed: short reversal ignored')
    
    # Test case 4: Multiple reversals
    times = np.arange(0, 20.1, 0.1)
    speedrunvel = np.ones(len(times))
    speedrunvel[10:51] = -1   # Reversal 1: t=1 to t=5 (4 seconds)
    speedrunvel[100:151] = -1 # Reversal 2: t=10 to t=15 (5 seconds)
    
    reversals = detect_reversals(times, speedrunvel, 3.0)
    
    assert len(reversals) == 2, 'Test 4 failed: should have 2 reversals'
    print('Test 4 passed: multiple reversals')
    
    # Test case 5: Reversal at end of data
    times = np.arange(0, 10.1, 0.1)
    speedrunvel = np.ones(len(times))
    speedrunvel[60:] = -1  # Negative from t=6 to end (4 seconds)
    
    reversals = detect_reversals(times, speedrunvel, 3.0)
    
    assert len(reversals) == 1, 'Test 5 failed: should detect reversal at end'
    print('Test 5 passed: reversal at end of data')
    
    print('\nAll tests passed for detect_reversals!')


if __name__ == '__main__':
    test_detect_reversals()

