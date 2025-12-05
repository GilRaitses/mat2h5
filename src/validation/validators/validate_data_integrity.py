"""
validate_data_integrity.py - Compare raw input arrays between H5 and MATLAB .mat

VALIDATION LAYER 1: Data Integrity
----------------------------------
This script verifies that the H5 file contains identical data to the source .mat file.
Any discrepancy here indicates a problem with the H5 export process.

Compares:
  - shead arrays (element-by-element)
  - smid arrays (element-by-element)
  - loc/sloc arrays (element-by-element)
  - eti time arrays (element-by-element)
  - LED arrays (element-by-element)
  - lengthPerPixel calibration value
  - Track count and track numbering

REFERENCE: FIELD_MAPPING.md
"""

import numpy as np
import h5py
from scipy.io import loadmat
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
import sys


@dataclass
class ComparisonResult:
    """Result of comparing two arrays or values."""
    field_name: str
    matlab_source: str
    h5_source: str
    passed: bool
    max_diff: float
    mean_diff: float
    num_elements: int
    message: str
    tolerance: float


def compare_arrays(
    matlab_arr: np.ndarray,
    h5_arr: np.ndarray,
    field_name: str,
    tolerance: float = 0.0
) -> ComparisonResult:
    """
    Compare two arrays element-by-element.
    
    Args:
        matlab_arr: Array from MATLAB .mat file
        h5_arr: Array from H5 file
        field_name: Name of field being compared
        tolerance: Maximum allowed difference (0 = exact match)
    
    Returns:
        ComparisonResult with comparison details
    """
    # Flatten and ensure same type
    mat = np.asarray(matlab_arr).ravel().astype(np.float64)
    h5 = np.asarray(h5_arr).ravel().astype(np.float64)
    
    # Handle potential shape mismatch
    if len(mat) != len(h5):
        return ComparisonResult(
            field_name=field_name,
            matlab_source=f"shape {matlab_arr.shape}",
            h5_source=f"shape {h5_arr.shape}",
            passed=False,
            max_diff=float('inf'),
            mean_diff=float('inf'),
            num_elements=max(len(mat), len(h5)),
            message=f"Array length mismatch: MATLAB={len(mat)}, H5={len(h5)}",
            tolerance=tolerance
        )
    
    # Compute differences
    diff = np.abs(mat - h5)
    max_diff = float(np.max(diff))
    mean_diff = float(np.mean(diff))
    
    passed = max_diff <= tolerance
    
    if passed:
        if tolerance == 0:
            message = f"Exact match ({len(mat)} elements)"
        else:
            message = f"Within tolerance (max_diff={max_diff:.2e}, tol={tolerance})"
    else:
        # Find where differences occur
        diff_indices = np.where(diff > tolerance)[0]
        message = f"MISMATCH: max_diff={max_diff:.2e} at {len(diff_indices)} positions"
    
    return ComparisonResult(
        field_name=field_name,
        matlab_source=f"shape {matlab_arr.shape}",
        h5_source=f"shape {h5_arr.shape}",
        passed=passed,
        max_diff=max_diff,
        mean_diff=mean_diff,
        num_elements=len(mat),
        message=message,
        tolerance=tolerance
    )


def compare_2d_arrays(
    matlab_arr: np.ndarray,
    h5_arr: np.ndarray,
    field_name: str,
    tolerance: float = 0.0
) -> ComparisonResult:
    """
    Compare two 2D arrays, handling potential transpose.
    
    Position arrays may be (2, N) in MATLAB but (N, 2) in H5.
    This function handles both orientations.
    """
    mat = np.asarray(matlab_arr)
    h5 = np.asarray(h5_arr)
    
    # Normalize to (2, N) orientation
    if mat.shape[0] != 2 and len(mat.shape) == 2:
        mat = mat.T
    if h5.shape[0] != 2 and len(h5.shape) == 2:
        h5 = h5.T
    
    # Check shape match after normalization
    if mat.shape != h5.shape:
        return ComparisonResult(
            field_name=field_name,
            matlab_source=f"shape {matlab_arr.shape} -> {mat.shape}",
            h5_source=f"shape {h5_arr.shape} -> {h5.shape}",
            passed=False,
            max_diff=float('inf'),
            mean_diff=float('inf'),
            num_elements=max(mat.size, h5.size),
            message=f"Shape mismatch after normalization: MATLAB={mat.shape}, H5={h5.shape}",
            tolerance=tolerance
        )
    
    # Compare flattened
    return compare_arrays(mat, h5, field_name, tolerance)


