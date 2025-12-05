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
import json
import logging
from pathlib import Path
import time
import re
from typing import Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mat2h5.progress import ColoredProgress, print_red_header, print_white_header, print_blue_header
from mat2h5.config import get_magat_codebase

# Script paths (relative to this file)
CONVERT_SCRIPT = Path(__file__).parent / "convert_matlab_to_h5.py"
MAT2H5_ROOT = Path(__file__).parent.parent.parent.parent


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


def export_experiment(file_info: Dict, output_dir: Path, codebase_path: Path = None, 
                     skip_existing: bool = False, dry_run: bool = False, 
                     logger: Optional[logging.Logger] = None) -> Dict:
    """Export a single experiment using convert_matlab_to_h5.py"""
    base_name = file_info['base_name']
    
    # Output filename matches base_name with .h5 extension
    output_file = output_dir / f"{base_name}.h5"
    
    # Check if file exists and skip if requested
    if skip_existing and output_file.exists():
        if logger:
            logger.info(f"Skipping {base_name} - file already exists: {output_file}")
        return {
            'success': True,
            'output_file': output_file,
            'file_size_mb': output_file.stat().st_size / (1024 * 1024),
            'time_min': 0,
            'base_name': base_name,
            'timestamp': file_info['timestamp'],
            'skipped': True
        }
    
    if dry_run:
        print(f"  [DRY-RUN] Would convert: {base_name} -> {output_file.name}")
        return {
            'success': True,
            'output_file': output_file,
            'file_size_mb': 0,
            'time_min': 0,
            'base_name': base_name,
            'timestamp': file_info['timestamp'],
            'dry_run': True
        }
    
    if logger:
        logger.info(f"Exporting {base_name} -> {output_file.name}")
    
    print(f"\n  Exporting: {base_name}")
    print(f"    MAT: {file_info['mat_file'].name}")
    print(f"    Output: {output_file.name}")
    
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


def load_progress(output_dir: Path) -> set:
    """Load progress tracking file"""
    progress_file = output_dir / ".progress.json"
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return set(data.get('completed', []))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_progress(output_dir: Path, completed: List[str]):
    """Save progress tracking file"""
    progress_file = output_dir / ".progress.json"
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, 'w') as f:
        json.dump({'completed': completed}, f, indent=2)


