#!/usr/bin/env python3
"""
Validate H5 files for INDYsim analysis compatibility.

Checks that all required fields are present and have expected units/ranges.

Created: 2025-12-10
"""

import sys
import h5py
import numpy as np
from pathlib import Path


def validate_h5_for_analysis(h5_path: str, verbose: bool = True) -> list:
    """
    Validate that an H5 file has all required fields for downstream analysis.
    
    Returns a list of problems found (empty if validation passed).
    """
    problems = []
    h5_path = Path(h5_path)
    
    if not h5_path.exists():
        return [f"File not found: {h5_path}"]
    
    with h5py.File(h5_path, 'r') as f:
        # 1. Check derivation_rules
        if 'derivation_rules' not in f:
            problems.append("CRITICAL: Missing /derivation_rules group")
        else:
            dr = f['derivation_rules']
            for attr in ['smoothTime', 'derivTime', 'interpTime']:
                if attr not in dr.attrs:
                    problems.append(f"CRITICAL: Missing derivation_rules.{attr}")
        
        # 2. Check root-level fields
        if 'eti' not in f:
            problems.append("Missing /eti (experiment time index)")
        
        if 'lengthPerPixel' not in f:
            problems.append("Missing /lengthPerPixel (camera calibration)")
        
        # 3. Check tracks exist
        if 'tracks' not in f:
            problems.append("Missing /tracks group")
        else:
            track_keys = [k for k in f['tracks'].keys() if k.startswith('track_')]
            if len(track_keys) == 0:
                problems.append("No tracks found in /tracks")
            else:
                # Check first track for required fields
                first_track = f['tracks'][track_keys[0]]
                
                if 'derived_quantities' not in first_track:
                    problems.append(f"Missing derived_quantities in {track_keys[0]}")
                else:
                    dq = first_track['derived_quantities']
                    required_dq = ['sloc', 'shead', 'smid', 'speed', 'sspineTheta', 'vel_dp', 'eti']
                    for field in required_dq:
                        if field not in dq:
                            problems.append(f"Missing derived_quantities/{field}")
                    
                    # Sanity check: sloc should be in cm (range ~1-20)
                    if 'sloc' in dq:
                        sloc = dq['sloc'][:]
                        sloc_range = sloc.max() - sloc.min()
                        if sloc_range > 100:
                            problems.append(f"WARNING: sloc range {sloc_range:.1f} suggests pixels, not cm")
                        elif sloc_range < 0.1:
                            problems.append(f"WARNING: sloc range {sloc_range:.4f} is suspiciously small")
                    
                    # Sanity check: speed should be in cm/s (typical mean ~0.02)
                    if 'speed' in dq:
                        speed = dq['speed'][:]
                        if speed.ndim == 2:
                            speed = speed.flatten()
                        mean_speed = np.nanmean(speed)
                        if mean_speed > 1.0:
                            problems.append(f"WARNING: mean speed {mean_speed:.3f} suggests mm/s, not cm/s")
                        elif mean_speed < 0.001:
                            problems.append(f"WARNING: mean speed {mean_speed:.6f} is suspiciously low")
        
        # 4. Check global quantities
        if 'global_quantities' not in f:
            problems.append("Missing /global_quantities group")
        else:
            gq = f['global_quantities']
            for led in ['led1Val', 'led2Val']:
                if led not in gq:
                    problems.append(f"Missing global_quantities/{led}")
    
    # Report
    if verbose:
        if problems:
            print(f"VALIDATION FAILED: {h5_path.name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"VALIDATION PASSED: {h5_path.name}")
    
    return problems


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_h5_for_analysis.py <h5_file_or_directory>")
        print("       python validate_h5_for_analysis.py /path/to/exports/")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    
    if target.is_file():
        problems = validate_h5_for_analysis(target)
        sys.exit(1 if problems else 0)
    elif target.is_dir():
        h5_files = list(target.glob("*.h5"))
        if not h5_files:
            print(f"No H5 files found in {target}")
            sys.exit(1)
        
        all_passed = True
        for h5_file in sorted(h5_files):
            problems = validate_h5_for_analysis(h5_file)
            if problems:
                all_passed = False
        
        print()
        if all_passed:
            print(f"ALL {len(h5_files)} FILES PASSED VALIDATION")
        else:
            print(f"SOME FILES FAILED VALIDATION")
        
        sys.exit(0 if all_passed else 1)
    else:
        print(f"Not found: {target}")
        sys.exit(1)


if __name__ == '__main__':
    main()