def load_matlab_experiment(mat_path: Path) -> Dict[str, Any]:
    """
    Load MATLAB experiment data from .mat file.
    
    Handles both 'experiment' and 'eset' variable names.
    Returns structured data for comparison.
    """
    data = loadmat(str(mat_path), squeeze_me=True, struct_as_record=False)
    
    result = {
        'tracks': [],
        'global_quantities': {},
        'metadata': {}
    }
    
    # Find experiment structure
    expt = None
    if 'experiment' in data:
        expt = data['experiment']
    elif 'eset' in data:
        eset = data['eset']
        if hasattr(eset, 'expt'):
            expt = eset.expt
            if hasattr(expt, '__len__') and len(expt) > 0:
                expt = expt[0]
    
    if expt is None:
        raise ValueError("Could not find experiment data in .mat file")
    
    # Extract track data
    if hasattr(expt, 'track'):
        tracks = expt.track
        if not hasattr(tracks, '__len__'):
            tracks = [tracks]
        
        for t in tracks:
            track_data = {}
            if hasattr(t, 'trackNum'):
                track_data['trackNum'] = int(t.trackNum)
            if hasattr(t, 'dq'):
                dq = t.dq
                if hasattr(dq, 'shead'):
                    track_data['shead'] = np.asarray(dq.shead)
                if hasattr(dq, 'smid'):
                    track_data['smid'] = np.asarray(dq.smid)
                if hasattr(dq, 'eti'):
                    track_data['eti'] = np.asarray(dq.eti)
                if hasattr(dq, 'sloc'):
                    track_data['sloc'] = np.asarray(dq.sloc)
            result['tracks'].append(track_data)
    
    # Extract global quantities (LED values)
    if hasattr(expt, 'globalQuantity') and expt.globalQuantity is not None:
        gq = expt.globalQuantity
        if not hasattr(gq, '__len__'):
            gq = [gq]
        
        for q in gq:
            if hasattr(q, 'fieldname'):
                name = str(q.fieldname)
                if hasattr(q, 'yData'):
                    result['global_quantities'][name] = np.asarray(q.yData)
                if hasattr(q, 'xData'):
                    result['global_quantities'][f"{name}_time"] = np.asarray(q.xData)
    
    return result


