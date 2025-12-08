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
import subprocess
import shutil
import os
import atexit
import signal
import gc
import io
import platform
from pathlib import Path
from typing import Optional, Tuple

from mat2h5.config import get_magat_codebase

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

# MAGAT codebase repository (Samuel Lab)
MAGAT_REPO_URL = "https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git"
MAGAT_REPO_NAME = "MAGATAnalyzer-Matlab-Analysis"

_CLEANUP_DONE = False
_RUN_COMPLETED = False


def close_open_files():
    """Close open file handles to release locks (best-effort)."""
    try:
        for obj in gc.get_objects():
            try:
                if isinstance(obj, io.IOBase) and not obj.closed:
                    obj.close()
            except Exception:
                continue
    except Exception:
        pass


def kill_python_processes(exclude_pid: Optional[int] = None):
    """Terminate python processes to avoid lingering file locks."""
    try:
        import psutil  # type: ignore
    except Exception:
        psutil = None

    if psutil:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if "python" in name and proc.pid != exclude_pid:
                    proc.terminate()
            except Exception:
                continue
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if "python" in name and proc.pid != exclude_pid:
                    proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    continue
    else:
        if os.name == "nt":
            filters = ["/F", "/FI", f"PID ne {exclude_pid}"] if exclude_pid else ["/F"]
            for image in ("python.exe", "python3.exe", "pythonw.exe"):
                cmd = ["taskkill", "/IM", image, *filters]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            subprocess.run(
                ["pkill", "-f", "python"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


def kill_named_processes(names, exclude_pid: Optional[int] = None):
    """Terminate processes by name (best-effort), skipping exclude_pid."""
    try:
        import psutil  # type: ignore
    except Exception:
        psutil = None

    if psutil:
        lowered = {n.lower() for n in names}
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in lowered and proc.pid != exclude_pid:
                    proc.terminate()
            except Exception:
                continue
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in lowered and proc.pid != exclude_pid:
                    proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    continue
    else:
        if os.name == "nt":
            filters = ["/F", "/FI", f"PID ne {exclude_pid}"] if exclude_pid else ["/F"]
            for name in names:
                cmd = ["taskkill", "/IM", name, *filters]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            for name in names:
                subprocess.run(
                    ["pkill", "-f", name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )


def cleanup_on_exit(reason: str = "exit"):
    """Best-effort cleanup to free locks and stop python processes."""
    global _CLEANUP_DONE
    if _CLEANUP_DONE:
        return
    _CLEANUP_DONE = True

    if _RUN_COMPLETED and reason == "normal":
        return

    close_open_files()
    kill_python_processes(exclude_pid=os.getpid())
    if os.name == "nt":
        # MATLAB can hold files; Explorer preview can lock folders.
        kill_named_processes(["MATLAB.exe", "matlab.exe", "matlab"], exclude_pid=os.getpid())
        # Cursor.exe (IDE) can hold file handles from indexing/open files
        if os.environ.get("MAGATFAIRY_KILL_CURSOR", "0") == "1":
            kill_named_processes(["Cursor.exe", "cursor.exe"], exclude_pid=os.getpid())
        if os.environ.get("MAGATFAIRY_KILL_EXPLORER", "0") == "1":
            kill_named_processes(["explorer.exe", "explorer"], exclude_pid=os.getpid())


def _signal_handler(signum, frame):
    cleanup_on_exit(f"signal:{signum}")
    sys.exit(1)


def setup_cleanup_hooks():
    atexit.register(cleanup_on_exit)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _signal_handler)
        except Exception:
            continue
    if hasattr(signal, "SIGBREAK"):
        try:
            signal.signal(signal.SIGBREAK, _signal_handler)
        except Exception:
            pass


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


def clone_magat_codebase(target_path: Optional[Path] = None) -> Optional[Path]:
    """
    Clone the MAGAT codebase to parent directory of mat2h5 repo.
    
    Args:
        target_path: Optional specific path (defaults to parent of mat2h5 repo)
    
    Returns:
        Path to cloned codebase, or None if cloning failed
    """
    if not check_git():
        print("\n[FAIL] Git is not installed. Cannot clone MAGAT codebase automatically.")
        print(f"Please clone manually: {MAGAT_REPO_URL}")
        return None


def run_systemfairy():
    """Simple environment check for common requirements."""
    status = []

    bundled_core = REPO_ROOT / "matlab" / "core"

    # MAGAT Analyzer codebase (required)
    configured_codebase = get_magat_codebase()
    env_codebase = os.environ.get("MAGAT_CODEBASE")
    effective_codebase = configured_codebase or (Path(env_codebase) if env_codebase else None)

    # magatfairy bundled class folders (present)
    bundled_ok = bundled_core.exists()
    status.append(("Bundled magatfairy class folders", bundled_ok, str(bundled_core)))

    # MAGAT Analyzer presence
    codebase_ok = effective_codebase.exists() if effective_codebase else False
    codebase_detail = str(effective_codebase) if effective_codebase else "not set (will prompt/auto-clone during convert)"
    status.append(("MAGAT Analyzer codebase", codebase_ok, codebase_detail))

    # Python version
    py_ok = sys.version_info >= (3, 8)
    status.append(("Python >= 3.8", py_ok, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))

    # Git availability
    git_ok = check_git()
    status.append(("git available (for auto-clone)", git_ok, shutil.which("git") or "not found"))

    # MATLAB Engine
    matlab_ok = check_matlab_engine()
    status.append(("MATLAB Engine importable", matlab_ok, "ok" if matlab_ok else "missing"))

    print("=" * 60)
    print("systemfairy: environment check")
    print("=" * 60)
    if configured_codebase:
        print(f"Configured MAGAT codebase (config): {configured_codebase}")
    elif env_codebase:
        print(f"Using MAGAT_CODEBASE env: {env_codebase}")
    else:
        print("No MAGAT codebase configured; convert will prompt/auto-clone if allowed.")
    print(f"Bundled magatfairy class folders: {bundled_core}")

    for label, ok, detail in status:
        icon = "[OK]" if ok else "[X]"
        print(f"{icon} {label}: {detail}")
    print()

    missing = [label for label, ok, _ in status if not ok]
    if missing:
        print("Items to fix:")
        for label, ok, detail in status:
            if ok:
                continue
            if "MAGAT Analyzer codebase" in label:
                print(f"- Ensure MAGAT class folders exist at: {detail}")
                print(f"  (Bundled default expected at: {bundled_core})")
                print("  Or set MAGAT_CODEBASE to a valid path.")
            elif "MATLAB Engine" in label:
                print("- Install MATLAB Engine: cd matlabroot/extern/engines/python && python setup.py install")
            elif "git" in label:
                print("- Install git or provide MAGAT codebase path manually.")
            elif "Python" in label:
                print("- Install Python 3.8+ and re-run.")
        return 1
    else:
        print("All required checks passed.")
        return 0


def ensure_systemfairy_on_first_run():
    """
    Auto-run systemfairy on first invocation when no config/env override is set.
    Skips if MAGATFAIRY_SKIP_SYSTEMFAIRY=1.
    """
    if os.environ.get("MAGATFAIRY_SKIP_SYSTEMFAIRY") == "1":
        return

    # If MAGAT_CODEBASE is explicitly set, trust the user.
    if os.environ.get("MAGAT_CODEBASE"):
        return

    # If config exists, don't auto-run.
    config_path = Path.home() / ".magatfairy" / "config.json"
    if config_path.exists():
        return

    # No config/env: run systemfairy once, exit on failure.
    rc = run_systemfairy()
    if rc != 0:
        sys.exit(rc)


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
    subparsers.required = True
    
    # Convert subcommands
    convert_parser = subparsers.add_parser('convert', help='Conversion commands')
    convert_subparsers = convert_parser.add_subparsers(dest='subcommand', help='Conversion subcommands')
    
    # convert batch
    batch_parser = convert_subparsers.add_parser('batch', help='Batch convert all ESETs in a directory')
    batch_parser.add_argument('--root-dir', required=True, help='Root directory containing ESET folders')
    batch_parser.add_argument('--output-dir', help='Output directory for H5 files (default: exports/)')
    batch_parser.add_argument('--codebase', help='Path to MAGAT codebase (or use config/env)')
    batch_parser.add_argument('--skip-existing', action='store_true', help='Skip files that already exist')
    batch_parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    batch_parser.add_argument('--dry-run', action='store_true', help='Preview without converting')
    batch_parser.add_argument('--log-file', help='Log file path (default: output_dir/conversion.log)')
    batch_parser.add_argument('--validate', action='store_true', help='Run validation after conversion')
    
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
    auto_parser.add_argument('--output-dir', help='Output directory (default: exports/)')
    auto_parser.add_argument('--codebase', help='Path to MAGAT codebase (or use config/env)')
    auto_parser.add_argument('--skip-existing', action='store_true', help='Skip files that already exist')
    auto_parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    auto_parser.add_argument('--dry-run', action='store_true', help='Preview without converting')
    auto_parser.add_argument('--validate', action='store_true', help='Run validation after conversion')
    
    # Config subcommands
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_subparsers = config_parser.add_subparsers(dest='config_command', help='Config commands')
    
    # config set
    config_set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    config_set_parser.add_argument('key', choices=['magat_codebase', 'default_output'], help='Configuration key')
    config_set_parser.add_argument('value', help='Configuration value (path)')
    
    # config get
    config_get_parser = config_subparsers.add_parser('get', help='Get configuration value')
    config_get_parser.add_argument('key', choices=['magat_codebase', 'default_output'], help='Configuration key')
    
    # config show
    config_subparsers.add_parser('show', help='Show all configuration')
    
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

    # systemfairy (environment check)
    subparsers.add_parser('systemfairy', help='Run environment checks (Python, git, MATLAB Engine)')
    
    return parser


def handle_convert_batch(args):
    """Handle convert batch command"""
    import importlib.util
    from mat2h5.config import get_magat_codebase, get_default_output
    
    script_path = SRC_ROOT / "scripts" / "convert" / "batch_export_esets.py"
    spec = importlib.util.spec_from_file_location("batch_export_esets", script_path)
    module = importlib.util.module_from_spec(spec)
    
    # Build command args
    cmd_args = ['batch_export_esets.py', '--root-dir', args.root_dir]
    
    # Output directory (use default if not provided)
    output_dir = args.output_dir or get_default_output() or str(REPO_ROOT / "exports")
    cmd_args.extend(['--output-dir', output_dir])
    
    # Codebase (use config/env if not provided)
    codebase = args.codebase or get_magat_codebase()
    if codebase:
        cmd_args.extend(['--codebase', str(codebase)])
    
    # Optional flags
    if args.skip_existing:
        cmd_args.append('--skip-existing')
    if args.resume:
        cmd_args.append('--resume')
    if args.dry_run:
        cmd_args.append('--dry-run')
    if args.log_file:
        cmd_args.extend(['--log-file', args.log_file])
    if args.validate:
        cmd_args.append('--validate')
    
    sys.argv = cmd_args
    spec.loader.exec_module(module)
    return module.main()


def handle_convert_single(args):
    """Handle convert single command"""
    import importlib.util
    script_path = SRC_ROOT / "scripts" / "convert" / "convert_matlab_to_h5.py"
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
    script_path = SRC_ROOT / "scripts" / "convert" / "append_camcal_to_h5.py"
    spec = importlib.util.spec_from_file_location("append_camcal_to_h5", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['append_camcal_to_h5.py', '--eset-dir', args.eset_dir]
    spec.loader.exec_module(module)
    return module.main()


def handle_convert_unlock(args):
    """Handle convert unlock command"""
    import importlib.util
    script_path = SRC_ROOT / "scripts" / "convert" / "unlock_h5_file.py"
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
        print(f"\n[FAIL] Could not detect data type for: {input_path}")
        print("  Expected: genotype directory, ESET folder, experiment file, or tracks directory")
        return 1
    
    print(f"[OK] Detected: {data_type}")
    print(f"  Path: {detected_path}")
    
    # Get codebase path (from config, env, prompt, or clone)
    from mat2h5.config import get_magat_codebase, set_magat_codebase
    
    codebase_path = args.codebase or get_magat_codebase() or os.environ.get('MAGAT_CODEBASE')
    
    if not codebase_path:
        print("\n" + "=" * 70)
        print("MAGAT Codebase Required")
        print("=" * 70)
        print("\nOptions:")
        print("  1. Provide path to existing MAGAT codebase")
        if check_git():
            print("  2. Clone automatically (to parent directory)")
        else:
            print("  2. Clone automatically (git not available - install git first)")
        print("  3. Set with: mat2h5 config set magat_codebase /path")
        print()
        
        response = input("Enter path to MAGAT codebase, or press Enter to clone: ").strip()
        
        if response:
            # User provided path
            codebase_path = Path(response).expanduser()
            if not codebase_path.exists():
                print(f"[FAIL] Path does not exist: {codebase_path}")
                return 1
            # Save to config
            set_magat_codebase(codebase_path)
        else:
            # Clone automatically (if git is available)
            if not check_git():
                print("\n[FAIL] Git is not installed. Cannot clone automatically.")
                print("\nPlease either:")
                print("  1. Install git and try again")
                print("  2. Clone manually: git clone https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git")
                print("  3. Provide path to existing codebase")
                return 1
            
            print("\nCloning MAGAT codebase to parent directory...")
            codebase_path = clone_magat_codebase()
            if not codebase_path:
                print("\n[FAIL] Failed to clone MAGAT codebase")
                print("\nPlease either:")
                print("  1. Check your internet connection and try again")
                print("  2. Clone manually: git clone https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git")
                print("  3. Provide path to existing codebase")
                return 1
            # Save to config
            set_magat_codebase(codebase_path)
    
    codebase_path = Path(codebase_path)
    if not codebase_path.exists():
        print(f"[FAIL] MAGAT codebase not found: {codebase_path}")
        return 1
    
    # Get output directory - default to repo's exports folder or config
    from mat2h5.config import get_default_output
    
    default_output = get_default_output() or (REPO_ROOT / "exports")
    
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
    else:
        # Use config or repo's exports folder as default
        output_dir = Path(default_output)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[OK] Output directory: {output_dir}")
    
    # Route to appropriate handler based on detected type
    print(f"\n" + "=" * 70)
    print(f"Processing {data_type}: {detected_path.name}")
    print("=" * 70)
    
    if data_type == 'genotype':
        # Process as genotype (batch)
        return handle_convert_batch(type('args', (), {
            'root_dir': str(detected_path),
            'output_dir': str(output_dir),
            'codebase': str(codebase_path),
            'skip_existing': args.skip_existing if hasattr(args, 'skip_existing') else False,
            'resume': args.resume if hasattr(args, 'resume') else False,
            'dry_run': args.dry_run if hasattr(args, 'dry_run') else False,
            'validate': args.validate if hasattr(args, 'validate') else False,
            'log_file': None
        })())
    
    elif data_type == 'eset':
        # Process as single ESET
        import importlib.util
        script_path = SRC_ROOT / "scripts" / "convert" / "batch_export_esets.py"
        spec = importlib.util.spec_from_file_location("batch_export_esets", script_path)
        module = importlib.util.module_from_spec(spec)
        
        cmd_args = ['batch_export_esets.py', '--eset-dir', str(detected_path),
                    '--output-dir', str(output_dir), '--codebase', str(codebase_path)]
        
        if hasattr(args, 'skip_existing') and args.skip_existing:
            cmd_args.append('--skip-existing')
        if hasattr(args, 'resume') and args.resume:
            cmd_args.append('--resume')
        if hasattr(args, 'dry_run') and args.dry_run:
            cmd_args.append('--dry-run')
        if hasattr(args, 'validate') and args.validate:
            cmd_args.append('--validate')
        
        sys.argv = cmd_args
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
        
        print(f"[FAIL] Could not find required files (tracks directory, .bin file) for experiment")
        print(f"  MAT file: {mat_file}")
        return 1
    
    else:
        print(f"[FAIL] Unsupported data type: {data_type}")
        return 1


def handle_analyze_engineer(args):
    """Handle analyze engineer command"""
    import importlib.util
    script_path = SRC_ROOT / "scripts" / "analyze" / "engineer_data.py"
    spec = importlib.util.spec_from_file_location("engineer_data", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['engineer_data.py', '--h5', args.h5]
    spec.loader.exec_module(module)
    return module.main()


def handle_analyze_dataset(args):
    """Handle analyze dataset command"""
    import importlib.util
    script_path = SRC_ROOT / "scripts" / "analyze" / "engineer_dataset_from_h5.py"
    spec = importlib.util.spec_from_file_location("engineer_dataset_from_h5", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.argv = ['engineer_dataset_from_h5.py', '--h5', args.h5]
    spec.loader.exec_module(module)
    return module.main()


def handle_validate_schema(args):
    """Handle validate schema command"""
    import importlib.util
    script_path = SRC_ROOT / "validation" / "validators" / "validate_h5_schema.py"
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
    script_path = SRC_ROOT / "validation" / "validators" / "validate_data_integrity.py"
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
    script_path = SRC_ROOT / "validation" / "validators" / "run_full_validation.py"
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
    global _RUN_COMPLETED
    setup_cleanup_hooks()

    parser = create_parser()
    args = parser.parse_args()

    # Auto-run systemfairy on first run when no config/env is set
    ensure_systemfairy_on_first_run()
    
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
    
    # Handle config commands
    if args.command == 'config':
        from mat2h5.config import set_config, get_config, load_config
        
        if args.config_command == 'set':
            if args.key == 'magat_codebase':
                from mat2h5.config import set_magat_codebase
                set_magat_codebase(Path(args.value))
                print(f"[OK] Set MAGAT codebase to: {args.value}")
            elif args.key == 'default_output':
                from mat2h5.config import set_default_output
                set_default_output(Path(args.value))
                print(f"[OK] Set default output to: {args.value}")
            return 0
        
        elif args.config_command == 'get':
            value = get_config(args.key)
            if value:
                print(value)
            else:
                print(f"No value set for {args.key}")
            return 0
        
        elif args.config_command == 'show':
            config = load_config()
            if config:
                print("Current configuration:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
            else:
                print("No configuration set")
            return 0
    
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
        ('systemfairy', None): lambda args: run_systemfairy(),
    }
    
    handler = handlers.get((args.command, getattr(args, 'subcommand', None)))
    if handler:
        try:
            rc = handler(args)
            _RUN_COMPLETED = True
            return rc
        finally:
            if _RUN_COMPLETED:
                cleanup_on_exit("normal")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
