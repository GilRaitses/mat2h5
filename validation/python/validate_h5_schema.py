"""
validate_h5_schema.py - Verify H5 file contains all required fields for validation

This script validates that an H5 experiment file has the complete schema
required for the reverse crawl analysis pipeline. Missing or malformed
fields are reported with specific error messages.

REFERENCE: FIELD_MAPPING.md
"""

import h5py
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
import sys


@dataclass
class FieldSpec:
    """Specification for a required H5 field."""
    path: str
    expected_dtype: str  # 'float64', 'int', 'string', 'any'
    expected_ndim: Optional[int]  # None = any
    expected_shape_0: Optional[int]  # First dimension, None = any
    description: str
    required: bool = True


# Required fields for validation pipeline (based on actual H5 structure)
REQUIRED_FIELDS = [
    # Global time
    FieldSpec('/eti', 'float64', 1, None, 'Global elapsed time array'),
    
    # Camera calibration - primary
    FieldSpec('/lengthPerPixel', 'float64', None, None, 'Camera calibration cm/pixel'),
    FieldSpec('/camcalinfo', 'group', None, None, 'Camera calibration group'),
    
    # Camera calibration - point arrays (required for interpolation reconstruction)
    FieldSpec('/camcalinfo/realx', 'float64', 1, None, 'World X calibration points (cm)'),
    FieldSpec('/camcalinfo/realy', 'float64', 1, None, 'World Y calibration points (cm)'),
    FieldSpec('/camcalinfo/camx', 'float64', 1, None, 'Camera X calibration points'),
    FieldSpec('/camcalinfo/camy', 'float64', 1, None, 'Camera Y calibration points'),
    
    # Camera calibration - triangulation (optional, allows direct use of precomputed Delaunay)
    FieldSpec('/camcalinfo/tri_points', 'float64', 2, None, 'Triangulation points (N, 2)', required=False),
    FieldSpec('/camcalinfo/tri_connectivity', 'int', 2, None, 'Triangle indices (M, 3)', required=False),
    
    # Metadata
    FieldSpec('/metadata', 'group', None, None, 'Metadata group'),
    
    # Global quantities (LED values) - can be group with yData or direct dataset
    FieldSpec('/global_quantities', 'group', None, None, 'Global quantities group'),
    FieldSpec('/global_quantities/led1Val', 'group', None, None, 'LED1 group (contains yData)'),
    FieldSpec('/global_quantities/led2Val', 'group', None, None, 'LED2 group (contains yData)'),
    
    # Tracks group
    FieldSpec('/tracks', 'group', None, None, 'Tracks container group'),
]

# Per-track required fields (relative to /tracks/{track_key}/)
TRACK_FIELDS = [
    FieldSpec('derived_quantities', 'group', None, None, 'Derived quantities group'),
    FieldSpec('derived_quantities/shead', 'float64', 2, 2, 'Smoothed head position (2, N)'),
    FieldSpec('derived_quantities/smid', 'float64', 2, 2, 'Smoothed midpoint position (2, N)'),
    FieldSpec('derived_quantities/eti', 'float64', None, None, 'Track elapsed time (any shape)', required=False),
]

# Alternative position sources (at least one required)
POSITION_FIELDS = [
    'derived_quantities/sloc',
    'points/loc',
]


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    field: str
    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'


