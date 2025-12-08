#!/usr/bin/env python3
"""
check_stimuli_status.py - Check which H5 files have empty or missing stimulus data

Quick script to identify which H5 files need the stimulus detection fix.
"""

import sys
from pathlib import Path
import h5py
import argparse

def check_stimuli_status(h5_file: Path) -> dict:
    """Check if an H5 file has valid stimulus data."""
    result = {
        'file': h5_file.name,
        'has_stimulus_group': False,
        'num_cycles': 0,
        'onset_frames_count': 0,
        'needs_fix': False
    }
    
    try:
        with h5py.File(h5_file, 'r') as f:
            if 'stimulus' in f:
                result['has_stimulus_group'] = True
                stim_grp = f['stimulus']
                
                if 'num_cycles' in stim_grp.attrs:
                    result['num_cycles'] = int(stim_grp.attrs['num_cycles'])
                
                if 'onset_frames' in stim_grp:
                    onset_frames = stim_grp['onset_frames']
                    result['onset_frames_count'] = len(onset_frames) if onset_frames.size > 0 else 0
                
                # Needs fix if num_cycles is 0 or onset_frames is empty
                if result['num_cycles'] == 0 or result['onset_frames_count'] == 0:
                    result['needs_fix'] = True
            else:
                result['needs_fix'] = True
    except Exception as e:
        result['error'] = str(e)
        result['needs_fix'] = True
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Check stimulus status in H5 files')
    parser.add_argument('--h5-dir', type=str, required=True, help='Directory with H5 files')
    parser.add_argument('--list-only', action='store_true', help='Only list files that need fixing')
    
    args = parser.parse_args()
    
    h5_dir = Path(args.h5_dir)
    if not h5_dir.exists():
        print(f"[ERROR] Directory does not exist: {h5_dir}")
        return 1
    
    h5_files = sorted(h5_dir.glob("*.h5"))
    
    if not h5_files:
        print(f"[ERROR] No H5 files found in {h5_dir}")
        return 1
    
    print(f"Checking {len(h5_files)} H5 files...\n")
    
    needs_fix = []
    has_stimuli = []
    
    for h5_file in h5_files:
        status = check_stimuli_status(h5_file)
        
        if status['needs_fix']:
            needs_fix.append((h5_file, status))
        else:
            has_stimuli.append((h5_file, status))
    
    if args.list_only:
        print("Files that need stimulus detection fix:")
        print("=" * 70)
        for h5_file, status in needs_fix:
            print(f"  {h5_file.name}")
    else:
        print("=" * 70)
        print("STIMULUS STATUS CHECK")
        print("=" * 70)
        
        print(f"\n[OK] Files with valid stimulus data: {len(has_stimuli)}")
        for h5_file, status in has_stimuli:
            print(f"  {h5_file.name}: {status['num_cycles']} cycles, {status['onset_frames_count']} onset frames")
        
        print(f"\n[NEEDS FIX] Files that need fixing: {len(needs_fix)}")
        for h5_file, status in needs_fix:
            print(f"  {h5_file.name}: cycles={status['num_cycles']}, frames={status['onset_frames_count']}")
    
    if needs_fix:
        print(f"\n{'='*70}")
        print("To fix these files, run:")
        print(f"  python src/scripts/convert/update_stimuli_in_h5.py --h5-dir {h5_dir}")
        print(f"\nOr fix individual files:")
        for h5_file, _ in needs_fix:
            print(f"  python src/scripts/convert/update_stimuli_in_h5.py --h5 {h5_file}")
    
    return 0 if not needs_fix else 1

if __name__ == "__main__":
    sys.exit(main())

