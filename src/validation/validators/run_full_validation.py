"""
run_full_validation.py - Batch validation runner for all experiments

Runs schema validation on all H5 files across all esets in GMR61@GMR61.
Reports pass/fail summary and generates validation manifest.

Usage:
    python run_full_validation.py [--base-dir D:\rawdata\GMR61@GMR61]
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from validate_h5_schema import validate_h5_schema, print_results


def find_all_h5_files(base_dir: Path) -> List[Tuple[str, Path, Path]]:
    """
    Find all H5 files and their corresponding MAT files.
    
    Returns:
        List of (eset_name, h5_path, mat_path) tuples
    """
    results = []
    
    for eset_dir in sorted(base_dir.iterdir()):
        if not eset_dir.is_dir():
            continue
        
        h5_dir = eset_dir / "h5_exports"
        mat_dir = eset_dir / "matfiles"
        
        if not h5_dir.exists():
            continue
        
        for h5_file in sorted(h5_dir.glob("*.h5")):
            # Find corresponding MAT file
            mat_file = mat_dir / f"{h5_file.stem}.mat"
            results.append((eset_dir.name, h5_file, mat_file))
    
    return results


def run_schema_validation(h5_files: List[Tuple[str, Path, Path]], verbose: bool = False) -> Dict:
    """
    Run schema validation on all H5 files.
    
    Returns:
        Dict with validation results
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'total': len(h5_files),
        'passed': 0,
        'failed': 0,
        'files': []
    }
    
    print("=" * 70)
    print("SCHEMA VALIDATION - All H5 Files")
    print("=" * 70)
    
    for eset_name, h5_path, mat_path in h5_files:
        print(f"\n[{eset_name}] {h5_path.name}")
        
        passed, validation_results = validate_h5_schema(h5_path)
        
        errors = [r for r in validation_results if r.severity == 'error' and not r.passed]
        warnings = [r for r in validation_results if r.severity == 'warning' and not r.passed]
        
        file_result = {
            'eset': eset_name,
            'h5_file': str(h5_path),
            'mat_file': str(mat_path),
            'mat_exists': mat_path.exists(),
            'passed': passed,
            'errors': [r.message for r in errors],
            'warnings': [r.message for r in warnings]
        }
        
        results['files'].append(file_result)
        
        if passed:
            results['passed'] += 1
            print(f"  [OK] PASSED")
        else:
            results['failed'] += 1
            print(f"  [FAIL] FAILED ({len(errors)} errors)")
            for err in errors[:3]:  # Show first 3 errors
                print(f"    - {err.message}")
            if len(errors) > 3:
                print(f"    ... and {len(errors) - 3} more errors")
        
        if warnings and verbose:
            print(f"  [WARN] {len(warnings)} warnings")
    
    return results


def print_summary(results: Dict):
    """Print validation summary."""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total files: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    if results['failed'] > 0:
        print("\nFailed files:")
        for f in results['files']:
            if not f['passed']:
                print(f"  [FAIL] {f['eset']}/{Path(f['h5_file']).name}")
                for err in f['errors'][:2]:
                    print(f"      {err}")
    
    print("\n" + "=" * 70)
    if results['failed'] == 0:
        print("RESULT: ALL VALIDATIONS PASSED")
    else:
        print(f"RESULT: {results['failed']} FILE(S) FAILED VALIDATION")
    print("=" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run validation on all H5 files in GMR61@GMR61')
    parser.add_argument('--base-dir', type=str, 
                       default=r'D:\rawdata\GMR61@GMR61',
                       help='Base directory containing esets')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show verbose output including warnings')
    parser.add_argument('--output', type=str,
                       help='Save results to JSON file')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"ERROR: Base directory not found: {base_dir}")
        return 1
    
    # Find all H5 files
    h5_files = find_all_h5_files(base_dir)
    
    if not h5_files:
        print(f"No H5 files found in {base_dir}")
        return 1
    
    print(f"Found {len(h5_files)} H5 files across {len(set(f[0] for f in h5_files))} esets\n")
    
    # Run validation
    results = run_schema_validation(h5_files, args.verbose)
    
    # Print summary
    print_summary(results)
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_path}")
    
    # Save to default location
    default_output = Path(__file__).parent / 'validation_results.json'
    with open(default_output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {default_output}")
    
    return 0 if results['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