def check_field(h5_file: h5py.File, spec: FieldSpec) -> ValidationResult:
    """Check if a field exists and matches specification."""
    path = spec.path
    
    # Check existence
    if path not in h5_file:
        if spec.required:
            return ValidationResult(path, False, f"Required field missing: {path}", 'error')
        else:
            return ValidationResult(path, True, f"Optional field not present: {path}", 'info')
    
    obj = h5_file[path]
    
    # Check if group vs dataset
    if spec.expected_dtype == 'group':
        if isinstance(obj, h5py.Group):
            return ValidationResult(path, True, f"Group exists: {path}", 'info')
        else:
            return ValidationResult(path, False, f"Expected group, got dataset: {path}", 'error')
    
    # For datasets, check dtype and shape
    if isinstance(obj, h5py.Group):
        return ValidationResult(path, False, f"Expected dataset, got group: {path}", 'error')
    
    # Handle scalar vs array datasets
    if obj.shape == ():  # Scalar dataset
        data = np.array([obj[()]])  # Wrap scalar in array for consistent handling
    else:
        data = obj[:]
    
    # Check dtype
    if spec.expected_dtype == 'float64':
        if not np.issubdtype(data.dtype, np.floating):
            return ValidationResult(path, False, 
                f"Expected float dtype, got {data.dtype}: {path}", 'warning')
    elif spec.expected_dtype == 'int':
        if not np.issubdtype(data.dtype, np.integer):
            return ValidationResult(path, False,
                f"Expected int dtype, got {data.dtype}: {path}", 'warning')
    
    # Check ndim
    if spec.expected_ndim is not None:
        if data.ndim != spec.expected_ndim:
            return ValidationResult(path, False,
                f"Expected {spec.expected_ndim}D array, got {data.ndim}D: {path}", 'error')
    
    # Check shape[0]
    if spec.expected_shape_0 is not None:
        # Allow transposed arrays
        if data.shape[0] != spec.expected_shape_0 and data.shape[-1] != spec.expected_shape_0:
            return ValidationResult(path, False,
                f"Expected shape[0]={spec.expected_shape_0}, got shape {data.shape}: {path}", 'error')
    
    return ValidationResult(path, True, f"Field valid: {path} (shape={data.shape}, dtype={data.dtype})", 'info')


def check_track_fields(h5_file: h5py.File, track_key: str) -> List[ValidationResult]:
    """Check all required fields for a single track."""
    results = []
    track_path = f'/tracks/{track_key}'
    
    if track_path not in h5_file:
        results.append(ValidationResult(track_path, False, f"Track not found: {track_path}", 'error'))
        return results
    
    track = h5_file[track_path]
    
    # Check each required track field
    for spec in TRACK_FIELDS:
        full_path = f"{track_path}/{spec.path}"
        
        if spec.path not in track:
            if spec.required:
                results.append(ValidationResult(full_path, False, 
                    f"Required track field missing: {spec.path}", 'error'))
            else:
                results.append(ValidationResult(full_path, True,
                    f"Optional track field not present: {spec.path}", 'info'))
            continue
        
        # Check the field
        new_spec = FieldSpec(full_path, spec.expected_dtype, spec.expected_ndim,
                            spec.expected_shape_0, spec.description, spec.required)
        results.append(check_field(h5_file, new_spec))
    
    # Check position fields (at least one required)
    has_position = False
    for pos_field in POSITION_FIELDS:
        full_path = f"{track_path}/{pos_field}"
        if pos_field in track or full_path in h5_file:
            has_position = True
            # Verify it's valid
            try:
                if pos_field in track:
                    data = track[pos_field][:]
                else:
                    data = h5_file[full_path][:]
                if data.shape[0] == 2 or data.shape[1] == 2:
                    results.append(ValidationResult(full_path, True,
                        f"Position field valid: {pos_field} (shape={data.shape})", 'info'))
                else:
                    results.append(ValidationResult(full_path, False,
                        f"Position field wrong shape: {pos_field} (shape={data.shape})", 'error'))
            except Exception as e:
                results.append(ValidationResult(full_path, False,
                    f"Error reading position field: {e}", 'error'))
            break
    
    if not has_position:
        results.append(ValidationResult(f"{track_path}/position", False,
            f"No position data found. Need one of: {POSITION_FIELDS}", 'error'))
    
    return results


