#!/usr/bin/env python3
"""
batch_process_all_esets.py - Process all GMR61@GMR61 esets

1. Append camera calibration to all H5 files
2. Verify H5 schema for all experiments
3. Copy validated H5s to INDYsim/data/h5_validated/

Author: mechanosensation validation framework
Date: 2025-12-04
"""

import sys
from pathlib import Path
import shutil

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))

from validate_h5_schema import validate_h5_schema


def find_all_esets(base_dir: Path):
    """Find all eset directories with h5_exports."""
    esets = []
    for item in base_dir.iterdir():
        if item.is_dir():
            h5_dir = item / "h5_exports"
            matfiles_dir = item / "matfiles"
            if h5_dir.exists() and matfiles_dir.exists():
                esets.append(item)
    return sorted(esets)


def find_h5_files(eset_dir: Path):
    """Find all H5 files in an eset's h5_exports directory."""
    h5_dir = eset_dir / "h5_exports"
    if h5_dir.exists():
        return sorted(h5_dir.glob("*.h5"))
    return []


def check_has_camcal(h5_path: Path) -> bool:
    """Check if H5 file has lengthPerPixel."""
    import h5py
    try:
        with h5py.File(str(h5_path), 'r') as f:
            return 'lengthPerPixel' in f
    except:
        return False


def main():
    print("=" * 70)
    print("BATCH PROCESS ALL GMR61@GMR61 ESETS")
    print("=" * 70)
    print()
    
    # Configuration
    base_dir = Path(r"D:\rawdata\GMR61@GMR61")
    output_dir = Path(r"D:\INDYsim\data\h5_validated")
    
    # Find all esets
    esets = find_all_esets(base_dir)
    print(f"Found {len(esets)} esets:")
    for eset in esets:
        print(f"  - {eset.name}")
    print()
    
    # Collect all H5 files
    all_h5_files = []
    for eset in esets:
        h5_files = find_h5_files(eset)
        all_h5_files.extend(h5_files)
        print(f"{eset.name}: {len(h5_files)} H5 files")
    
    print(f"\nTotal: {len(all_h5_files)} H5 files")
    print()
    
    # Check which need camcal
    need_camcal = []
    have_camcal = []
    
    print("--- Checking Camera Calibration Status ---")
    for h5_path in all_h5_files:
        if check_has_camcal(h5_path):
            have_camcal.append(h5_path)
            print(f"  ✓ {h5_path.name}")
        else:
            need_camcal.append(h5_path)
            print(f"  ✗ {h5_path.name} (needs camcal)")
    
    print(f"\nHave camcal: {len(have_camcal)}")
    print(f"Need camcal: {len(need_camcal)}")
    print()
    
    # Process esets that need camcal
    if need_camcal:
        print("=" * 70)
        print("STEP 1: APPEND CAMERA CALIBRATION")
        print("=" * 70)
        print()
        
        # Group by eset
        esets_to_process = set()
        for h5_path in need_camcal:
            eset_dir = h5_path.parent.parent
            esets_to_process.add(eset_dir)
        
        print(f"Esets needing camcal: {len(esets_to_process)}")
        print()
        print("Run these commands in PowerShell:")
        print()
        
        for eset_dir in sorted(esets_to_process):
            print(f'python "D:\\INDYsim\\src\\@matlab_conversion\\append_camcal_to_h5.py" --eset-dir "{eset_dir}"')
        
        print()
        print("After running those, re-run this script to continue.")
        return 1
    
    # Validate all H5 files
    print("=" * 70)
    print("STEP 2: VALIDATE H5 SCHEMA")
    print("=" * 70)
    print()
    
    validation_results = []
    for h5_path in all_h5_files:
        print(f"Validating: {h5_path.name}...", end=" ")
        passed, results = validate_h5_schema(h5_path)
        validation_results.append((h5_path, passed, results))
        print("✓ PASS" if passed else "✗ FAIL")
    
    passed_count = sum(1 for _, passed, _ in validation_results if passed)
    print(f"\nValidation: {passed_count}/{len(all_h5_files)} passed")
    
    # Show failures
    failures = [(p, r) for p, passed, r in validation_results if not passed]
    if failures:
        print("\nFailed validations:")
        for h5_path, results in failures:
            print(f"\n  {h5_path.name}:")
            for r in results:
                if not r.passed and r.severity == 'error':
                    print(f"    - {r.message}")
        return 1
    
    # Copy to INDYsim
    print()
    print("=" * 70)
    print("STEP 3: COPY VALIDATED H5s TO INDYsim")
    print("=" * 70)
    print()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    copied = []
    for h5_path in all_h5_files:
        dest = output_dir / h5_path.name
        print(f"Copying: {h5_path.name}...")
        shutil.copy2(h5_path, dest)
        copied.append(dest)
    
    print(f"\n✓ Copied {len(copied)} files to: {output_dir}")
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Esets processed: {len(esets)}")
    print(f"H5 files validated: {len(all_h5_files)}")
    print(f"Files copied to INDYsim: {len(copied)}")
    print(f"Output directory: {output_dir}")
    print()
    print("✓ ALL EXPERIMENTS VALIDATED AND READY FOR SIMULATION")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

