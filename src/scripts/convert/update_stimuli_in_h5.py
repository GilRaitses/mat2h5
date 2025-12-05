#!/usr/bin/env python3
"""
update_stimuli_in_h5.py - Update stimulus detection in existing H5 files

This script updates the stimulus onset frames in H5 files that were exported
with empty or incorrect stimulus data. It re-detects stimuli from the source
MATLAB experiment files and updates the H5 file.

Usage:
  # Update a single H5 file (requires corresponding .mat file)
  python update_stimuli_in_h5.py --h5 <experiment.h5> --mat <experiment.mat>
  
  # Update all H5 files in a directory (auto-finds corresponding .mat files)
  python update_stimuli_in_h5.py --h5-dir <directory_with_h5_files>
  
  # Update from a genotype directory (finds all H5 files and their .mat sources)
  python update_stimuli_in_h5.py --genotype-dir <genotype_directory>

The script will:
  1. Load the experiment from the .mat file
  2. Detect stimulus onsets using DataManager.detectStimuli()
  3. Update /stimulus/onset_frames and /stimulus/num_cycles in the H5 file

Author: magatfairy
Date: 2025-12-05
"""

import sys
from pathlib import Path
import numpy as np
import h5py
import argparse
from typing import Optional, Tuple, List

# Add parent directories to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from mat2h5.bridge import MAGATBridge


def find_mat_file_for_h5(h5_file: Path) -> Optional[Path]:
    """
    Find the corresponding .mat file for an H5 file.
    
    Looks for .mat files with the same base name in:
    1. Same directory as H5 file
    2. Parent directories (matfiles/, etc.)
    3. Sibling directories
    
    Args:
        h5_file: Path to H5 file
        
    Returns:
        Path to .mat file if found, None otherwise
    """
    base_name = h5_file.stem
    
    # Try same directory
    mat_file = h5_file.parent / f"{base_name}.mat"
    if mat_file.exists():
        return mat_file
    
    # Try matfiles/ subdirectory
    mat_file = h5_file.parent / "matfiles" / f"{base_name}.mat"
    if mat_file.exists():
        return mat_file
    
    # Try parent/matfiles/
    mat_file = h5_file.parent.parent / "matfiles" / f"{base_name}.mat"
    if mat_file.exists():
        return mat_file
    
    # Try searching up to 3 levels up
    for level in range(1, 4):
        search_dir = h5_file.parent
        for _ in range(level):
            search_dir = search_dir.parent
        mat_file = search_dir / "matfiles" / f"{base_name}.mat"
        if mat_file.exists():
            return mat_file
    
    return None