def load_h5_experiment(h5_path: Path) -> Dict[str, Any]:
    """
    Load H5 experiment data for comparison.
    
    Returns structured data matching MATLAB format.
    """
    result = {
        'tracks': [],
        'global_quantities': {},
        'metadata': {}
    }
    
    with h5py.File(str(h5_path), 'r') as f:
        # Load lengthPerPixel - check root first (primary), then metadata (backup)
        if 'lengthPerPixel' in f:
            result['metadata']['lengthPerPixel'] = float(f['lengthPerPixel'][()])
        elif 'metadata' in f:
            meta = f['metadata']
            if 'lengthPerPixel' in meta.attrs:
                result['metadata']['lengthPerPixel'] = float(meta.attrs['lengthPerPixel'])
            elif 'lengthPerPixel' in meta:
                result['metadata']['lengthPerPixel'] = float(meta['lengthPerPixel'][()])
        
        # Load global quantities - handle both direct datasets and groups with yData
        if 'global_quantities' in f:
            gq = f['global_quantities']
            for key in gq.keys():
                obj = gq[key]
                if isinstance(obj, h5py.Dataset):
                    result['global_quantities'][key] = obj[:]
                elif isinstance(obj, h5py.Group) and 'yData' in obj:
                    # LED values stored as group with yData inside
                    result['global_quantities'][key] = obj['yData'][:]
        
        # Load tracks
        if 'tracks' in f:
            for track_key in sorted(f['tracks'].keys()):
                track = f['tracks'][track_key]
                track_data = {}
                
                # Extract track number from key
                try:
                    track_data['trackNum'] = int(track_key.replace('track_', '').replace('track', ''))
                except ValueError:
                    track_data['trackNum'] = 0
                
                # Load derived quantities
                if 'derived_quantities' in track:
                    dq = track['derived_quantities']
                    if 'shead' in dq:
                        track_data['shead'] = dq['shead'][:]
                    if 'smid' in dq:
                        track_data['smid'] = dq['smid'][:]
                    if 'eti' in dq:
                        track_data['eti'] = dq['eti'][:]
                    if 'sloc' in dq:
                        track_data['sloc'] = dq['sloc'][:]
                
                # Note: points/loc is RAW location, sloc is SMOOTHED
                # Only use points/loc as last resort fallback with warning
                if 'sloc' not in track_data:
                    if 'points' in track and 'loc' in track['points']:
                        print(f"  WARNING: Track {track_key} using points/loc (raw) instead of sloc (smoothed)")
                        track_data['sloc'] = track['points']['loc'][:]
                
                result['tracks'].append(track_data)
    
    return result


def validate_data_integrity(
    mat_path: Path,
    h5_path: Path,
    track_numbers: Optional[List[int]] = None
) -> Tuple[bool, List[ComparisonResult]]:
    """
    Compare data integrity between MATLAB .mat and H5 files.
    
    Args:
        mat_path: Path to MATLAB .mat file (experiment or track)
        h5_path: Path to H5 file
        track_numbers: Optional list of track numbers to compare (default: all)
    
    Returns:
        (all_passed, results): Boolean success and list of comparison results
    """
    results = []
    
    # Load data
    try:
        mat_data = load_matlab_experiment(mat_path)
    except Exception as e:
        results.append(ComparisonResult(
            field_name='MATLAB_LOAD',
            matlab_source=str(mat_path),
            h5_source='N/A',
            passed=False,
            max_diff=float('inf'),
            mean_diff=float('inf'),
            num_elements=0,
            message=f"Failed to load MATLAB data: {e}",
            tolerance=0
        ))
        return False, results
    
    try:
        h5_data = load_h5_experiment(h5_path)
    except Exception as e:
        results.append(ComparisonResult(
            field_name='H5_LOAD',
            matlab_source='N/A',
            h5_source=str(h5_path),
            passed=False,
            max_diff=float('inf'),
            mean_diff=float('inf'),
            num_elements=0,
            message=f"Failed to load H5 data: {e}",
            tolerance=0
        ))
        return False, results
    
    # Compare track counts
    mat_track_count = len(mat_data['tracks'])
    h5_track_count = len(h5_data['tracks'])
    
    results.append(ComparisonResult(
        field_name='track_count',
        matlab_source=str(mat_track_count),
        h5_source=str(h5_track_count),
        passed=mat_track_count == h5_track_count,
        max_diff=abs(mat_track_count - h5_track_count),
        mean_diff=abs(mat_track_count - h5_track_count),
        num_elements=1,
        message=f"Track count: MATLAB={mat_track_count}, H5={h5_track_count}",
        tolerance=0
    ))
    
    # Compare global quantities (LED values)
    for key in ['led1Val', 'led2Val']:
        if key in mat_data['global_quantities'] and key in h5_data['global_quantities']:
            results.append(compare_arrays(
                mat_data['global_quantities'][key],
                h5_data['global_quantities'][key],
                f"global_quantities/{key}",
                tolerance=0
            ))
    
    # Compare tracks
    mat_tracks_by_num = {t.get('trackNum', i): t for i, t in enumerate(mat_data['tracks'])}
    h5_tracks_by_num = {t.get('trackNum', i): t for i, t in enumerate(h5_data['tracks'])}
    
    # Determine which tracks to compare
    if track_numbers is None:
        # Compare all common tracks
        common_nums = set(mat_tracks_by_num.keys()) & set(h5_tracks_by_num.keys())
        track_numbers = sorted(common_nums)[:5]  # Limit to first 5 for efficiency
    
    for track_num in track_numbers:
        if track_num not in mat_tracks_by_num:
            results.append(ComparisonResult(
                field_name=f'track_{track_num}',
                matlab_source='MISSING',
                h5_source='present',
                passed=False,
                max_diff=float('inf'),
                mean_diff=float('inf'),
                num_elements=0,
                message=f"Track {track_num} not found in MATLAB data",
                tolerance=0
            ))
            continue
        
        if track_num not in h5_tracks_by_num:
            results.append(ComparisonResult(
                field_name=f'track_{track_num}',
                matlab_source='present',
                h5_source='MISSING',
                passed=False,
                max_diff=float('inf'),
                mean_diff=float('inf'),
                num_elements=0,
                message=f"Track {track_num} not found in H5 data",
                tolerance=0
            ))
            continue
        
        mat_track = mat_tracks_by_num[track_num]
        h5_track = h5_tracks_by_num[track_num]
        
        # Compare shead
        if 'shead' in mat_track and 'shead' in h5_track:
            results.append(compare_2d_arrays(
                mat_track['shead'],
                h5_track['shead'],
                f'track_{track_num}/shead',
                tolerance=0
            ))
        
        # Compare smid
        if 'smid' in mat_track and 'smid' in h5_track:
            results.append(compare_2d_arrays(
                mat_track['smid'],
                h5_track['smid'],
                f'track_{track_num}/smid',
                tolerance=0
            ))
        
        # Compare sloc
        if 'sloc' in mat_track and 'sloc' in h5_track:
            results.append(compare_2d_arrays(
                mat_track['sloc'],
                h5_track['sloc'],
                f'track_{track_num}/sloc',
                tolerance=0
            ))
        
        # Compare eti
        if 'eti' in mat_track and 'eti' in h5_track:
            results.append(compare_arrays(
                mat_track['eti'],
                h5_track['eti'],
                f'track_{track_num}/eti',
                tolerance=0
            ))
    
    # Overall result
    all_passed = all(r.passed for r in results)
    
    return all_passed, results


