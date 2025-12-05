#!/usr/bin/env python3
"""
mat2h5 - MATLAB to H5 Conversion Tool
Main entry point for converting MAGAT experiment data to H5 format.

Usage:
    python mat2h5.py
"""

import sys
import subprocess
import shutil
from pathlib import Path
import os

# MAGAT codebase repository (Samuel Lab)
MAGAT_REPO_URL = "https://github.com/SkanataLab/Matlab-Track-Analysis-SkanataLab.git"
MAGAT_REPO_NAME = "Matlab-Track-Analysis-SkanataLab"

def check_matlab_engine():
    """Check if MATLAB Engine for Python is available"""
    try:
        import matlab.engine
        return True
    except ImportError:
        return False

def check_git():
    """Check if git is installed"""
    return shutil.which('git') is not None

def clone_magat_codebase(codebase_path=None):
    """
    Clone the MAGAT codebase using git or provide instructions.
    
    Args:
        codebase_path: Optional path where codebase should be cloned.
                       If None, will prompt user.
    
    Returns:
        Path to cloned codebase, or None if cloning failed
    """
    if not check_git():
        print("\n" + "=" * 70)
        print("Git is not installed, but you need it to clone the MAGAT codebase.")
        print("=" * 70)
        print("\nPlease install git, or clone the repository manually:")
        print(f"\n  Repository: {MAGAT_REPO_URL}")
        print(f"  Clone to: {codebase_path or 'a directory of your choice'}")
        print("\nAfter cloning, run this script again and provide the path.")
        return None
    
    if codebase_path is None:
        default_path = Path.home() / "codebase" / MAGAT_REPO_NAME
        print(f"\nWhere should the MAGAT codebase be cloned?")
        print(f"  [Press Enter for default: {default_path}]")
        user_input = input("  Path: ").strip()
        
        if user_input:
            codebase_path = Path(user_input)
        else:
            codebase_path = default_path
    
    codebase_path = Path(codebase_path)
    
    # If already exists, check if it's a git repo
    if codebase_path.exists():
        if (codebase_path / ".git").exists():
            print(f"\n✓ MAGAT codebase already exists at: {codebase_path}")
            return codebase_path
        else:
            print(f"\n⚠ Directory exists but is not a git repository: {codebase_path}")
            response = input("  Remove and re-clone? [y/N]: ").strip().lower()
            if response == 'y':
                shutil.rmtree(codebase_path)
            else:
                print("  Please provide a different path or remove the directory manually.")
                return None
    
    # Clone the repository
    print(f"\nCloning MAGAT codebase to: {codebase_path}")
    print(f"  Repository: {MAGAT_REPO_URL}")
    print("  This may take a few minutes...")
    
    try:
        codebase_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call([
            'git', 'clone', MAGAT_REPO_URL, str(codebase_path)
        ])
        print(f"\n✓ Successfully cloned MAGAT codebase to: {codebase_path}")
        return codebase_path
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to clone repository. Exit code: {e.returncode}")
        print("\nPlease clone manually:")
        print(f"  git clone {MAGAT_REPO_URL} {codebase_path}")
        return None

def get_magat_codebase_path():
    """
    Get or clone the MAGAT codebase path.
    Prompts user for existing path or offers to clone.
    """
    print("\n" + "=" * 70)
    print("MAGAT Codebase Setup")
    print("=" * 70)
    print("\nThe MAGAT (MATLAB Track Analysis) codebase is required for conversion.")
    print("You can either:")
    print("  1. Provide the path to an existing codebase")
    print("  2. Clone it automatically (requires git)")
    print()
    
    response = input("Do you have the MAGAT codebase already? [y/N]: ").strip().lower()
    
    if response == 'y':
        print("\nEnter the path to the MAGAT codebase:")
        print("  (Should contain folders like @DataManager, @ExperimentSet, etc.)")
        codebase_path = input("  Path: ").strip()
        
        if codebase_path:
            codebase_path = Path(codebase_path)
            if codebase_path.exists() and (codebase_path / "@DataManager").exists():
                print(f"\n✓ Found MAGAT codebase at: {codebase_path}")
                return codebase_path
            else:
                print(f"\n⚠ Path does not appear to be a valid MAGAT codebase.")
                print("  Looking for @DataManager folder...")
                retry = input("  Try again? [y/N]: ").strip().lower()
                if retry == 'y':
                    return get_magat_codebase_path()
                return None
        return None
    else:
        # Offer to clone
        print("\nWould you like to clone the MAGAT codebase automatically?")
        response = input("  [Y/n]: ").strip().lower()
        
        if response != 'n':
            return clone_magat_codebase()
        else:
            print(f"\nPlease clone manually from: {MAGAT_REPO_URL}")
            print("Then run this script again and provide the path.")
            return None

def find_eset_directories(root_path):
    """Find ESET directories in the given root path"""
    root_path = Path(root_path)
    esets = []
    
    # Look for directories that might contain matfiles/ subdirectory
    for item in root_path.iterdir():
        if item.is_dir():
            matfiles_dir = item / "matfiles"
            if matfiles_dir.exists() and list(matfiles_dir.glob("*.mat")):
                esets.append(item)
    
    return esets

