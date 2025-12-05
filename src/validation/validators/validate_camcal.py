"""
validate_camcal.py - Validate camera calibration data in H5 matches MATLAB source

Compares:
  - lengthPerPixel (computed value)
  - realx, realy, camx, camy (calibration point arrays)
  - tri_points, tri_connectivity (if present)

Usage:
    python validate_camcal.py <h5_file> <mat_file>
    python validate_camcal.py --batch --base-dir D:\rawdata\GMR61@GMR61
"""

import sys
import numpy as np
import h5py
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class ComparisonResult:
    """Result of comparing a single field."""
    field: str
    h5_value: Optional[np.ndarray]
    mat_value: Optional[np.ndarray]
    match: bool
    max_diff: float
    message: str


def load_camcal_from_h5(h5_path: Path) -> Dict[str, np.ndarray]:
    """Load camera calibration data from H5 file."""
    result = {}
    
    with h5py.File(str(h5_path), 'r') as f:
        # lengthPerPixel from root
        if 'lengthPerPixel' in f:
            result['lengthPerPixel'] = np.array([f['lengthPerPixel'][()]])
        
        # camcalinfo group
        if 'camcalinfo' in f:
            cc = f['camcalinfo']
            for key in cc.keys():
                if isinstance(cc[key], h5py.Dataset):
                    result[key] = cc[key][:]
    
    return result


def load_camcal_from_mat(mat_path: Path) -> Dict[str, np.ndarray]:
    """Load camera calibration data from MATLAB .mat file using MATLAB engine."""
    import matlab.engine
    
    eng = matlab.engine.start_matlab()
    
    try:
        # Add paths
        eng.addpath(r"D:\mechanosensation\scripts\2025-10-16", nargout=0)
        eng.addpath(eng.genpath(r"d:\magniphyq\codebase\Matlab-Track-Analysis-SkanataLab"), nargout=0)
        
        # Load experiment
        eng.eval(f"load('{str(mat_path)}')", nargout=0)
        
        # Handle variable naming
        eng.eval("""
            if exist('experiment', 'var')
                eset = ExperimentSet();
                eset.expt = experiment;
                clear experiment;
            end
        """, nargout=0)
        
        result = {}
        
        # Get camcalinfo
        eng.eval("cc = eset.expt(1).camcalinfo;", nargout=0)
        
        # Extract arrays
        for field in ['realx', 'realy', 'camx', 'camy']:
            try:
                eng.eval(f"arr = cc.{field};", nargout=0)
                val = eng.workspace['arr']
                if val is not None:
                    result[field] = np.array(val).flatten()
            except:
                pass
        
        # Compute lengthPerPixel
        lpp_code = """
            test_pixels_x = [100, 500];
            test_pixels_y = [100, 500];
            real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
            real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
            pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
            real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
            lengthPerPixel = real_dist / pixel_dist;
        """
        eng.eval(lpp_code, nargout=0)
        result['lengthPerPixel'] = np.array([float(eng.workspace['lengthPerPixel'])])
        
        # Compute triangulation
        try:
            eng.eval("""
                tri_connectivity = delaunay(cc.camx, cc.camy);
                tri_points = [cc.camx(:), cc.camy(:)];
            """, nargout=0)
            result['tri_points'] = np.array(eng.workspace['tri_points'])
            result['tri_connectivity'] = np.array(eng.workspace['tri_connectivity']).astype(np.int32) - 1  # 0-based
        except:
            pass
        
        return result
        
    finally:
        eng.quit()