def find_tracks_and_bin_files(mat_file: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Find tracks directory and .bin file for a .mat file.
    
    Args:
        mat_file: Path to .mat file
        
    Returns:
        Tuple of (tracks_dir, bin_file) paths, or (None, None) if not found
    """
    base_name = mat_file.stem
    
    # Try same directory
    tracks_dir = mat_file.parent / f"{base_name} - tracks"
    bin_file = mat_file.parent / f"{base_name}.bin"
    
    if tracks_dir.exists() and bin_file.exists():
        return tracks_dir, bin_file
    
    # Try parent directory
    parent = mat_file.parent.parent
    tracks_dir = parent / f"{base_name} - tracks"
    bin_file = parent / f"{base_name}.bin"
    
    if tracks_dir.exists() and bin_file.exists():
        return tracks_dir, bin_file
    
    return None, None


def update_stimuli_in_h5(h5_file: Path, mat_file: Optional[Path] = None) -> bool:
    """
    Update stimulus data in an H5 file.
    
    Args:
        h5_file: Path to H5 file to update
        mat_file: Path to source .mat file (auto-detected if None)
        
    Returns:
        True if successful, False otherwise
    """
    if not h5_file.exists():
        print(f"[ERROR] H5 file does not exist: {h5_file}")
        return False
    
    # Find .mat file if not provided
    if mat_file is None:
        mat_file = find_mat_file_for_h5(h5_file)
        if mat_file is None:
            print(f"[ERROR] Could not find .mat file for: {h5_file.name}")
            return False
    
    if not mat_file.exists():
        print(f"[ERROR] MAT file does not exist: {mat_file}")
        return False
    
    print(f"\n{'='*70}")
    print(f"Updating stimuli: {h5_file.name}")
    print(f"{'='*70}")
    print(f"  H5: {h5_file}")
    print(f"  MAT: {mat_file}")
    
    # Find tracks and bin files
    tracks_dir, bin_file = find_tracks_and_bin_files(mat_file)
    if tracks_dir is None or bin_file is None:
        print(f"[WARNING] Could not find tracks/bin files, trying without them...")
        tracks_dir = None
        bin_file = None
    
    # Initialize bridge and load experiment
    try:
        bridge = MAGATBridge()
        bridge.load_experiment(mat_file, tracks_dir, bin_file)
        
        # Detect stimuli
        print("  Detecting stimuli...")
        stimuli = bridge.detect_stimuli()
        
        onset_frames = stimuli['onset_frames']
        num_stimuli = stimuli['num_stimuli']
        
        print(f"  Found {num_stimuli} stimulus onsets")
        if num_stimuli > 0:
            print(f"    First: frame {onset_frames[0]}, Last: frame {onset_frames[-1]}")
        
        # Update H5 file
        print("  Updating H5 file...")
        with h5py.File(h5_file, 'r+') as f:
            # Delete existing stimulus group if it exists
            if 'stimulus' in f:
                del f['stimulus']
            
            # Create new stimulus group
            stim_grp = f.create_group('stimulus')
            stim_grp.create_dataset('onset_frames', data=np.array(onset_frames, dtype=np.int32))
            stim_grp.attrs['num_cycles'] = num_stimuli
            
            # Update metadata if it exists
            if 'metadata' in f:
                # Note: We don't update metadata.export_date to preserve original export time
                pass
        
        print(f"  [OK] Updated stimulus data: {num_stimuli} onsets")
        
        bridge.close()
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to update stimuli: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_h5_files_in_dir(directory: Path) -> List[Path]:
    """Find all H5 files in a directory recursively."""
    h5_files = []
    for h5_file in directory.rglob("*.h5"):
        h5_files.append(h5_file)
    return sorted(h5_files)


def main():
    parser = argparse.ArgumentParser(
        description='Update stimulus detection in existing H5 files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update single file
  python update_stimuli_in_h5.py --h5 experiment.h5 --mat experiment.mat
  
  # Update all H5 files in directory (auto-finds .mat files)
  python update_stimuli_in_h5.py --h5-dir exports/
  
  # Update from genotype directory
  python update_stimuli_in_h5.py --genotype-dir D:/rawdata/GMR61@GMR61
        """
    )
    
    parser.add_argument('--h5', type=str, help='Path to single H5 file')
    parser.add_argument('--mat', type=str, help='Path to corresponding .mat file (optional, auto-detected)')
    parser.add_argument('--h5-dir', type=str, help='Directory containing H5 files to update')
    parser.add_argument('--genotype-dir', type=str, help='Genotype directory with ESET folders')
    
    args = parser.parse_args()
    
    if not any([args.h5, args.h5_dir, args.genotype_dir]):
        parser.print_help()
        return 1
    
    h5_files = []
    
    if args.h5:
        h5_files.append(Path(args.h5))
        mat_file = Path(args.mat) if args.mat else None
        success = update_stimuli_in_h5(h5_files[0], mat_file)
        return 0 if success else 1
    
    elif args.h5_dir:
        h5_dir = Path(args.h5_dir)
        h5_files = find_h5_files_in_dir(h5_dir)
        print(f"Found {len(h5_files)} H5 files in {h5_dir}")
    
    elif args.genotype_dir:
        genotype_dir = Path(args.genotype_dir)
        # Look for H5 files in exports or in the genotype directory itself
        exports_dir = Path(__file__).parent.parent.parent.parent / "exports"
        if exports_dir.exists():
            h5_files = [f for f in exports_dir.glob("*.h5") if genotype_dir.name in f.stem]
        else:
            h5_files = find_h5_files_in_dir(genotype_dir)
        print(f"Found {len(h5_files)} H5 files for genotype {genotype_dir.name}")
    
    if not h5_files:
        print("[ERROR] No H5 files found")
        return 1
    
    # Process all files
    print(f"\nProcessing {len(h5_files)} H5 files...")
    success_count = 0
    fail_count = 0
    
    for i, h5_file in enumerate(h5_files, 1):
        print(f"\n[{i}/{len(h5_files)}] {h5_file.name}")
        if update_stimuli_in_h5(h5_file):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Total:   {len(h5_files)}")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