def process_genotype(root_dir: Path, output_dir: Path, codebase_path: Path = None,
                    skip_existing: bool = False, resume: bool = False, dry_run: bool = False,
                    logger: Optional[logging.Logger] = None) -> List[Dict]:
    """
    Process all ESET folders in a root directory.
    
    Args:
        root_dir: Path to root directory containing ESET folders
        output_dir: Path to output directory for H5 files
        codebase_path: Path to MAGAT codebase
        skip_existing: Skip files that already exist
        resume: Resume from previous progress
        dry_run: Preview mode, don't actually convert
        logger: Optional logger instance
    
    Returns:
        List of export results
    """
    # RED SECTION: Beginning - Setup and discovery
    print_red_header(f"Processing Root Directory: {root_dir.name}")
    
    # Find all ESET folders
    eset_folders = [d for d in root_dir.iterdir() if d.is_dir() and (d / "matfiles").exists()]
    
    if not eset_folders:
        print(f"[WARNING] No ESET folders found in {root_dir.name}")
        return []
    
    print(f"Found {len(eset_folders)} ESET folders")
    
    # Discover all experiments
    all_experiments = []
    for eset_dir in sorted(eset_folders):
        experiments = detect_experiments_in_eset(eset_dir)
        for exp in experiments:
            exp['eset_name'] = eset_dir.name
            all_experiments.append(exp)
    
    total_experiments = len(all_experiments)
    print(f"Found {total_experiments} total experiments")
    
    # Load progress if resuming
    completed = set()
    if resume:
        completed = load_progress(output_dir)
        print(f"Resuming: {len(completed)} already completed")
    
    # Initialize progress tracker
    progress = ColoredProgress(total_experiments)
    
    # WHITE SECTION: Middle - Processing
    print_white_header("Converting Experiments")
    
    all_results = []
    completed_list = list(completed)
    
    for exp_idx, file_info in enumerate(all_experiments, 1):
        base_name = file_info['base_name']
        
        # Skip if already completed and resuming
        if resume and base_name in completed:
            progress.update(1, f"Skipped (already done): {base_name}")
            continue
        
        # Update progress
        progress.update(0, f"Processing: {base_name}")
        
        # Export experiment
        result = export_experiment(file_info, output_dir, codebase_path, 
                                  skip_existing, dry_run, logger)
        all_results.append(result)
        
        # Update progress
        if result.get('success'):
            completed_list.append(base_name)
            if resume:
                save_progress(output_dir, completed_list)
            progress.update(1, f"✓ {base_name}")
        else:
            progress.update(1, f"✗ {base_name} failed")
    
    progress.finish("All experiments processed")
    
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
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip files that already exist')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from previous progress')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be converted without actually converting')
    parser.add_argument('--log-file', type=str, default=None,
                       help='Log file path (default: output_dir/conversion.log)')
    parser.add_argument('--validate', action='store_true',
                       help='Run schema validation after conversion')
    
    args = parser.parse_args()
    
    # Verify dependencies
    if not CONVERT_SCRIPT.exists():
        print(f"[ERROR] Convert script not found: {CONVERT_SCRIPT}")
        return 1
    
    # Set output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    log_file = args.log_file or (output_dir / "conversion.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Get codebase path (from config, env, or arg)
    codebase_path = args.codebase or get_magat_codebase() or os.environ.get('MAGAT_CODEBASE')
    
    if not codebase_path:
        # Try to clone automatically
        repo_parent = Path(__file__).parent.parent.parent.parent.parent
        default_codebase_path = repo_parent / "MAGATAnalyzer-Matlab-Analysis"
        
        if default_codebase_path.exists():
            codebase_path = default_codebase_path
            logger.info(f"Found MAGAT codebase at default location: {codebase_path}")
        else:
            logger.warning("No MAGAT codebase specified. Set --codebase or MAGAT_CODEBASE env var.")
            print("\n" + "="*80)
            print("MAGAT Codebase Required")
            print("="*80)
            print("\nThe MAGAT codebase is required for conversion.")
            print(f"Expected location: {default_codebase_path}")
            print("\nOptions:")
            print("  1. Clone automatically: Press Enter")
            print("  2. Provide path: Enter path to existing codebase")
            print()
            
            response = input("Action [Enter to clone, or path]: ").strip()
            
            if not response:
                # Clone automatically (if git is available)
                import subprocess
                import shutil
                MAGAT_REPO_URL = "https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git"
                
                if not shutil.which('git'):
                    print("\n✗ Git is not installed. Cannot clone automatically.")
                    print("\nPlease either:")
                    print("  1. Install git and try again")
                    print("  2. Clone manually: git clone https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git")
                    print("  3. Provide path to existing codebase")
                    return 1
                
                print(f"\nCloning MAGAT codebase to: {default_codebase_path}")
                try:
                    default_codebase_path.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.check_call([
                        'git', 'clone', MAGAT_REPO_URL, str(default_codebase_path)
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    codebase_path = default_codebase_path
                    logger.info(f"Cloned MAGAT codebase to: {codebase_path}")
                except subprocess.CalledProcessError as e:
                    print(f"\n✗ Failed to clone. Exit code: {e.returncode}")
                    print("\nPlease either:")
                    print("  1. Check your internet connection and try again")
                    print("  2. Clone manually: git clone https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git")
                    print("  3. Provide path to existing codebase")
                    return 1
            else:
                codebase_path = Path(response).expanduser()
                if not codebase_path.exists():
                    print(f"✗ Path does not exist: {codebase_path}")
                    return 1
    
    if codebase_path:
        codebase_path = Path(codebase_path)
        os.environ['MAGAT_CODEBASE'] = str(codebase_path)
        logger.info(f"Using MAGAT codebase: {codebase_path}")
    
    if not codebase_path:
        print("[ERROR] MAGAT codebase path required")
        print("  Set --codebase argument, MAGAT_CODEBASE env var, or use: mat2h5 config set magat_codebase /path")
        return 1
    
    if args.dry_run:
        print("="*80)
        print("DRY-RUN MODE: Preview Only")
        print("="*80)
    else:
        print("="*80)
        print("BATCH EXPORT: MATLAB TO H5 CONVERSION")
        print("="*80)
    print(f"Output directory: {output_dir}")
    print(f"Convert script: {CONVERT_SCRIPT}")
    print(f"MAGAT codebase: {codebase_path}")
    if args.skip_existing:
        print("Skip existing: Enabled")
    if args.resume:
        print("Resume: Enabled")
    print()
    
    # Process ESETs
    if args.eset_dir:
        # Process single ESET
        eset_dir = Path(args.eset_dir)
        if not eset_dir.exists():
            print(f"[ERROR] ESET directory not found: {eset_dir}")
            return 1
        
        print_red_header(f"Processing ESET: {eset_dir.name}")
        experiments = detect_experiments_in_eset(eset_dir)
        if not experiments:
            print(f"[ERROR] No complete experiments found in {eset_dir}")
            return 1
        
        print(f"Found {len(experiments)} experiments")
        
        # Use progress tracker for single ESET too
        print_white_header("Converting Experiments")
        progress = ColoredProgress(len(experiments))
        all_results = []
        
        for exp_idx, file_info in enumerate(experiments, 1):
            progress.update(0, f"Processing: {file_info['base_name']}")
            result = export_experiment(file_info, output_dir, codebase_path,
                                     args.skip_existing, args.dry_run, logger)
            all_results.append(result)
            
            if result.get('success'):
                progress.update(1, f"✓ {file_info['base_name']}")
            else:
                progress.update(1, f"✗ {file_info['base_name']} failed")
        
        progress.finish()
    elif args.root_dir:
        # Process root directory with multiple ESETs
        root_dir = Path(args.root_dir)
        if not root_dir.exists():
            print(f"[ERROR] Root directory not found: {root_dir}")
            return 1
        
        all_results = process_genotype(root_dir, output_dir, codebase_path,
                                     args.skip_existing, args.resume, args.dry_run, logger)
    else:
        print("[ERROR] Must specify either --root-dir or --eset-dir")
        return 1
    
    # BLUE SECTION: End - Summary and validation
    print_blue_header("Finalizing")
    
    successful = [r for r in all_results if r.get('success')]
    failed = [r for r in all_results if not r.get('success')]
    skipped = [r for r in all_results if r.get('skipped')]
    
    print(f"\nTotal experiments: {len(all_results)}")
    print(f"Successful: {len(successful)}")
    if skipped:
        print(f"Skipped (already exist): {len(skipped)}")
    print(f"Failed: {len(failed)}")
    print()
    
    if successful:
        print("Successful exports:")
        total_size = 0
        for r in successful[:10]:  # Show first 10
            size = r.get('file_size_mb', 0)
            total_size += size
            status = "(skipped)" if r.get('skipped') else "(converted)"
            print(f"  ✓ {r['base_name']} {status} - {size:.1f} MB")
        if len(successful) > 10:
            print(f"  ... and {len(successful) - 10} more")
        print(f"\n  Total size: {total_size:.1f} MB")
    
    if failed:
        print("\nFailed exports:")
        for r in failed:
            error = r.get('error', 'Unknown error')
            print(f"  ✗ {r['base_name']}: {error}")
    
    print(f"\nOutput directory: {output_dir}")
    if logger:
        logger.info(f"Batch export complete: {len(successful)}/{len(all_results)} successful")
    print("="*80)
    
    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    exit(main())

