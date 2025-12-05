#!/usr/bin/env python3
"""
mat2h5 - MATLAB to H5 Conversion Tool
CLI entry point for converting MAGAT experiment data to H5 format.

Usage:
    mat2h5 convert batch --root-dir /path/to/data --output /path/to/output --codebase /path/to/magat
    mat2h5 convert single --mat file.mat --output file.h5 --codebase /path/to/magat
    mat2h5 analyze engineer --h5 file.h5
    mat2h5 validate schema --h5 file.h5
"""

import sys
import argparse
import re
from pathlib import Path
from typing import Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# MAGAT codebase repository (Samuel Lab)
MAGAT_REPO_URL = "https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git"
MAGAT_REPO_NAME = "MAGATAnalyzer-Matlab-Analysis"


def check_matlab_engine():
    """Check if MATLAB Engine for Python is available"""
    try:
        import matlab.engine
        return True
    except ImportError:
        return False


def detect_data_type(path: Path) -> Tuple[str, Optional[Path]]:
    """
    Auto-detect the type of data at the given path.
    
    Returns:
        Tuple of (data_type, detected_path) where:
        - data_type: 'genotype', 'eset', 'experiment', 'track', or 'unknown'
        - detected_path: Path to the detected data (may differ from input)
    """
    path = Path(path).resolve()
    
    if not path.exists():
        return 'unknown', None
    
    # Check if it's a file
    if path.is_file():
        # Check if it's a .mat file (experiment)
        if path.suffix == '.mat':
            return 'experiment', path
        # Check if it's a track file
        if path.suffix == '.mat' and 'track' in path.name.lower():
            return 'track', path
        return 'unknown', path
    
    # It's a directory - check structure
    # 1. Check if it's a genotype (root with multiple ESET folders)
    eset_folders = [d for d in path.iterdir() if d.is_dir() and (d / "matfiles").exists()]
    if len(eset_folders) > 1:
        return 'genotype', path
    
    # 2. Check if it's a single ESET (has matfiles/ subdirectory)
    if (path / "matfiles").exists():
        return 'eset', path
    
    # 3. Check if it's a tracks directory (contains track*.mat files)
    track_files = list(path.glob("track*.mat"))
    if track_files:
        return 'track', path
    
    # 4. Check if parent is an ESET and this is matfiles/
    if path.name == "matfiles" and (path.parent / "matfiles").exists():
        # Check if there's a single .mat file
        mat_files = list(path.glob("*.mat"))
        if len(mat_files) == 1:
            return 'experiment', mat_files[0]
        return 'eset', path.parent
    
    # 5. Check if it contains a single .mat file (experiment)
    mat_files = list(path.glob("*.mat"))
    if len(mat_files) == 1:
        return 'experiment', mat_files[0]
    
    return 'unknown', path


