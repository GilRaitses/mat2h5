#!/usr/bin/env python3
"""
Batch Export Script for INDYsim MATLAB Data Conversion

Processes all ESET folders in a genotype directory using native folder structure.
Handles dynamic genotype parsing, file discovery, and H5 export.

Source: Adapted from D:\mechanosensation\scripts\2025-11-11\batch_export_indysim.py

Author: mechanobro (adapted for INDYsim)
Date: 2025-11-11
"""

import sys
import subprocess
import os
from pathlib import Path
import time
import re
from typing import Dict, List, Optional

# Script paths (relative to this file)
CONVERT_SCRIPT = Path(__file__).parent / "convert_matlab_to_h5.py"
MAT2H5_ROOT = Path(__file__).parent.parent


def parse_genotype_from_path(eset_path: Path, mat_filename: str) -> Optional[str]:
    """Parse genotype from mat filename or parent folder path"""
    match = re.search(r'^([A-Za-z0-9]+@[A-Za-z0-9]+)_', mat_filename)
    if match:
        return match.group(1)
    
    parent = eset_path.parent
    if parent.name and '@' in parent.name:
        parts = parent.name.split('@')
        if len(parts) == 2 and parts[0] == parts[1]:
            return parent.name
    
    return None


def extract_timestamp_from_mat(mat_filename: str) -> Optional[str]:
    """Extract 12-digit timestamp from mat filename"""
    match = re.search(r'_(\d{12})\.mat$', mat_filename)
    return match.group(1) if match else None


def detect_experiments_in_eset(eset_dir: Path) -> List[Dict]:
    """
    Detect all experiments in an ESET folder.
    
    Uses matfiles/ directory for .mat files (MATLAB expects these, not btdfiles/).
    """
    matfiles_dir = eset_dir / "matfiles"
    
    if not matfiles_dir.exists():
        print(f"  [ERROR] matfiles directory not found: {matfiles_dir}")
        return []
    
    # Find all .mat files in matfiles/ (MATLAB expects these)
    mat_files = list(matfiles_dir.glob("*.mat"))
    
    if not mat_files:
        print(f"  [WARNING] No .mat files found in {matfiles_dir}")
        return []
    
    print(f"  Found {len(mat_files)} .mat files in matfiles/")
    
    experiments = []
    
    for mat_file in sorted(mat_files):
        timestamp = extract_timestamp_from_mat(mat_file.name)
        if not timestamp:
            print(f"  [SKIP] Could not extract timestamp from {mat_file.name}")
            continue
        
        base_name = mat_file.stem
        genotype = parse_genotype_from_path(eset_dir, mat_file.name)
        
        if not genotype:
            print(f"  [SKIP] Could not parse genotype from {mat_file.name}")
            continue
        
        # Tracks directory: in matfiles/ subdirectory
        tracks_name = f"{genotype}_{timestamp} - tracks"
        tracks_dir = matfiles_dir / tracks_name
        
        # FID .bin file: Root level of ESET
        bin_file = eset_dir / f"{base_name}.bin"
        
        # Sup data dir: Root level of ESET
        sup_data_name = f"{base_name} sup data dir"
        sup_data_dir = eset_dir / sup_data_name
        
        # LED bin files in sup data dir
        led1_bin = sup_data_dir / f"{base_name} led1 values.bin"
        led2_bin = sup_data_dir / f"{base_name} led2 values.bin"
        
        # Validate ALL required files exist
        missing_files = []
        
        if not mat_file.exists():
            missing_files.append(f"MAT file: {mat_file}")
        if not tracks_dir.exists():
            missing_files.append(f"Tracks directory: {tracks_dir}")
        if not bin_file.exists():
            missing_files.append(f"FID .bin file: {bin_file}")
        if not sup_data_dir.exists():
            missing_files.append(f"Sup data directory: {sup_data_dir}")
        if not led1_bin.exists():
            missing_files.append(f"LED1 values bin: {led1_bin}")
        
        has_led2 = led2_bin.exists()
        
        if missing_files:
            print(f"  [SKIP] {mat_file.name} - missing files:")
            for f in missing_files:
                print(f"    - {f}")
            continue
        
        experiments.append({
            'mat_file': mat_file,
            'tracks_dir': tracks_dir,
            'bin_file': bin_file,
            'sup_data_dir': sup_data_dir,
            'led1_bin': led1_bin,
            'led2_bin': led2_bin,
            'has_led2': has_led2,
            'base_name': base_name,
            'timestamp': timestamp,
            'genotype': genotype
        })
    
    return experiments