def get_data_path():
    """
    Get the path to data directory (root with esets or single eset).
    """
    print("\n" + "=" * 70)
    print("Data Path Selection")
    print("=" * 70)
    print("\nYou can process either:")
    print("  1. A root folder containing multiple ESET directories")
    print("  2. A single ESET directory")
    print()
    
    response = input("Process multiple ESETs or single ESET? [m/S]: ").strip().lower()
    
    if response == 'm':
        print("\nEnter the path to the root folder containing ESET directories:")
        print("  (e.g., /path/to/GMR61@GMR61/)")
        root_path = input("  Path: ").strip()
        
        if root_path:
            root_path = Path(root_path)
            if root_path.exists():
                esets = find_eset_directories(root_path)
                if esets:
                    print(f"\n✓ Found {len(esets)} ESET directories:")
                    for eset in esets[:10]:  # Show first 10
                        print(f"    - {eset.name}")
                    if len(esets) > 10:
                        print(f"    ... and {len(esets) - 10} more")
                    return root_path, 'root'
                else:
                    print(f"\n⚠ No ESET directories found in: {root_path}")
                    print("  (Looking for directories containing 'matfiles/' with .mat files)")
                    return None, None
            else:
                print(f"\n✗ Path does not exist: {root_path}")
                return None, None
    
    # Single ESET
    print("\nEnter the path to a single ESET directory:")
    print("  (Should contain 'matfiles/' subdirectory)")
    eset_path = input("  Path: ").strip()
    
    if eset_path:
        eset_path = Path(eset_path)
        matfiles_dir = eset_path / "matfiles"
        if eset_path.exists():
            if matfiles_dir.exists():
                print(f"\n✓ Found ESET directory: {eset_path.name}")
                return eset_path, 'single'
            else:
                print(f"\n⚠ ESET directory does not contain 'matfiles/' subdirectory")
                print(f"  Path: {eset_path}")
                return None, None
        else:
            print(f"\n✗ Path does not exist: {eset_path}")
            return None, None
    
    return None, None

def get_output_directory():
    """Get output directory for H5 files"""
    print("\n" + "=" * 70)
    print("Output Directory")
    print("=" * 70)
    
    default_output = Path.cwd() / "h5_output"
    print(f"\nWhere should H5 files be saved?")
    print(f"  [Press Enter for default: {default_output}]")
    output_path = input("  Path: ").strip()
    
    if output_path:
        output_dir = Path(output_path)
    else:
        output_dir = default_output
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n✓ Output directory: {output_dir}")
    return output_dir

def run_conversion(data_path, data_type, codebase_path, output_dir):
    """Run the actual conversion using batch_export_esets.py"""
    script_path = Path(__file__).parent / "src" / "scripts" / "conversion" / "batch_export_esets.py"
    
    if not script_path.exists():
        print(f"\n✗ Conversion script not found: {script_path}")
        return False
    
    print("\n" + "=" * 70)
    print("Starting Conversion")
    print("=" * 70)
    print(f"\nData path: {data_path}")
    print(f"Data type: {data_type}")
    print(f"Codebase: {codebase_path}")
    print(f"Output: {output_dir}")
    print()
    
    # Set environment variables for the conversion script
    env = os.environ.copy()
    env['MAGAT_CODEBASE'] = str(codebase_path)
    env['MAT2H5_ROOT'] = str(Path(__file__).parent)
    env['PYTHONPATH'] = str(Path(__file__).parent / "src") + os.pathsep + env.get('PYTHONPATH', '')
    
    # Note: convert_matlab_to_h5.py may need MAGAT Bridge
    # If you have it in a specific location, set MAGAT_BRIDGE_PATH
    # Otherwise, the script will try to find it or use built-in bridge
    
    # Run the batch export script
    try:
        if data_type == 'root':
            # Process root directory with multiple ESETs
            subprocess.check_call([
                sys.executable, str(script_path),
                '--root-dir', str(data_path),
                '--output-dir', str(output_dir),
                '--codebase', str(codebase_path)
            ], env=env)
        else:
            # Process single ESET
            subprocess.check_call([
                sys.executable, str(script_path),
                '--eset-dir', str(data_path),
                '--output-dir', str(output_dir),
                '--codebase', str(codebase_path)
            ], env=env)
        
        print("\n" + "=" * 70)
        print("✓ Conversion complete!")
        print("=" * 70)
        print(f"\nH5 files saved to: {output_dir}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Conversion failed. Exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\nConversion interrupted by user.")
        return False

def main():
    """Main entry point"""
    print("=" * 70)
    print("mat2h5 - MATLAB to H5 Conversion Tool")
    print("=" * 70)
    print("\nThis tool converts MAGAT experiment data to H5 format.")
    print("It requires MATLAB and the MAGAT codebase.")
    
    # Check MATLAB Engine
    if not check_matlab_engine():
        print("\n" + "=" * 70)
        print("MATLAB Engine Not Found")
        print("=" * 70)
        print("\nMATLAB Engine for Python is required.")
        print("Please install it from MATLAB:")
        print("  cd matlabroot/extern/engines/python")
        print("  python setup.py install")
        print("\nOr see: https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html")
        sys.exit(1)
    
    print("\n✓ MATLAB Engine found")
    
    # Get MAGAT codebase
    codebase_path = get_magat_codebase_path()
    if not codebase_path:
        print("\n✗ Cannot proceed without MAGAT codebase.")
        sys.exit(1)
    
    # Get data path
    data_path, data_type = get_data_path()
    if not data_path:
        print("\n✗ Cannot proceed without data path.")
        sys.exit(1)
    
    # Get output directory
    output_dir = get_output_directory()
    
    # Confirm and run
    print("\n" + "=" * 70)
    print("Ready to Convert")
    print("=" * 70)
    print(f"\nData: {data_path}")
    print(f"Codebase: {codebase_path}")
    print(f"Output: {output_dir}")
    print()
    
    response = input("Start conversion? [Y/n]: ").strip().lower()
    if response == 'n':
        print("\nConversion cancelled.")
        sys.exit(0)
    
    # Run conversion
    success = run_conversion(data_path, data_type, codebase_path, output_dir)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

