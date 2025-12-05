#!/usr/bin/env python3
"""
Utility to unlock and optionally delete locked H5 files.

Handles Windows file locking issues (Error 33) by:
1. Attempting to close Python processes that might have the file open
2. Attempting to close MATLAB processes
3. Providing instructions for manual deletion if needed
"""

import sys
import os
import subprocess
from pathlib import Path
import h5py


def check_file_integrity(file_path: Path) -> dict:
    """Check if H5 file is valid and complete"""
    result = {
        'exists': False,
        'valid': False,
        'complete': False,
        'size_mb': 0,
        'error': None
    }
    
    if not file_path.exists():
        result['error'] = 'File does not exist'
        return result
    
    result['exists'] = True
    result['size_mb'] = file_path.stat().st_size / (1024 * 1024)
    
    try:
        with h5py.File(file_path, 'r') as f:
            # Check for required root keys
            required_keys = ['eti', 'tracks', 'metadata', 'global_quantities']
            has_all_keys = all(key in f for key in required_keys)
            
            if has_all_keys:
                # Check ETI
                eti_shape = f['eti'].shape if 'eti' in f else None
                num_tracks = len(list(f['tracks'].keys())) if 'tracks' in f else 0
                
                result['valid'] = True
                result['complete'] = (
                    eti_shape is not None and len(eti_shape) > 0 and
                    num_tracks > 0 and
                    'has_eti' in f['metadata'].attrs and
                    f['metadata'].attrs['has_eti']
                )
                
                return {
                    **result,
                    'eti_shape': eti_shape,
                    'num_tracks': num_tracks,
                    'metadata': dict(f['metadata'].attrs)
                }
            else:
                result['error'] = f'Missing required keys. Found: {list(f.keys())}'
                return result
                
    except Exception as e:
        result['error'] = str(e)
        return result


def try_delete_file(file_path: Path) -> tuple[bool, str]:
    """Try to delete a file, handling locking errors"""
    try:
        # First, try to close any Python processes that might have it open
        # (This is a best-effort attempt)
        
        # Try to delete
        file_path.unlink()
        return True, "File deleted successfully"
    except PermissionError as e:
        return False, f"Permission denied: {e}"
    except OSError as e:
        if e.winerror == 32:  # File is being used by another process
            return False, f"File is locked (Error 32): Another process is using this file"
        elif e.winerror == 33:  # Cannot access file
            return False, f"File is locked (Error 33): Cannot access file"
        else:
            return False, f"OSError: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Unlock and optionally delete locked H5 files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check file integrity
  python unlock_h5_file.py --file "path/to/file.h5" --check
  
  # Delete locked file (if corrupted)
  python unlock_h5_file.py --file "path/to/file.h5" --delete
  
  # Force delete (attempts to close processes first)
  python unlock_h5_file.py --file "path/to/file.h5" --force-delete
        """
    )
    parser.add_argument('--file', type=str, required=True,
                       help='Path to H5 file')
    parser.add_argument('--check', action='store_true',
                       help='Check file integrity only')
    parser.add_argument('--delete', action='store_true',
                       help='Delete file if it can be unlocked')
    parser.add_argument('--force-delete', action='store_true',
                       help='Force delete (attempts to close processes)')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"[ERROR] File does not exist: {file_path}")
        return 1
    
    print("="*80)
    print("H5 FILE UNLOCK UTILITY")
    print("="*80)
    print(f"File: {file_path.name}")
    print(f"Path: {file_path}")
    print()
    
    # Check integrity
    print("Checking file integrity...")
    integrity = check_file_integrity(file_path)
    
    print(f"  Exists: {integrity['exists']}")
    print(f"  Size: {integrity['size_mb']:.1f} MB")
    print(f"  Valid: {integrity['valid']}")
    print(f"  Complete: {integrity['complete']}")
    
    if integrity['error']:
        print(f"  Error: {integrity['error']}")
    
    if integrity.get('eti_shape'):
        print(f"  ETI shape: {integrity['eti_shape']}")
    if integrity.get('num_tracks'):
        print(f"  Tracks: {integrity['num_tracks']}")
    if integrity.get('metadata'):
        print(f"  Metadata: {integrity['metadata']}")
    
    print()
    
    if args.check:
        if integrity['valid'] and integrity['complete']:
            print("[OK] File is valid and complete")
            return 0
        else:
            print("[WARNING] File may be corrupted or incomplete")
            return 1
    
    # Try to delete if requested
    if args.delete or args.force_delete:
        if integrity['valid'] and integrity['complete']:
            print("[WARNING] File appears to be valid and complete!")
            response = input("Are you sure you want to delete it? (yes/no): ")
            if response.lower() != 'yes':
                print("Deletion cancelled")
                return 0
        
        if args.force_delete:
            print("\nAttempting to close processes that might have the file open...")
            print("(This is a best-effort attempt - you may need to close programs manually)")
            
            # List processes
            try:
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                    capture_output=True,
                    text=True
                )
                if 'python.exe' in result.stdout:
                    print("  Found Python processes - you may need to close them manually")
                
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq MATLAB.exe', '/FO', 'CSV'],
                    capture_output=True,
                    text=True
                )
                if 'MATLAB.exe' in result.stdout:
                    print("  Found MATLAB processes - you may need to close them manually")
            except:
                pass
        
        print(f"\nAttempting to delete: {file_path.name}")
        success, message = try_delete_file(file_path)
        
        if success:
            print(f"[SUCCESS] {message}")
            return 0
        else:
            print(f"[ERROR] {message}")
            print()
            print("Troubleshooting steps:")
            print("1. Close any programs that might have the file open:")
            print("   - HDFView")
            print("   - MATLAB")
            print("   - Python scripts")
            print("   - File Explorer (if previewing)")
            print("2. Try deleting manually from File Explorer")
            print("3. If still locked, restart your computer")
            print("4. As a last resort, use Process Explorer to find the locking process")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())