def check_lengthPerPixel(h5_file: h5py.File) -> ValidationResult:
    """Check that lengthPerPixel calibration is present."""
    # Check at root first (primary location after append_camcal_to_h5.py)
    if 'lengthPerPixel' in h5_file:
        val = float(h5_file['lengthPerPixel'][()])
        return ValidationResult('/lengthPerPixel', True,
            f"lengthPerPixel found at root: {val:.8f} cm/pixel", 'info')
    
    # Check in metadata attrs (backup location)
    if 'metadata' in h5_file:
        meta = h5_file['metadata']
        if 'lengthPerPixel' in meta.attrs:
            val = float(meta.attrs['lengthPerPixel'])
            return ValidationResult('/metadata.attrs[lengthPerPixel]', True,
                f"lengthPerPixel found in attrs: {val:.8f} cm/pixel", 'info')
        if 'lengthPerPixel' in meta:
            val = float(meta['lengthPerPixel'][()])
            return ValidationResult('/metadata/lengthPerPixel', True,
                f"lengthPerPixel found as dataset: {val:.8f} cm/pixel", 'info')
    
    return ValidationResult('/lengthPerPixel', False,
        "lengthPerPixel calibration not found - run append_camcal_to_h5.py", 'error')


def validate_h5_schema(h5_path: Path) -> Tuple[bool, List[ValidationResult]]:
    """
    Validate H5 file schema for reverse crawl analysis.
    
    Args:
        h5_path: Path to H5 file
    
    Returns:
        (all_passed, results): Boolean success and list of validation results
    """
    results = []
    
    if not h5_path.exists():
        results.append(ValidationResult(str(h5_path), False, 
            f"H5 file not found: {h5_path}", 'error'))
        return False, results
    
    try:
        with h5py.File(str(h5_path), 'r') as f:
            # Check global required fields
            for spec in REQUIRED_FIELDS:
                results.append(check_field(f, spec))
            
            # Check lengthPerPixel
            results.append(check_lengthPerPixel(f))
            
            # Check all tracks
            if '/tracks' in f:
                track_keys = list(f['tracks'].keys())
                results.append(ValidationResult('/tracks', True,
                    f"Found {len(track_keys)} tracks", 'info'))
                
                # Check first track in detail, sample others
                tracks_to_check = track_keys[:1]  # Always check first
                if len(track_keys) > 1:
                    tracks_to_check.append(track_keys[-1])  # Also check last
                
                for track_key in tracks_to_check:
                    track_results = check_track_fields(f, track_key)
                    results.extend(track_results)
            else:
                results.append(ValidationResult('/tracks', False,
                    "No tracks group found", 'error'))
            
            # Check for time source
            has_time = False
            if '/eti' in f:
                has_time = True
            else:
                # Check if tracks have eti
                for track_key in f.get('tracks', {}).keys():
                    if f'tracks/{track_key}/derived_quantities/eti' in f:
                        has_time = True
                        break
            
            if not has_time:
                results.append(ValidationResult('/eti', False,
                    "No time data found (global /eti or track-level)", 'error'))
    
    except Exception as e:
        results.append(ValidationResult(str(h5_path), False,
            f"Error reading H5 file: {e}", 'error'))
        return False, results
    
    # Determine overall pass/fail
    errors = [r for r in results if r.severity == 'error' and not r.passed]
    all_passed = len(errors) == 0
    
    return all_passed, results


def print_results(results: List[ValidationResult], verbose: bool = False):
    """Print validation results."""
    errors = [r for r in results if r.severity == 'error' and not r.passed]
    warnings = [r for r in results if r.severity == 'warning' and not r.passed]
    
    print(f"\n{'='*60}")
    print("H5 SCHEMA VALIDATION RESULTS")
    print(f"{'='*60}")
    
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for r in errors:
            print(f"  ✗ {r.message}")
    
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for r in warnings:
            print(f"  ⚠ {r.message}")
    
    if verbose:
        print(f"\nPASSED ({len([r for r in results if r.passed])}):")
        for r in results:
            if r.passed and r.severity == 'info':
                print(f"  ✓ {r.message}")
    
    print(f"\n{'='*60}")
    if not errors:
        print("RESULT: PASSED - H5 schema is valid for analysis pipeline")
    else:
        print(f"RESULT: FAILED - {len(errors)} errors found")
    print(f"{'='*60}\n")


def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate H5 file schema for reverse crawl analysis')
    parser.add_argument('h5_file', type=str, help='Path to H5 file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show all validation results, not just errors')
    
    args = parser.parse_args()
    
    h5_path = Path(args.h5_file)
    passed, results = validate_h5_schema(h5_path)
    print_results(results, args.verbose)
    
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())