def create_parser():
    """Create the main argument parser with subcommands"""
    parser = argparse.ArgumentParser(
        description="MATLAB to H5 Conversion Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect and convert (drag folder into terminal, press Enter)
  mat2h5 convert auto
  
  # Convert all ESETs in a directory
  mat2h5 convert batch --root-dir /data/GMR61@GMR61 --output /h5_output --codebase /path/to/magat
  
  # Convert a single experiment
  mat2h5 convert single --mat experiment.mat --output experiment.h5 --codebase /path/to/magat
  
  # Analyze H5 file
  mat2h5 analyze engineer --h5 file.h5
  
  # Validate H5 schema
  mat2h5 validate schema --h5 file.h5
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert subcommands
    convert_parser = subparsers.add_parser('convert', help='Conversion commands')
    convert_subparsers = convert_parser.add_subparsers(dest='subcommand', help='Conversion subcommands')
    
    # convert batch
    batch_parser = convert_subparsers.add_parser('batch', help='Batch convert all ESETs in a directory')
    batch_parser.add_argument('--root-dir', required=True, help='Root directory containing ESET folders')
    batch_parser.add_argument('--output-dir', required=True, help='Output directory for H5 files')
    batch_parser.add_argument('--codebase', required=True, help='Path to MAGAT codebase')
    
    # convert single
    single_parser = convert_subparsers.add_parser('single', help='Convert a single experiment')
    single_parser.add_argument('--mat', required=True, help='Path to .mat experiment file')
    single_parser.add_argument('--tracks', help='Path to tracks directory')
    single_parser.add_argument('--bin', help='Path to .bin file')
    single_parser.add_argument('--output', required=True, help='Output H5 file path')
    single_parser.add_argument('--codebase', required=True, help='Path to MAGAT codebase')
    
    # convert append-camcal
    camcal_parser = convert_subparsers.add_parser('append-camcal', help='Append camera calibration to H5 files')
    camcal_parser.add_argument('--eset-dir', required=True, help='ESET directory containing H5 files')
    
    # convert unlock
    unlock_parser = convert_subparsers.add_parser('unlock', help='Unlock a locked H5 file')
    unlock_parser.add_argument('--file', required=True, help='Path to H5 file')
    unlock_parser.add_argument('--force-delete', action='store_true', help='Force delete lock file')
    
    # convert auto (drag-and-drop friendly)
    auto_parser = convert_subparsers.add_parser('auto', help='Auto-detect and convert (drag folder into terminal, press Enter)')
    auto_parser.add_argument('path', nargs='?', help='Path to data (can drag-and-drop folder here)')
    auto_parser.add_argument('--output-dir', help='Output directory (default: ./h5_output)')
    auto_parser.add_argument('--codebase', help='Path to MAGAT codebase (or set MAGAT_CODEBASE env var)')
    
    # Analyze subcommands
    analyze_parser = subparsers.add_parser('analyze', help='Analysis commands')
    analyze_subparsers = analyze_parser.add_subparsers(dest='subcommand', help='Analysis subcommands')
    
    # analyze engineer
    engineer_parser = analyze_subparsers.add_parser('engineer', help='Engineer data from H5 file')
    engineer_parser.add_argument('--h5', required=True, help='Path to H5 file')
    
    # analyze dataset
    dataset_parser = analyze_subparsers.add_parser('dataset', help='Engineer dataset from H5 file')
    dataset_parser.add_argument('--h5', required=True, help='Path to H5 file')
    
    # Validate subcommands
    validate_parser = subparsers.add_parser('validate', help='Validation commands')
    validate_subparsers = validate_parser.add_subparsers(dest='subcommand', help='Validation subcommands')
    
    # validate schema
    schema_parser = validate_subparsers.add_parser('schema', help='Validate H5 file schema')
    schema_parser.add_argument('--h5', required=True, help='Path to H5 file')
    schema_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # validate integrity
    integrity_parser = validate_subparsers.add_parser('integrity', help='Compare H5 data integrity with MATLAB source')
    integrity_parser.add_argument('--mat', required=True, help='Path to MATLAB .mat file')
    integrity_parser.add_argument('--h5', required=True, help='Path to H5 file')
    integrity_parser.add_argument('--tracks', nargs='+', type=int, help='Specific track numbers to compare')
    integrity_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # validate full
    full_parser = validate_subparsers.add_parser('full', help='Run full validation suite')
    full_parser.add_argument('--base-dir', required=True, help='Base directory containing ESETs')
    full_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    full_parser.add_argument('--output', help='Save results to JSON file')
    
    return parser


def handle_convert_batch(args):
    """Handle convert batch command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "scripts" / "convert" / "batch_export_esets.py"
    spec = importlib.util.spec_from_file_location("batch_export_esets", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['batch_export_esets.py', '--root-dir', args.root_dir, 
                '--output-dir', args.output_dir, '--codebase', args.codebase]
    spec.loader.exec_module(module)
    return module.main()


def handle_convert_single(args):
    """Handle convert single command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "scripts" / "convert" / "convert_matlab_to_h5.py"
    spec = importlib.util.spec_from_file_location("convert_matlab_to_h5", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['convert_matlab_to_h5.py', '--mat', args.mat, 
                '--output', args.output, '--codebase', args.codebase]
    if args.tracks:
        sys.argv.extend(['--tracks', args.tracks])
    if args.bin:
        sys.argv.extend(['--bin', args.bin])
    spec.loader.exec_module(module)
    return module.main()


def handle_convert_append_camcal(args):
    """Handle convert append-camcal command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "scripts" / "convert" / "append_camcal_to_h5.py"
    spec = importlib.util.spec_from_file_location("append_camcal_to_h5", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['append_camcal_to_h5.py', '--eset-dir', args.eset_dir]
    spec.loader.exec_module(module)
    return module.main()


def handle_convert_unlock(args):
    """Handle convert unlock command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "scripts" / "convert" / "unlock_h5_file.py"
    spec = importlib.util.spec_from_file_location("unlock_h5_file", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['unlock_h5_file.py', '--file', args.file]
    if args.force_delete:
        sys.argv.append('--force-delete')
    spec.loader.exec_module(module)
    return module.main()


def handle_convert_auto(args):
    """Handle convert auto command - auto-detect data type and process"""
    import os
    
    # Get path from argument or prompt
    if args.path:
        input_path = Path(args.path).expanduser()
    else:
        print("\n" + "=" * 70)
        print("Drag-and-Drop Auto Conversion")
        print("=" * 70)
        print("\nDrag a folder into this terminal and press Enter,")
        print("or type a path and press Enter:")
        user_input = input("  Path: ").strip()
        if not user_input:
            print("No path provided. Exiting.")
            return 1
        input_path = Path(user_input.strip().strip("'\"")).expanduser()
    
    # Auto-detect data type
    print(f"\nAnalyzing: {input_path}")
    data_type, detected_path = detect_data_type(input_path)
    
    if data_type == 'unknown' or detected_path is None:
        print(f"\n✗ Could not detect data type for: {input_path}")
        print("  Expected: genotype directory, ESET folder, experiment file, or tracks directory")
        return 1
    
    print(f"✓ Detected: {data_type}")
    print(f"  Path: {detected_path}")
    
    # Get codebase path
    codebase_path = args.codebase or os.environ.get('MAGAT_CODEBASE')
    if not codebase_path:
        print("\n" + "=" * 70)
        print("MAGAT Codebase Required")
        print("=" * 70)
        print("\nEnter the path to the MAGAT codebase:")
        print("  (Or set MAGAT_CODEBASE environment variable)")
        codebase_input = input("  Path: ").strip()
        if codebase_input:
            codebase_path = Path(codebase_input).expanduser()
        else:
            print("✗ MAGAT codebase path required")
            return 1
    
    codebase_path = Path(codebase_path)
    if not codebase_path.exists():
        print(f"✗ MAGAT codebase not found: {codebase_path}")
        return 1
    
    # Get output directory - default to repo's exports folder
    repo_root = Path(__file__).parent
    default_output = repo_root / "exports"
    
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
    else:
        # Use repo's exports folder as default
        output_dir = default_output
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n✓ Output directory: {output_dir}")
    
    # Route to appropriate handler based on detected type
    print(f"\n" + "=" * 70)
    print(f"Processing {data_type}: {detected_path.name}")
    print("=" * 70)
    
    if data_type == 'genotype':
        # Process as genotype (batch)
        return handle_convert_batch(type('args', (), {
            'root_dir': str(detected_path),
            'output_dir': str(output_dir),
            'codebase': str(codebase_path)
        })())
    
    elif data_type == 'eset':
        # Process as single ESET
        import importlib.util
        script_path = Path(__file__).parent / "src" / "scripts" / "convert" / "batch_export_esets.py"
        spec = importlib.util.spec_from_file_location("batch_export_esets", script_path)
        module = importlib.util.module_from_spec(spec)
        sys.argv = ['batch_export_esets.py', '--eset-dir', str(detected_path),
                    '--output-dir', str(output_dir), '--codebase', str(codebase_path)]
        spec.loader.exec_module(module)
        return module.main()
    
    elif data_type == 'experiment':
        # Process as single experiment
        # Need to find tracks and bin files
        mat_file = detected_path
        eset_dir = mat_file.parent.parent if mat_file.parent.name == "matfiles" else mat_file.parent
        
        # Try to find tracks directory
        timestamp_match = re.search(r'_(\d{12})\.mat$', mat_file.name)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            genotype_match = re.search(r'^([A-Za-z0-9]+@[A-Za-z0-9]+)_', mat_file.name)
            if genotype_match:
                genotype = genotype_match.group(1)
                tracks_dir = mat_file.parent / f"{genotype}_{timestamp} - tracks"
                bin_file = eset_dir / f"{mat_file.stem}.bin"
                
                if tracks_dir.exists() and bin_file.exists():
                    return handle_convert_single(type('args', (), {
                        'mat': str(mat_file),
                        'tracks': str(tracks_dir),
                        'bin': str(bin_file),
                        'output': str(output_dir / f"{mat_file.stem}.h5"),
                        'codebase': str(codebase_path)
                    })())
        
        print(f"✗ Could not find required files (tracks directory, .bin file) for experiment")
        print(f"  MAT file: {mat_file}")
        return 1
    
    else:
        print(f"✗ Unsupported data type: {data_type}")
        return 1


def handle_analyze_engineer(args):
    """Handle analyze engineer command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "scripts" / "analyze" / "engineer_data.py"
    spec = importlib.util.spec_from_file_location("engineer_data", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['engineer_data.py', '--h5', args.h5]
    spec.loader.exec_module(module)
    return module.main()


def handle_analyze_dataset(args):
    """Handle analyze dataset command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "scripts" / "analyze" / "engineer_dataset_from_h5.py"
    spec = importlib.util.spec_from_file_location("engineer_dataset_from_h5", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['engineer_dataset_from_h5.py', '--h5', args.h5]
    spec.loader.exec_module(module)
    return module.main()


def handle_validate_schema(args):
    """Handle validate schema command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "validation" / "validators" / "validate_h5_schema.py"
    spec = importlib.util.spec_from_file_location("validate_h5_schema", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['validate_h5_schema.py', args.h5]
    if args.verbose:
        sys.argv.append('--verbose')
    spec.loader.exec_module(module)
    return module.main()


def handle_validate_integrity(args):
    """Handle validate integrity command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "validation" / "validators" / "validate_data_integrity.py"
    spec = importlib.util.spec_from_file_location("validate_data_integrity", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['validate_data_integrity.py', args.mat, args.h5]
    if args.tracks:
        sys.argv.extend(['--tracks'] + [str(t) for t in args.tracks])
    if args.verbose:
        sys.argv.append('--verbose')
    spec.loader.exec_module(module)
    return module.main()


def handle_validate_full(args):
    """Handle validate full command"""
    import importlib.util
    script_path = Path(__file__).parent / "src" / "validation" / "validators" / "run_full_validation.py"
    spec = importlib.util.spec_from_file_location("run_full_validation", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['run_full_validation.py', '--base-dir', args.base_dir]
    if args.verbose:
        sys.argv.append('--verbose')
    if args.output:
        sys.argv.extend(['--output', args.output])
    spec.loader.exec_module(module)
    return module.main()


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check MATLAB Engine only for commands that need it
    matlab_commands = ['convert']
    if args.command in matlab_commands:
        if not check_matlab_engine():
            print("ERROR: MATLAB Engine for Python is required.")
            print("Please install it from MATLAB:")
            print("  cd matlabroot/extern/engines/python")
            print("  python setup.py install")
            print("\nOr see: https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html")
            sys.exit(1)
    
    # Route to appropriate handler
    handlers = {
        ('convert', 'batch'): handle_convert_batch,
        ('convert', 'single'): handle_convert_single,
        ('convert', 'append-camcal'): handle_convert_append_camcal,
        ('convert', 'unlock'): handle_convert_unlock,
        ('convert', 'auto'): handle_convert_auto,
        ('analyze', 'engineer'): handle_analyze_engineer,
        ('analyze', 'dataset'): handle_analyze_dataset,
        ('validate', 'schema'): handle_validate_schema,
        ('validate', 'integrity'): handle_validate_integrity,
        ('validate', 'full'): handle_validate_full,
    }
    
    handler = handlers.get((args.command, args.subcommand))
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