def export_experiment(file_info: Dict, output_dir: Path, codebase_path: Path = None) -> Dict:
    """Export a single experiment using convert_matlab_to_h5.py"""
    base_name = file_info['base_name']
    
    print(f"\n{'='*80}")
    print(f"EXPORTING: {base_name}")
    print(f"{'='*80}")
    print(f"  Genotype: {file_info['genotype']}")
    print(f"  Timestamp: {file_info['timestamp']}")
    print(f"  MAT file: {file_info['mat_file'].name}")
    print(f"  Tracks: {file_info['tracks_dir'].name}")
    print(f"  BIN file: {file_info['bin_file'].name}")
    print()
    
    # Output filename matches base_name with .h5 extension
    output_file = output_dir / f"{base_name}.h5"
    
    # Build command
    cmd = [
        sys.executable,
        str(CONVERT_SCRIPT),
        '--mat', str(file_info['mat_file']),
        '--tracks', str(file_info['tracks_dir']),
        '--bin', str(file_info['bin_file']),
        '--output', str(output_file)
    ]
    
    # Add codebase path if provided
    if codebase_path:
        cmd.extend(['--codebase', str(codebase_path)])
    
    # Run export
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(CONVERT_SCRIPT.parent),
            check=True,
            capture_output=False,
            text=True
        )
        
        elapsed = time.time() - start_time
        file_size = output_file.stat().st_size / (1024 * 1024) if output_file.exists() else 0
        
        print(f"\n  [SUCCESS] Export complete: {output_file.name}")
        print(f"     Size: {file_size:.1f} MB")
        print(f"     Time: {elapsed/60:.1f} minutes")
        
        return {
            'success': True,
            'output_file': output_file,
            'file_size_mb': file_size,
            'time_min': elapsed / 60,
            'base_name': base_name,
            'timestamp': file_info['timestamp']
        }
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"\n  [ERROR] Export failed after {elapsed/60:.1f} minutes")
        print(f"     Error code: {e.returncode}")
        return {
            'success': False,
            'error': f"Exit code {e.returncode}",
            'base_name': base_name,
            'timestamp': file_info['timestamp'],
            'time_min': elapsed / 60
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n  [ERROR] Export failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'base_name': base_name,
            'timestamp': file_info['timestamp'],
            'time_min': elapsed / 60
        }


