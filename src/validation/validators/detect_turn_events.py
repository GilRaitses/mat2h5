"""
detect_turn_events.py - Detect turn/reorientation events from heading angle changes

ORIGINAL MASON SCRIPT: Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m
Location: scripts/2025-11-20/mason's scritps/

Original turn detection (from Mason's script):
    theta = acos(CosThetaFactor);
    TurnFactor1 = pi/4;   % 45 degrees
    TurnFactor2 = 3*pi/4; % 135 degrees
    % Turn detected when: TurnFactor1 < abs(theta) < TurnFactor2

Note: Mason's scripts detect TURN EVENTS (binary), not turn RATE.
Turn rate computation is in separate scripts (binReorientationTimesWithCycles.m).

A turn is detected when the cumulative heading angle change exceeds
the threshold within a sliding window.

Documentation: scripts/2025-11-24/mason_script_4_behavior_analysis.qmd
MATLAB equivalent: src/validation/reference/detect_turn_events.m
"""

import numpy as np
from typing import List
from dataclasses import dataclass


@dataclass
class TurnEvent:
    """Represents a turn/reorientation event."""
    idx: int
    time: float
    angle_change: float  # in degrees
    direction: str  # 'left' or 'right'
    
    def to_dict(self) -> dict:
        return {
            'idx': self.idx,
            'time': self.time,
            'angle_change': self.angle_change,
            'direction': self.direction
        }


def detect_turn_events(
    times: np.ndarray,
    head_unit_vec: np.ndarray,
    angle_threshold: float = 45.0,
    min_frames: int = 3
) -> List[TurnEvent]:
    """
    Detect turn/reorientation events from heading angle changes.
    
    A turn is detected when the cumulative heading angle change
    exceeds the threshold within a window.
    
    Args:
        times: Time array
        head_unit_vec: Normalized heading vectors (2, N)
        angle_threshold: Minimum angle change (degrees)
        min_frames: Minimum frames between detected turns
    
    Returns:
        List of TurnEvent objects
    """
    times = np.asarray(times).ravel()
    
    if head_unit_vec.shape[0] != 2:
        head_unit_vec = head_unit_vec.T
    
    if head_unit_vec.shape[1] < min_frames:
        return []
    
    # Compute heading angles (radians)
    angles = np.arctan2(head_unit_vec[1, :], head_unit_vec[0, :])
    
    # Unwrap angles to handle -pi to pi discontinuity
    angles_unwrapped = np.unwrap(angles)
    
    # Compute angle changes (radians to degrees)
    angle_diff = np.diff(angles_unwrapped)
    angle_diff_deg = np.rad2deg(angle_diff)
    
    turn_events = []
    i = 0
    max_window = 30  # Maximum frames to look ahead
    
    while i < len(angle_diff) - min_frames:
        # Look for cumulative angle change exceeding threshold
        cumsum_angle = 0.0
        found = False
        
        for j in range(i, min(i + max_window, len(angle_diff))):
            cumsum_angle += angle_diff_deg[j]
            
            if abs(cumsum_angle) >= angle_threshold:
                direction = 'left' if cumsum_angle > 0 else 'right'
                turn_events.append(TurnEvent(
                    idx=i,
                    time=times[i],
                    angle_change=abs(cumsum_angle),
                    direction=direction
                ))
                i = j + min_frames  # Skip ahead to avoid double-counting
                found = True
                break
        
        if not found:
            i += 1
    
    return turn_events


def test_detect_turn_events():
    """Run unit tests for detect_turn_events."""
    
    # Test case 1: No turns (constant heading)
    times = np.arange(0, 10.1, 0.1)
    N = len(times)
    head_unit_vec = np.vstack([np.ones(N), np.zeros(N)])  # Always pointing right
    
    turn_events = detect_turn_events(times, head_unit_vec, 45.0)
    
    assert len(turn_events) == 0, 'Test 1 failed: should have no turns'
    print('Test 1 passed: no turns (constant heading)')
    
    # Test case 2: Single 90 degree left turn
    times = np.arange(0, 5.1, 0.1)
    N = len(times)
    head_unit_vec = np.zeros((2, N))
    
    # First half: pointing right [1, 0]
    head_unit_vec[0, :25] = 1
    head_unit_vec[1, :25] = 0
    
    # Second half: pointing up [0, 1] (90 degree left turn)
    head_unit_vec[0, 25:] = 0
    head_unit_vec[1, 25:] = 1
    
    turn_events = detect_turn_events(times, head_unit_vec, 45.0)
    
    assert len(turn_events) >= 1, 'Test 2 failed: should detect turn'
    assert turn_events[0].direction == 'left', 'Test 2 failed: should be left turn'
    print('Test 2 passed: single left turn')
    
    # Test case 3: Single 90 degree right turn
    times = np.arange(0, 5.1, 0.1)
    N = len(times)
    head_unit_vec = np.zeros((2, N))
    
    # First half: pointing right [1, 0]
    head_unit_vec[0, :25] = 1
    head_unit_vec[1, :25] = 0
    
    # Second half: pointing down [0, -1] (90 degree right turn)
    head_unit_vec[0, 25:] = 0
    head_unit_vec[1, 25:] = -1
    
    turn_events = detect_turn_events(times, head_unit_vec, 45.0)
    
    assert len(turn_events) >= 1, 'Test 3 failed: should detect turn'
    assert turn_events[0].direction == 'right', 'Test 3 failed: should be right turn'
    print('Test 3 passed: single right turn')
    
    # Test case 4: Small turn below threshold
    times = np.arange(0, 5.1, 0.1)
    N = len(times)
    angles = np.linspace(0, np.deg2rad(30), N)  # Only 30 degree turn
    head_unit_vec = np.vstack([np.cos(angles), np.sin(angles)])
    
    turn_events = detect_turn_events(times, head_unit_vec, 45.0)
    
    assert len(turn_events) == 0, 'Test 4 failed: small turn should be ignored'
    print('Test 4 passed: small turn below threshold')
    
    print('\nAll tests passed for detect_turn_events!')


if __name__ == '__main__':
    test_detect_turn_events()

