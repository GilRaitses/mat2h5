#!/usr/bin/env python3
"""
inspect_h5_structure.py - Inspect H5 file structure for field naming alignment

Run this BEFORE validation to identify any naming discrepancies between
the expected field names and actual H5 structure.
"""

import h5py
import numpy as np
from pathlib import Path


def print_h5_structure(h5_file, path='/', indent=0):
    """Recursively print H5 file structure."""
    prefix = "  " * indent
    
    obj = h5_file[path]
    
    if isinstance(obj, h5py.Group):
        print(f"{prefix}[GROUP] {path}")
        
        # Print attributes
        if obj.attrs:
            for attr_name, attr_val in obj.attrs.items():
                if isinstance(attr_val, bytes):
                    attr_val = attr_val.decode('utf-8', errors='replace')
                print(f"{prefix}  @{attr_name} = {attr_val}")
        
        # Recurse into children
        for key in sorted(obj.keys()):
            child_path = f"{path}/{key}" if path != '/' else f"/{key}"
            print_h5_structure(h5_file, child_path, indent + 1)
    
    elif isinstance(obj, h5py.Dataset):
        dtype = obj.dtype
        shape = obj.shape
        print(f"{prefix}[DATASET] {path}")
        print(f"{prefix}  dtype: {dtype}, shape: {shape}")
        
        # Show sample values for small arrays
        if obj.size < 10:
            print(f"{prefix}  values: {obj[:]}")
        elif obj.ndim == 1:
            print(f"{prefix}  first 3: {obj[:3]}")
            print(f"{prefix}  last 3: {obj[-3:]}")
        elif obj.ndim == 2 and obj.shape[0] <= 3:
            print(f"{prefix}  first col (3): {obj[:, :3]}")


def check_expected_fields(h5_file):
    """Check for expected fields and report missing/found status."""
    print("\n" + "=" * 70)
    print("FIELD ALIGNMENT CHECK")
    print("=" * 70 + "\n")
    
    # Expected fields from FIELD_MAPPING.md
    expected = {
        # Global
        '/eti': 'Global elapsed time array',
        '/metadata': 'Metadata group',
        '/global_quantities': 'Global quantities group',
        '/tracks': 'Tracks container group',
        
        # Metadata
        '/metadata/lengthPerPixel': 'Camera calibration (as dataset)',
        
        # LED - multiple possible names
        '/global_quantities/led1Val': 'LED1 values (yData)',
        '/global_quantities/led2Val': 'LED2 values (yData)',
    }
    
    # LED time - could be named various ways
    led_time_options = {
        'led1': ['/global_quantities/led1Val_xData', 
                 '/global_quantities/led1_xdata',
                 '/global_quantities/led1Val_time'],
        'led2': ['/global_quantities/led2Val_xData',
                 '/global_quantities/led2_xdata', 
                 '/global_quantities/led2Val_time'],
    }
    
    found = {}
    missing = {}
    
    # Check expected fields
    for path, desc in expected.items():
        if path in h5_file:
            found[path] = desc
        else:
            # Check if it's an attribute instead
            parent = '/'.join(path.split('/')[:-1]) or '/'
            attr_name = path.split('/')[-1]
            if parent in h5_file and attr_name in h5_file[parent].attrs:
                found[f"{parent}@{attr_name}"] = f"{desc} (as attribute)"
            else:
                missing[path] = desc
    
    # Check LED time fields
    for led, options in led_time_options.items():
        found_option = None
        for opt in options:
            if opt in h5_file:
                found_option = opt
                break
        
        if found_option:
            found[found_option] = f"{led.upper()} timestamps (xData)"
        else:
            missing[f"{led}_xdata"] = f"{led.upper()} timestamps - tried: {options}"
    
    # Print results
    print("FOUND:")
    for path, desc in sorted(found.items()):
        print(f"  ✓ {path}: {desc}")
    
    print("\nMISSING:")
    if missing:
        for path, desc in sorted(missing.items()):
            print(f"  ✗ {path}: {desc}")
    else:
        print("  (none)")
    
    return found, missing


def check_track_structure(h5_file):
    """Check track structure in detail."""
    print("\n" + "=" * 70)
    print("TRACK STRUCTURE CHECK")
    print("=" * 70 + "\n")
    
    if '/tracks' not in h5_file:
        print("ERROR: /tracks group not found!")
        return
    
    tracks = h5_file['/tracks']
    track_keys = list(tracks.keys())
    print(f"Found {len(track_keys)} tracks")
    print(f"Track keys: {track_keys[:5]}{'...' if len(track_keys) > 5 else ''}\n")
    
    # Check first track in detail
    if track_keys:
        first_key = track_keys[0]
        track = tracks[first_key]
        
        print(f"Checking track: {first_key}")
        print(f"Keys in track: {list(track.keys())}")
        
        # Expected track fields
        track_expected = {
            'derived_quantities': 'group',
            'derived_quantities/shead': '(2, N) or (N, 2)',
            'derived_quantities/smid': '(2, N) or (N, 2)',
            'derived_quantities/eti': '(N,)',
            'derived_quantities/sloc': '(2, N) or (N, 2)',
            'points': 'group',
            'points/loc': '(2, N) or (N, 2)',
        }
        
        print("\nTrack field check:")
        for field, expected_shape in track_expected.items():
            full_path = f"/tracks/{first_key}/{field}"
            if full_path in h5_file:
                obj = h5_file[full_path]
                if isinstance(obj, h5py.Dataset):
                    print(f"  ✓ {field}: shape={obj.shape}, dtype={obj.dtype}")
                else:
                    print(f"  ✓ {field}: (group)")
            else:
                print(f"  ✗ {field}: NOT FOUND (expected {expected_shape})")


def main():
    # Configuration
    h5_dir = Path(r"D:\rawdata\GMR61@GMR61\T_Re_Sq_50to250PWM_30#C_Bl_7PWM\h5_exports")
    experiment_name = "GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_202506251614"
    h5_file = h5_dir / f"{experiment_name}.h5"
    
    print("=" * 70)
    print("H5 FILE STRUCTURE INSPECTION")
    print("=" * 70)
    print(f"\nFile: {h5_file}")
    
    if not h5_file.exists():
        print(f"\nERROR: H5 file not found!")
        print(f"Expected: {h5_file}")
        print("\nPlease ensure the H5 export has been run.")
        return 1
    
    print(f"Size: {h5_file.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    with h5py.File(str(h5_file), 'r') as f:
        # Print full structure
        print("=" * 70)
        print("FULL H5 STRUCTURE")
        print("=" * 70 + "\n")
        print_h5_structure(f)
        
        # Check expected fields
        found, missing = check_expected_fields(f)
        
        # Check track structure
        check_track_structure(f)
        
        # Check global_quantities in detail
        print("\n" + "=" * 70)
        print("GLOBAL QUANTITIES DETAIL")
        print("=" * 70 + "\n")
        
        if '/global_quantities' in f:
            gq = f['/global_quantities']
            print(f"Keys: {list(gq.keys())}")
            for key in gq.keys():
                obj = gq[key]
                if isinstance(obj, h5py.Dataset):
                    print(f"  {key}: shape={obj.shape}, dtype={obj.dtype}")
        else:
            print("No global_quantities group found")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"\nFields found: {len(found)}")
        print(f"Fields missing: {len(missing)}")
        
        if missing:
            print("\n⚠ ACTION REQUIRED: Update H5 export or validation scripts to resolve missing fields")
        else:
            print("\n✓ All expected fields found - ready for validation")
    
    return 0 if not missing else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

