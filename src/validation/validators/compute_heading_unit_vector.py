"""
compute_heading_unit_vector.py - Compute normalized heading vector

ORIGINAL MASON SCRIPT: Just_ReverseCrawl_Matlab.m
Location: scripts/2025-11-20/mason's scritps/

Original code (lines ~15-25):
    HeadVec = shead - smid;
    for k = 1:(size(HeadVec,2)-1)
        norm_val = sqrt(HeadVec(1,k)^2 + HeadVec(2,k)^2);
        if norm_val > 0
            HeadUnitVec(:,k) = HeadVec(:,k) / norm_val;
        end
    end

Mathematical Definition:
    HeadVec = shead - smid
    HeadUnitVec = HeadVec / ||HeadVec||

Documentation: scripts/2025-11-24/mason_script_3_reverse_crawl.qmd
MATLAB equivalent: src/validation/reference/compute_heading_unit_vector.m
"""

import numpy as np
from typing import Tuple


def compute_heading_unit_vector(shead: np.ndarray, smid: np.ndarray) -> np.ndarray:
    """
    Compute normalized heading unit vector from head and midpoint positions.
    
    HeadVec = shead - smid
    HeadUnitVec = HeadVec / ||HeadVec||
    
    Args:
        shead: Head positions, shape (2, N) or (N, 2)
        smid: Midpoint positions, shape (2, N) or (N, 2)
    
    Returns:
        HeadUnitVec: Normalized heading vectors, shape (2, N)
    """
    # Ensure shape is (2, N)
    if shead.shape[0] != 2:
        shead = shead.T
    if smid.shape[0] != 2:
        smid = smid.T
    
    # HeadVec = shead - smid
    head_vec = shead - smid
    
    # Compute norm for each time point
    norms = np.sqrt(head_vec[0, :]**2 + head_vec[1, :]**2)
    
    # Avoid division by zero
    norms[norms == 0] = 1.0
    
    # Normalize: HeadUnitVec = HeadVec / ||HeadVec||
    head_unit_vec = head_vec / norms
    
    return head_unit_vec


def test_compute_heading_unit_vector():
    """Run unit tests for compute_heading_unit_vector."""
    
    # Test case 1: Simple diagonal heading
    shead = np.array([[1, 2, 3], [1, 2, 3]])
    smid = np.array([[0, 1, 2], [0, 1, 2]])
    result = compute_heading_unit_vector(shead, smid)
    
    expected = np.array([[1/np.sqrt(2), 1/np.sqrt(2), 1/np.sqrt(2)],
                         [1/np.sqrt(2), 1/np.sqrt(2), 1/np.sqrt(2)]])
    
    assert np.max(np.abs(result - expected)) < 1e-10, 'Test 1 failed: diagonal heading'
    print('Test 1 passed: diagonal heading')
    
    # Test case 2: Horizontal heading (y=0)
    shead = np.array([[2, 4, 6], [0, 0, 0]])
    smid = np.array([[0, 2, 4], [0, 0, 0]])
    result = compute_heading_unit_vector(shead, smid)
    
    expected = np.array([[1, 1, 1], [0, 0, 0]])
    
    assert np.max(np.abs(result - expected)) < 1e-10, 'Test 2 failed: horizontal heading'
    print('Test 2 passed: horizontal heading')
    
    # Test case 3: Vertical heading (x=0)
    shead = np.array([[0, 0, 0], [3, 6, 9]])
    smid = np.array([[0, 0, 0], [0, 3, 6]])
    result = compute_heading_unit_vector(shead, smid)
    
    expected = np.array([[0, 0, 0], [1, 1, 1]])
    
    assert np.max(np.abs(result - expected)) < 1e-10, 'Test 3 failed: vertical heading'
    print('Test 3 passed: vertical heading')
    
    # Test case 4: Zero vector (shead == smid)
    shead = np.array([[1, 2, 3], [1, 2, 3]])
    smid = np.array([[1, 2, 3], [1, 2, 3]])
    result = compute_heading_unit_vector(shead, smid)
    
    expected = np.array([[0, 0, 0], [0, 0, 0]])
    
    assert np.max(np.abs(result - expected)) < 1e-10, 'Test 4 failed: zero vector'
    print('Test 4 passed: zero vector handling')
    
    print('\nAll tests passed for compute_heading_unit_vector!')


if __name__ == '__main__':
    test_compute_heading_unit_vector()