def compare_camcal(h5_data: Dict, mat_data: Dict, tolerance: float = 1e-10) -> List[ComparisonResult]:
    """Compare camera calibration data between H5 and MATLAB."""
    results = []
    
    # Fields to compare
    fields = ['lengthPerPixel', 'realx', 'realy', 'camx', 'camy', 'tri_points', 'tri_connectivity']
    
    for field in fields:
        h5_val = h5_data.get(field)
        mat_val = mat_data.get(field)
        
        if h5_val is None and mat_val is None:
            results.append(ComparisonResult(
                field=field,
                h5_value=None,
                mat_value=None,
                match=True,
                max_diff=0.0,
                message=f"{field}: not present in either (OK)"
            ))
            continue
        
        if h5_val is None:
            results.append(ComparisonResult(
                field=field,
                h5_value=None,
                mat_value=mat_val,
                match=False,
                max_diff=float('inf'),
                message=f"{field}: MISSING in H5, present in MATLAB"
            ))
            continue
        
        if mat_val is None:
            results.append(ComparisonResult(
                field=field,
                h5_value=h5_val,
                mat_value=None,
                match=False,
                max_diff=float('inf'),
                message=f"{field}: present in H5, MISSING in MATLAB"
            ))
            continue
        
        # Both present - compare
        h5_flat = np.array(h5_val).flatten()
        mat_flat = np.array(mat_val).flatten()
        
        if h5_flat.shape != mat_flat.shape:
            results.append(ComparisonResult(
                field=field,
                h5_value=h5_val,
                mat_value=mat_val,
                match=False,
                max_diff=float('inf'),
                message=f"{field}: SHAPE MISMATCH - H5={h5_flat.shape}, MAT={mat_flat.shape}"
            ))
            continue
        
        # Compute difference
        max_diff = np.max(np.abs(h5_flat - mat_flat))
        match = max_diff <= tolerance
        
        if match:
            results.append(ComparisonResult(
                field=field,
                h5_value=h5_val,
                mat_value=mat_val,
                match=True,
                max_diff=max_diff,
                message=f"{field}: MATCH (max_diff={max_diff:.2e}, n={len(h5_flat)})"
            ))
        else:
            results.append(ComparisonResult(
                field=field,
                h5_value=h5_val,
                mat_value=mat_val,
                match=False,
                max_diff=max_diff,
                message=f"{field}: MISMATCH (max_diff={max_diff:.6f}, tolerance={tolerance})"
            ))
    
    return results


def validate_single_experiment(h5_path: Path, mat_path: Path) -> Tuple[bool, List[ComparisonResult]]:
    """Validate camera calibration for a single experiment."""
    
    # Load from H5
    h5_data = load_camcal_from_h5(h5_path)
    
    # Load from MATLAB
    mat_data = load_camcal_from_mat(mat_path)
    
    # Compare
    results = compare_camcal(h5_data, mat_data)
    
    all_match = all(r.match for r in results)
    
    return all_match, results


def print_results(results: List[ComparisonResult], verbose: bool = False):
    """Print comparison results."""
    errors = [r for r in results if not r.match]
    
    if errors:
        print(f"  ✗ {len(errors)} mismatches:")
        for r in errors:
            print(f"      {r.message}")
    else:
        print(f"  ✓ All {len(results)} fields match")
        if verbose:
            for r in results:
                print(f"      {r.message}")


