"""
compute_speedrunvel.py - Compute signed velocity using dot product method

ORIGINAL MASON SCRIPT: Just_ReverseCrawl_Matlab.m
Location: scripts/2025-11-20/mason's scritps/

Original core computation:
    HeadVec = shead - smid;
    HeadUnitVec = HeadVec / norm(HeadVec);
    VelocityVec = [dx/distance; dy/distance];
    speed = distance / dt;
    CosThetaFactor = dot(VelocityVec, HeadUnitVec);
    SpeedRunVel = speed * CosThetaFactor;

KEY OUTPUT: SpeedRunVel is the central variable for reverse crawl detection
- SpeedRunVel > 0 means forward crawling
- SpeedRunVel < 0 means REVERSE CRAWL (backing up)

Mathematical Definition:
    HeadUnitVec = normalized(shead - smid)
    VelocityVec = normalized displacement
    SpeedRun = ||displacement|| / dt
    CosThetaFactor = VelocityVec . HeadUnitVec
    SpeedRunVel = SpeedRun * CosThetaFactor

Interpretation:
    SpeedRunVel > 0  ->  Forward movement (velocity aligned with head)
    SpeedRunVel < 0  ->  Reverse crawl (velocity opposite to head)
    SpeedRunVel = 0  ->  Stationary or perpendicular movement

Documentation: scripts/2025-11-24/mason_scripts_documentation.qmd (Section 3)
MATLAB equivalent: src/validation/reference/compute_speedrunvel.m
"""

import numpy as np
from typing import Tuple
from compute_heading_unit_vector import compute_heading_unit_vector
from compute_velocity_and_speed import compute_velocity_and_speed


def compute_speedrunvel(
    shead: np.ndarray,
    smid: np.ndarray,
    xpos: np.ndarray,
    ypos: np.ndarray,
    times: np.ndarray,
    length_per_pixel: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute SpeedRunVel (signed velocity indicating forward/reverse motion).
    
    SpeedRunVel = SpeedRun * CosThetaFactor
    
    where:
        CosThetaFactor = VelocityVec . HeadUnitVec
    
    Args:
        shead: Head positions, shape (2, N) or (N, 2)
        smid: Midpoint positions, shape (2, N) or (N, 2)
        xpos: X positions in pixels (N,)
        ypos: Y positions in pixels (N,)
        times: Time values (N,)
        length_per_pixel: Conversion factor (cm/pixel)
    
    Returns:
        speedrunvel: Signed velocity array (N-1,)
        times_out: Time values for speedrunvel (N-1,)
    """
    # Ensure 1D arrays
    xpos = np.asarray(xpos).ravel()
    ypos = np.asarray(ypos).ravel()
    times = np.asarray(times).ravel()
    
    # Convert positions to cm
    xpos_cm = xpos * length_per_pixel
    ypos_cm = ypos * length_per_pixel
    
    # Compute heading unit vectors
    head_unit_vec = compute_heading_unit_vector(shead, smid)
    
    # Compute velocity vectors and speed
    velocity_vec, speed = compute_velocity_and_speed(xpos_cm, ypos_cm, times)
    
    N = len(times) - 1
    
    # Compute dot product (CosThetaFactor)
    # Use head_unit_vec at each frame (truncate to match velocity length)
    cos_theta = np.sum(velocity_vec * head_unit_vec[:, :N], axis=0)
    
    # SpeedRunVel = speed * cos(theta)
    speedrunvel = speed * cos_theta
    
    # Times correspond to the first point of each interval
    times_out = times[:-1]
    
    return speedrunvel, times_out


def test_compute_speedrunvel():
    """Run unit tests for compute_speedrunvel."""
    
    length_per_pixel = 1.0
    
    # Test case 1: Forward movement (heading and velocity aligned)
    shead = np.array([[2, 3, 4], [0, 0, 0]])
    smid = np.array([[1, 2, 3], [0, 0, 0]])
    xpos = np.array([0, 1, 2])
    ypos = np.array([0, 0, 0])
    times = np.array([0, 1, 2])
    
    speedrunvel, _ = compute_speedrunvel(shead, smid, xpos, ypos, times, length_per_pixel)
    
    assert np.all(speedrunvel > 0), 'Test 1 failed: forward movement should have positive SpeedRunVel'
    assert np.max(np.abs(speedrunvel - 1)) < 1e-10, 'Test 1 failed: SpeedRunVel should be 1'
    print('Test 1 passed: forward movement')
    
    # Test case 2: Reverse crawl (heading opposite to velocity)
    shead = np.array([[2, 3, 4], [0, 0, 0]])
    smid = np.array([[1, 2, 3], [0, 0, 0]])
    xpos = np.array([2, 1, 0])  # Moving LEFT (reverse)
    ypos = np.array([0, 0, 0])
    times = np.array([0, 1, 2])
    
    speedrunvel, _ = compute_speedrunvel(shead, smid, xpos, ypos, times, length_per_pixel)
    
    assert np.all(speedrunvel < 0), 'Test 2 failed: reverse movement should have negative SpeedRunVel'
    assert np.max(np.abs(speedrunvel - (-1))) < 1e-10, 'Test 2 failed: SpeedRunVel should be -1'
    print('Test 2 passed: reverse crawl')
    
    # Test case 3: Perpendicular movement (90 degrees)
    shead = np.array([[2, 3, 4], [0, 0, 0]])  # Head pointing +x
    smid = np.array([[1, 2, 3], [0, 0, 0]])
    xpos = np.array([0, 0, 0])  # Not moving in x
    ypos = np.array([0, 1, 2])  # Moving up
    times = np.array([0, 1, 2])
    
    speedrunvel, _ = compute_speedrunvel(shead, smid, xpos, ypos, times, length_per_pixel)
    
    assert np.max(np.abs(speedrunvel)) < 1e-10, 'Test 3 failed: perpendicular should have zero SpeedRunVel'
    print('Test 3 passed: perpendicular movement')
    
    # Test case 4: 45 degree angle
    shead = np.array([[1, 2, 3], [0, 0, 0]])  # Head pointing +x
    smid = np.array([[0, 1, 2], [0, 0, 0]])
    xpos = np.array([0, 1, 2])  # Moving diagonally
    ypos = np.array([0, 1, 2])
    times = np.array([0, 1, 2])
    
    speedrunvel, _ = compute_speedrunvel(shead, smid, xpos, ypos, times, length_per_pixel)
    
    expected = np.sqrt(2) * (1/np.sqrt(2))  # = 1
    assert np.max(np.abs(speedrunvel - expected)) < 1e-10, 'Test 4 failed: 45 degree angle'
    print('Test 4 passed: 45 degree angle')
    
    print('\nAll tests passed for compute_speedrunvel!')


if __name__ == '__main__':
    test_compute_speedrunvel()

