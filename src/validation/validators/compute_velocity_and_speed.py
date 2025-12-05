"""
compute_velocity_and_speed.py - Compute velocity unit vectors and speed

ORIGINAL MASON SCRIPT: Just_ReverseCrawl_Matlab.m
Location: scripts/2025-11-20/mason's scritps/

Original code (lines ~30-45):
    for o = 1:(length(times)-1)
        dx = xpos(o+1) - xpos(o);
        dy = ypos(o+1) - ypos(o);
        distance = sqrt(dx^2 + dy^2);
        dt = times(o+1) - times(o);
        if distance > 0 && dt > 0
            VelocityVecx = dx / distance;
            VelocityVecy = dy / distance;
            speed = distance / dt;
        end
    end

Mathematical Definition:
    dx = xpos(i+1) - xpos(i)
    dy = ypos(i+1) - ypos(i)
    dt = times(i+1) - times(i)
    distance = sqrt(dx^2 + dy^2)
    VelocityVec = [dx/distance; dy/distance]  (normalized)
    speed = distance / dt

Documentation: scripts/2025-11-24/mason_script_3_reverse_crawl.qmd
MATLAB equivalent: src/validation/reference/compute_velocity_and_speed.m
"""

import numpy as np
from typing import Tuple


def compute_velocity_and_speed(
    xpos: np.ndarray, 
    ypos: np.ndarray, 
    times: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute velocity unit vectors and speed from position time series.
    
    VelocityVec = [dx, dy] / ||[dx, dy]||
    SpeedRun = ||[dx, dy]|| / dt
    
    Args:
        xpos: X positions (N,)
        ypos: Y positions (N,)
        times: Time values (N,)
    
    Returns:
        velocity_vec: Normalized velocity vectors, shape (2, N-1)
        speed: Speed values, shape (N-1,)
    """
    # Ensure 1D arrays
    xpos = np.asarray(xpos).ravel()
    ypos = np.asarray(ypos).ravel()
    times = np.asarray(times).ravel()
    
    # Compute displacements
    dx = np.diff(xpos)
    dy = np.diff(ypos)
    dt = np.diff(times)
    
    # Compute distance
    distance = np.sqrt(dx**2 + dy**2)
    
    # Compute speed (distance / time)
    speed = np.zeros_like(distance)
    valid = dt > 0
    speed[valid] = distance[valid] / dt[valid]
    
    # Normalize velocity vectors
    velocity_vec = np.zeros((2, len(dx)))
    valid_dist = distance > 0
    velocity_vec[0, valid_dist] = dx[valid_dist] / distance[valid_dist]
    velocity_vec[1, valid_dist] = dy[valid_dist] / distance[valid_dist]
    
    return velocity_vec, speed


def test_compute_velocity_and_speed():
    """Run unit tests for compute_velocity_and_speed."""
    
    # Test case 1: Constant velocity along x-axis
    xpos = np.array([0, 1, 2, 3, 4])
    ypos = np.array([0, 0, 0, 0, 0])
    times = np.array([0, 1, 2, 3, 4])
    
    velocity_vec, speed = compute_velocity_and_speed(xpos, ypos, times)
    
    expected_vel = np.array([[1, 1, 1, 1], [0, 0, 0, 0]])
    expected_speed = np.array([1, 1, 1, 1])
    
    assert np.max(np.abs(velocity_vec - expected_vel)) < 1e-10, 'Test 1 failed: velocity'
    assert np.max(np.abs(speed - expected_speed)) < 1e-10, 'Test 1 failed: speed'
    print('Test 1 passed: constant x-velocity')
    
    # Test case 2: Diagonal movement
    xpos = np.array([0, 1, 2, 3])
    ypos = np.array([0, 1, 2, 3])
    times = np.array([0, 1, 2, 3])
    
    velocity_vec, speed = compute_velocity_and_speed(xpos, ypos, times)
    
    expected_vel = np.array([[1/np.sqrt(2), 1/np.sqrt(2), 1/np.sqrt(2)],
                             [1/np.sqrt(2), 1/np.sqrt(2), 1/np.sqrt(2)]])
    expected_speed = np.array([np.sqrt(2), np.sqrt(2), np.sqrt(2)])
    
    assert np.max(np.abs(velocity_vec - expected_vel)) < 1e-10, 'Test 2 failed: velocity'
    assert np.max(np.abs(speed - expected_speed)) < 1e-10, 'Test 2 failed: speed'
    print('Test 2 passed: diagonal movement')
    
    # Test case 3: Zero displacement (stationary)
    xpos = np.array([1, 1, 1])
    ypos = np.array([2, 2, 2])
    times = np.array([0, 1, 2])
    
    velocity_vec, speed = compute_velocity_and_speed(xpos, ypos, times)
    
    expected_vel = np.array([[0, 0], [0, 0]])
    expected_speed = np.array([0, 0])
    
    assert np.max(np.abs(velocity_vec - expected_vel)) < 1e-10, 'Test 3 failed: velocity'
    assert np.max(np.abs(speed - expected_speed)) < 1e-10, 'Test 3 failed: speed'
    print('Test 3 passed: stationary')
    
    # Test case 4: Variable time steps
    xpos = np.array([0, 2, 6])
    ypos = np.array([0, 0, 0])
    times = np.array([0, 1, 3])  # dt = [1, 2]
    
    velocity_vec, speed = compute_velocity_and_speed(xpos, ypos, times)
    
    expected_vel = np.array([[1, 1], [0, 0]])
    expected_speed = np.array([2, 2])  # distance/dt = [2/1, 4/2]
    
    assert np.max(np.abs(velocity_vec - expected_vel)) < 1e-10, 'Test 4 failed: velocity'
    assert np.max(np.abs(speed - expected_speed)) < 1e-10, 'Test 4 failed: speed'
    print('Test 4 passed: variable time steps')
    
    print('\nAll tests passed for compute_velocity_and_speed!')


if __name__ == '__main__':
    test_compute_velocity_and_speed()

