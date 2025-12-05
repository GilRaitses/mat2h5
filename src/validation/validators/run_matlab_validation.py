#!/usr/bin/env python3
"""
run_matlab_validation.py - Run MATLAB validation script via MATLAB engine

This script runs load_experiment_and_compute.m using the MATLAB engine for Python,
avoiding the need to open MATLAB GUI.
"""

import matlab.engine
import sys
from pathlib import Path


def main():
    print("=" * 60)
    print("Running MATLAB Validation via MATLAB Engine")
    print("=" * 60)
    print()
    
    # Get the reference script directory
    script_dir = Path(__file__).parent.parent / "reference"
    
    print(f"Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    
    try:
        # Add the matlab validation directory to path
        print(f"Adding path: {script_dir}")
        eng.addpath(str(script_dir), nargout=0)
        
        # Add MAGAT/Track Analysis codebases needed for ExperimentSet, Track classes, etc.
        print("Adding MAGAT codebases to path...")
        
        # MirnaLab Track Analysis (primary)
        eng.addpath(eng.genpath(r"D:\Matlab-Track-Analysis-MirnaLab"), nargout=0)
        print("  Added: D:\\Matlab-Track-Analysis-MirnaLab")
        
        # SkanataLab Track Analysis
        eng.addpath(eng.genpath(r"d:\magniphyq\codebase\Matlab-Track-Analysis-SkanataLab"), nargout=0)
        print("  Added: d:\\magniphyq\\codebase\\Matlab-Track-Analysis-SkanataLab")
        
        # Mechanosensation scripts (for custom classes)
        eng.addpath(r"D:\mechanosensation\scripts\2025-10-16", nargout=0)
        print("  Added: D:\\mechanosensation\\scripts\\2025-10-16")
        
        print()
        print("Running load_experiment_and_compute.m...")
        print("-" * 60)
        
        # Run the script
        eng.load_experiment_and_compute(nargout=0)
        
        print("-" * 60)
        print()
        print("MATLAB validation complete!")
        print()
        print("Output files should be in:")
        print(f"  {script_dir.parent / 'test_data'}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        print()
        print("Closing MATLAB engine...")
        eng.quit()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