def process_genotype(root_dir: Path, output_dir: Path, codebase_path: Path = None) -> List[Dict]:
    """
    Process all ESET folders in a root directory.
    
    Args:
        root_dir: Path to root directory containing ESET folders
        output_dir: Path to output directory for H5 files
        codebase_path: Path to MAGAT codebase
    
    Returns:
        List of export results
    """
    print("="*80)
    print(f"PROCESSING ROOT DIRECTORY: {root_dir.name}")
    print("="*80)
    
    # Find all ESET folders
    eset_folders = [d for d in root_dir.iterdir() if d.is_dir() and (d / "matfiles").exists()]
    
    if not eset_folders:
        print(f"[WARNING] No ESET folders found in {root_dir.name}")
        return []
    
    print(f"[OK] Found {len(eset_folders)} ESET folders")
    
    all_results = []
    
    for eset_idx, eset_dir in enumerate(sorted(eset_folders), 1):
        print(f"\n{'='*80}")
        print(f"ESET {eset_idx}/{len(eset_folders)}: {eset_dir.name}")
        print(f"{'='*80}")
        
        experiments = detect_experiments_in_eset(eset_dir)
        
        if not experiments:
            print(f"[WARNING] No complete experiments found in {eset_dir.name}")
            continue
        
        print(f"[OK] Found {len(experiments)} complete experiments")
        
        for exp_idx, file_info in enumerate(experiments, 1):
            print(f"\n[{exp_idx}/{len(experiments)}] Processing experiment...")
            result = export_experiment(file_info, output_dir, codebase_path)
            all_results.append(result)
            
            if exp_idx < len(experiments):
                print("\n" + "-"*80)
                time.sleep(2)
    
    return all_results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch export MATLAB experiments to H5 format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process root directory with multiple ESETs
  python batch_export_esets.py --root-dir "/path/to/GMR61@GMR61" --output-dir "/path/to/output" --codebase "/path/to/codebase"
  
  # Process single ESET directory
  python batch_export_esets.py --eset-dir "/path/to/T_Re_Sq_0to250PWM_30#C_Bl_7PWM" --output-dir "/path/to/output" --codebase "/path/to/codebase"
        """
    )
    parser.add_argument('--root-dir', type=str, default=None,
                       help='Root directory containing ESET folders (e.g., GMR61@GMR61/)')
    parser.add_argument('--eset-dir', type=str, default=None,
                       help='Single ESET directory to process')
    parser.add_argument('--output-dir', type=str, required=True,
                       help='Output directory for H5 files')
    parser.add_argument('--codebase', type=str, default=None,
                       help='Path to MAGAT codebase (or set MAGAT_CODEBASE env var)')
    
    args = parser.parse_args()
    
    # Verify dependencies
    if not CONVERT_SCRIPT.exists():
        print(f"[ERROR] Convert script not found: {CONVERT_SCRIPT}")
        return 1
    
    # Get codebase path
    codebase_path = args.codebase or os.environ.get('MAGAT_CODEBASE')
    if codebase_path:
        codebase_path = Path(codebase_path)
        os.environ['MAGAT_CODEBASE'] = str(codebase_path)
        print(f"[INFO] Using MAGAT codebase: {codebase_path}")
    
    # Set output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("BATCH EXPORT: MATLAB TO H5 CONVERSION")
    print("="*80)
    print(f"Output directory: {output_dir}")
    print(f"Convert script: {CONVERT_SCRIPT}")
    if codebase_path:
        print(f"MAGAT codebase: {codebase_path}")
    print()
    
    # Get codebase path from argument or environment
    codebase_path = args.codebase or os.environ.get('MAGAT_CODEBASE')
    if codebase_path:
        codebase_path = Path(codebase_path)
    else:
        codebase_path = None
    
    # Process ESETs
    if args.eset_dir:
        # Process single ESET
        eset_dir = Path(args.eset_dir)
        if not eset_dir.exists():
            print(f"[ERROR] ESET directory not found: {eset_dir}")
            return 1
        
        experiments = detect_experiments_in_eset(eset_dir)
        if not experiments:
            print(f"[ERROR] No complete experiments found in {eset_dir}")
            return 1
        
        all_results = []
        for exp_idx, file_info in enumerate(experiments, 1):
            print(f"\n[{exp_idx}/{len(experiments)}] Processing experiment...")
            result = export_experiment(file_info, output_dir, codebase_path)
            all_results.append(result)
    elif args.root_dir:
        # Process root directory with multiple ESETs
        root_dir = Path(args.root_dir)
        if not root_dir.exists():
            print(f"[ERROR] Root directory not found: {root_dir}")
            return 1
        
        all_results = process_genotype(root_dir, output_dir, codebase_path)
    else:
        print("[ERROR] Must specify either --root-dir or --eset-dir")
        return 1
    
    # Summary
    total_time = time.time()
    successful = [r for r in all_results if r['success']]
    failed = [r for r in all_results if not r['success']]
    
    print("\n" + "="*80)
    print("BATCH EXPORT SUMMARY")
    print("="*80)
    print(f"Total experiments: {len(all_results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print()
    
    if successful:
        print("[SUCCESS] Successful exports:")
        total_size = 0
        for r in successful:
            size = r.get('file_size_mb', 0)
            total_size += size
            print(f"   {r['base_name']}: {size:.1f} MB")
        print(f"\n   Total size: {total_size:.1f} MB")
    
    if failed:
        print("\n[ERROR] Failed exports:")
        for r in failed:
            error = r.get('error', 'Unknown error')
            print(f"   {r['base_name']}: {error}")
    
    print(f"\nOutput directory: {output_dir}")
    print("="*80)
    
    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    exit(main())