def batch_validate(base_dir: Path) -> Dict:
    """Validate all experiments in base directory."""
    import matlab.engine
    
    print("=" * 70)
    print("CAMERA CALIBRATION VALIDATION")
    print("Comparing H5 exports against MATLAB source files")
    print("=" * 70)
    
    # Find all H5/MAT pairs
    pairs = []
    for eset_dir in sorted(base_dir.iterdir()):
        if not eset_dir.is_dir():
            continue
        
        h5_dir = eset_dir / "h5_exports"
        mat_dir = eset_dir / "matfiles"
        
        if not h5_dir.exists() or not mat_dir.exists():
            continue
        
        for h5_file in sorted(h5_dir.glob("*.h5")):
            mat_file = mat_dir / f"{h5_file.stem}.mat"
            if mat_file.exists():
                pairs.append((eset_dir.name, h5_file, mat_file))
    
    print(f"Found {len(pairs)} H5/MAT pairs\n")
    
    # Start single MATLAB engine for all comparisons
    print("Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    eng.addpath(r"D:\mechanosensation\scripts\2025-10-16", nargout=0)
    eng.addpath(eng.genpath(r"d:\magniphyq\codebase\Matlab-Track-Analysis-SkanataLab"), nargout=0)
    
    results_summary = {
        'total': len(pairs),
        'passed': 0,
        'failed': 0,
        'files': []
    }
    
    try:
        for eset_name, h5_path, mat_path in pairs:
            print(f"\n[{eset_name}] {h5_path.name}")
            
            # Load H5 data
            h5_data = load_camcal_from_h5(h5_path)
            
            # Load MATLAB data using shared engine
            mat_data = {}
            try:
                eng.eval(f"load('{str(mat_path)}')", nargout=0)
                eng.eval("""
                    if exist('experiment', 'var')
                        eset = ExperimentSet();
                        eset.expt = experiment;
                        clear experiment;
                    end
                    cc = eset.expt(1).camcalinfo;
                """, nargout=0)
                
                for field in ['realx', 'realy', 'camx', 'camy']:
                    try:
                        eng.eval(f"arr = cc.{field};", nargout=0)
                        val = eng.workspace['arr']
                        if val is not None:
                            mat_data[field] = np.array(val).flatten()
                    except:
                        pass
                
                # Compute lengthPerPixel
                eng.eval("""
                    test_pixels_x = [100, 500];
                    test_pixels_y = [100, 500];
                    real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
                    real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
                    pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
                    real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
                    lengthPerPixel = real_dist / pixel_dist;
                """, nargout=0)
                mat_data['lengthPerPixel'] = np.array([float(eng.workspace['lengthPerPixel'])])
                
                # Compute triangulation
                eng.eval("""
                    tri_connectivity = delaunay(cc.camx, cc.camy);
                    tri_points = [cc.camx(:), cc.camy(:)];
                """, nargout=0)
                mat_data['tri_points'] = np.array(eng.workspace['tri_points'])
                mat_data['tri_connectivity'] = np.array(eng.workspace['tri_connectivity']).astype(np.int32) - 1
                
            except Exception as e:
                print(f"  ERROR loading MATLAB data: {e}")
                results_summary['failed'] += 1
                results_summary['files'].append({
                    'eset': eset_name,
                    'h5': str(h5_path),
                    'mat': str(mat_path),
                    'passed': False,
                    'error': str(e)
                })
                continue
            
            # Compare
            comparison = compare_camcal(h5_data, mat_data)
            all_match = all(r.match for r in comparison)
            
            print_results(comparison)
            
            if all_match:
                results_summary['passed'] += 1
            else:
                results_summary['failed'] += 1
            
            results_summary['files'].append({
                'eset': eset_name,
                'h5': str(h5_path),
                'mat': str(mat_path),
                'passed': all_match,
                'comparisons': [{'field': r.field, 'match': r.match, 'message': r.message} for r in comparison]
            })
    
    finally:
        eng.quit()
    
    # Print summary
    print("\n" + "=" * 70)
    print("CAMCAL VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total: {results_summary['total']}")
    print(f"Passed: {results_summary['passed']}")
    print(f"Failed: {results_summary['failed']}")
    
    if results_summary['failed'] > 0:
        print("\nFailed files:")
        for f in results_summary['files']:
            if not f['passed']:
                print(f"  ✗ {f['eset']}/{Path(f['h5']).name}")
    
    print("=" * 70)
    
    return results_summary


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate camera calibration in H5 vs MATLAB')
    parser.add_argument('h5_file', type=str, nargs='?', help='Path to H5 file')
    parser.add_argument('mat_file', type=str, nargs='?', help='Path to MAT file')
    parser.add_argument('--batch', action='store_true', help='Batch validate all experiments')
    parser.add_argument('--base-dir', type=str, default=r'D:\rawdata\GMR61@GMR61',
                       help='Base directory for batch mode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.batch:
        results = batch_validate(Path(args.base_dir))
        return 0 if results['failed'] == 0 else 1
    
    elif args.h5_file and args.mat_file:
        h5_path = Path(args.h5_file)
        mat_path = Path(args.mat_file)
        
        print(f"Validating: {h5_path.name}")
        passed, results = validate_single_experiment(h5_path, mat_path)
        print_results(results, args.verbose)
        
        return 0 if passed else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