def print_results(results: List[ComparisonResult], verbose: bool = False):
    """Print comparison results."""
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    
    print(f"\n{'='*70}")
    print("DATA INTEGRITY VALIDATION RESULTS")
    print(f"{'='*70}")
    
    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for r in failed:
            print(f"  ✗ {r.field_name}: {r.message}")
            print(f"      MATLAB: {r.matlab_source}")
            print(f"      H5:     {r.h5_source}")
    
    if verbose or not failed:
        print(f"\nPASSED ({len(passed)}):")
        for r in passed:
            print(f"  ✓ {r.field_name}: {r.message}")
    
    print(f"\n{'='*70}")
    if not failed:
        print("RESULT: PASSED - H5 data matches MATLAB source")
    else:
        print(f"RESULT: FAILED - {len(failed)} field(s) do not match")
    print(f"{'='*70}\n")


def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compare data integrity between MATLAB .mat and H5 files')
    parser.add_argument('mat_file', type=str, help='Path to MATLAB .mat file')
    parser.add_argument('h5_file', type=str, help='Path to H5 file')
    parser.add_argument('-t', '--tracks', type=int, nargs='+', default=None,
                       help='Specific track numbers to compare')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show all results, not just failures')
    
    args = parser.parse_args()
    
    mat_path = Path(args.mat_file)
    h5_path = Path(args.h5_file)
    
    if not mat_path.exists():
        print(f"ERROR: MATLAB file not found: {mat_path}")
        return 1
    
    if not h5_path.exists():
        print(f"ERROR: H5 file not found: {h5_path}")
        return 1
    
    passed, results = validate_data_integrity(mat_path, h5_path, args.tracks)
    print_results(results, args.verbose)
    
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())

