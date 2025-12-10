# magatfairy: MATLAB to H5 made easy

**Version 0.2.1** | Python 3.8+ | MATLAB R2020a+

magatfairy converts MAGAT (Multi Animal Gate and Track Analyzer) experiments into clean H5 files for Python workflows. It ships the MATLAB bridge, conversion scripts, and validation tools so you can drag in data, run a single command, and get analysis-ready H5 outputs.

## Overview

This tool is designed for researchers who:
- Use MATLAB and MAGAT Analyzer
- Process data from optogenetic genotype experiments
- Have root folders containing ESET directories (or single ESET folders)
- Want to convert their data to H5 format for Python analysis

## Quick Start

### 1. Clone magatfairy

```bash
git clone https://github.com/GilRaitses/magatfairy.git
cd magatfairy
```

> No conda or Docker required. Plain Python 3.8+ with pip is enough. A venv is optional but recommended.

### 2. Install Dependencies (and optional venv)

```bash
# optional but recommended
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# mac/Linux: source .venv/bin/activate

python src/install/install.py
```

This will install:
- numpy
- h5py
- scipy
- matlabengine (MATLAB Engine for Python)

**Note:** If MATLAB Engine installation fails, you may need to install it manually from MATLAB:
```bash
cd matlabroot/extern/engines/python
python setup.py install
```

See: https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

### 2b. Get the CLI (choose one)

- **Standard machines (recommended):**
  ```bash
  # optionally inside a venv
  pip install -e .
  magatfairy --help
  ```
  Ensure your Python Scripts dir is on PATH:
  - Windows: `%APPDATA%\Python\Python311\Scripts` or your venv’s `Scripts`
  - mac/Linux: `$HOME/.local/bin` or your venv’s `bin`

- **Managed / locked-down machines (no PATH changes):**
  ```bash
  python -m cli.magatfairy --help
  python -m cli.magatfairy convert auto /path/to/data
  ```
  (Uses the module directly; works even if executables are blocked.)

### MAGAT class folders
- magatfairy ships bundled MAGAT class folders at `matlab/core` and uses them by default (no external download).
- If you need to override with a different MAGAT codebase, set `MAGAT_CODEBASE` or `magatfairy config set magat_codebase /path/to/codebase`.

### Optional system check before running
- Minimal wiring check (no installs): `python -m cli.magatfairy --help`
- Dependency check/install: `python src/install/install.py` (reports Python version, git, MATLAB engine, and installs pip deps)
- Built-in CLI check: `magatfairy systemfairy` (or `python -m cli.magatfairy systemfairy` on locked-down machines)

### 3. Run the Conversion Tool

**Quick Start (Recommended):**
```bash
magatfairy convert auto
```

This will auto-detect your data type and guide you through conversion.

**Interactive Mode:**
```bash
magatfairy
```

The tool will guide you through:
1. **Data Path Selection** - Choose root folder with multiple ESETs or single ESET directory
2. **Output Directory** - Specify where H5 files should be saved
3. **Conversion** - Process your data

Note: MAGAT codebase is bundled by default. You can override it with `MAGAT_CODEBASE` environment variable if needed.

## Requirements

### Required
- **Python 3.8+**
- **MATLAB** (with MATLAB Engine for Python installed)

Note: MAGAT codebase is bundled with magatfairy at `matlab/core` and used by default. No external download needed.

### Optional
- **Git** - Required for cloning magatfairy repository (if you cloned magatfairy, you have git!)

## MAGAT Codebase

magatfairy includes a bundled minimal subset of MAGAT (MATLAB Track Analysis) core classes at `matlab/core`. These are used by default, so no external download is required.

### Using Bundled Classes (Default)

The bundled classes are automatically used when you run magatfairy. No configuration needed.

### Overriding with External Codebase

If you need to use a different MAGAT codebase (e.g., for additional features):
1. Set the `MAGAT_CODEBASE` environment variable:
   ```bash
   # Windows PowerShell
   $env:MAGAT_CODEBASE = "D:\path\to\MAGATAnalyzer-Matlab-Analysis"
   
   # Windows CMD
   set MAGAT_CODEBASE=D:\path\to\MAGATAnalyzer-Matlab-Analysis
   
   # macOS/Linux
   export MAGAT_CODEBASE=/path/to/MAGATAnalyzer-Matlab-Analysis
   ```

2. Or use the config command:
   ```bash
   magatfairy config set magat_codebase /path/to/MAGATAnalyzer-Matlab-Analysis
   ```

The bundled classes include the essential `DataManager`, `ExportManager`, `TrackManager`, and related classes needed for conversion.

## Data Structure

### Root Folder Structure (Multiple ESETs)

```
GMR61@GMR61/
├── T_Re_Sq_0to250PWM_30#C_Bl_7PWM/
│   ├── matfiles/
│   │   ├── GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202510301513.mat
│   │   └── ...
│   └── ...
├── T_Re_Sq_50to250PWM_30#C_Bl_7PWM/
│   ├── matfiles/
│   │   └── ...
│   └── ...
└── ...
```

### Single ESET Structure

```
T_Re_Sq_0to250PWM_30#C_Bl_7PWM/
├── matfiles/
│   ├── GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202510301513.mat
│   └── ...
└── ...
```

## Output

H5 files are saved to the specified output directory with the following structure:

```
h5_output/
├── GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202510301513.h5
├── GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202510311441.h5
└── ...
```

Each H5 file contains:
- Complete MAGAT structure
- Tracks with derived quantities
- Global quantities (LED values, etc.)
- ETI (Experiment Time Index) at root level
- Camera calibration data

## Usage Examples

### Process Root Folder with Multiple ESETs

```bash
magatfairy convert batch --root-dir /path/to/GMR61@GMR61 --output-dir /path/to/h5_output
```

Or use auto-detect (recommended):
```bash
magatfairy convert auto /path/to/GMR61@GMR61
```

### Process Single ESET

```bash
magatfairy convert auto /path/to/T_Re_Sq_0to250PWM_30#C_Bl_7PWM/
```

Or use batch mode with ESET directory:
```bash
magatfairy convert batch --root-dir /path/to/T_Re_Sq_0to250PWM_30#C_Bl_7PWM --output-dir /path/to/h5_output
```

Note: The `--codebase` flag is optional. Bundled classes are used by default. Override with `MAGAT_CODEBASE` environment variable if needed.

## Troubleshooting

### MATLAB Engine Not Found

If you see "MATLAB Engine Not Found":
1. Ensure MATLAB is installed
2. Install MATLAB Engine for Python:
   ```bash
   cd matlabroot/extern/engines/python
   python setup.py install
   ```

### Git Not Found

If git is not installed and you need to clone magatfairy:
1. Install git: https://git-scm.com/downloads
2. Or download magatfairy as a ZIP from GitHub

### No ESET Directories Found

Ensure your data folder contains subdirectories with `matfiles/` folders containing `.mat` files.

### Conversion Errors

- Run system check: `magatfairy systemfairy` to verify environment
- Verify that bundled MAGAT classes are present at `matlab/core/@DataManager`
- Verify that `.mat` files are in `matfiles/` subdirectories
- Ensure output directory is writable
- Check MATLAB Engine is properly installed

## Directory Structure

```
magatfairy/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Packaging + console_scripts entry
├── index.html                   # Landing page
│
├── matlab/                      # Bundled MAGAT core classes
│   └── core/                    # Minimal MATLAB classes (DataManager, etc.)
│       ├── @DataManager/        # Data loading and management
│       ├── @ExportManager/      # Export utilities
│       ├── @TrackManager/       # Track management
│       └── ...                  # Other core classes
│
├── src/                         # Source code
│   ├── install/                # Installation script (python src/install/install.py)
│   ├── cli/                    # Installed CLI shim (`magatfairy` command)
│   ├── launch_scripts/         # Double-click launchers for each OS
│   ├── mat2h5/                 # Core package (stable API)
│   │   ├── __init__.py         # Package initialization
│   │   ├── bridge.py           # MAGAT Bridge (MATLAB interface)
│   │   ├── config.py           # Configuration management
│   │   └── progress.py         # Progress tracking utilities
│   ├── scripts/                 # User-facing scripts (separate from package)
│   │   ├── convert/             # MATLAB → H5 conversion tools
│   │   │   ├── convert_matlab_to_h5.py    # Core conversion logic
│   │   │   ├── batch_export_esets.py      # Batch processing
│   │   │   ├── append_camcal_to_h5.py     # Camera calibration
│   │   │   └── unlock_h5_file.py          # H5 file utilities
│   │   └── analyze/             # H5 analysis scripts
│   │       ├── engineer_data.py           # Basic analysis
│   │       └── engineer_dataset_from_h5.py # Enhanced analysis
│   └── validation/              # Validation framework (separate from package)
│       ├── reference/           # MATLAB reference implementations
│       └── validators/          # Python validation scripts
│
└── docs/                        # Additional documentation and assets
    ├── assets/                 # Web assets (e.g., fairy-frames.js)
    ├── field-mapping.md        # MATLAB to H5 field reference
    └── magat-license.md        # MAGAT Analyzer license info
```

**Note:** The MAGAT Bridge code is included in `src/mat2h5/bridge.py`, and MAGAT core classes are bundled at `matlab/core`. You don't need any external dependencies beyond MATLAB.

## Advanced Usage

### Command-Line Interface

magatfairy provides a CLI with subcommands for all operations:

#### Quick Start: Click-and-Go (Easiest!)

**macOS:** Double-click `src/launch_scripts/magatfairy.command`  
**Linux:** Double-click `src/launch_scripts/magatfairy.sh`  
**Windows:** Double-click `src/launch_scripts/magatfairy.bat`

This opens a terminal window. Drag your data folder into it and press Enter. H5 files will be saved to `exports/` folder in the magatfairy repository.

#### Command-Line: Auto-Detect (Drag-and-Drop)

```bash
# Drag a folder into the terminal and press Enter
magatfairy convert auto

# Or provide the path directly
magatfairy convert auto /path/to/your/data
```

The tool will automatically detect:
- **Genotype** (root directory with multiple ESET folders)
- **ESET** (single folder with matfiles/ subdirectory)
- **Experiment** (single .mat file)
- **Track** (track file or tracks directory)

You'll be prompted for:
- Output directory (default: `exports/` folder in the magatfairy repository)

Note: MAGAT codebase is bundled and used automatically. Override with `MAGAT_CODEBASE` environment variable if needed.

#### Manual Commands

```bash
# Conversion commands
magatfairy convert batch --root-dir /path/to/data --output-dir /path/to/output
magatfairy convert single --mat file.mat --output file.h5
magatfairy convert append-camcal --eset-dir /path/to/eset
magatfairy convert unlock --file file.h5

# Analysis commands
magatfairy analyze engineer --h5 file.h5
magatfairy analyze dataset --h5 file.h5

# Validation commands
magatfairy validate schema --h5 file.h5
magatfairy validate integrity --mat file.mat --h5 file.h5
magatfairy validate full --base-dir /path/to/data

# Help
magatfairy --help
magatfairy convert --help
```

Scripts can also be run directly:
```bash
python src/scripts/convert/batch_export_esets.py --root-dir /path/to/data --output-dir /path/to/output
```

## Configuration

Save your settings to avoid entering them every time:

```bash
magatfairy config set magat_codebase /path/to/magat  # Optional: override bundled classes
magatfairy config set default_output /path/to/exports
magatfairy config show  # View all settings
```

Note: `magat_codebase` is optional. Bundled classes at `matlab/core` are used by default.

## Troubleshooting

### MATLAB Engine Not Found
- Install MATLAB Engine for Python:
  ```bash
  cd matlabroot/extern/engines/python
  python setup.py install
  ```
- See: https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

### Conversion Fails
- Run system check: `magatfairy systemfairy` (or `python -m cli.magatfairy systemfairy`)
- Verify MATLAB Engine is installed and accessible
- Check that bundled MAGAT classes are present: `matlab/core/@DataManager`
- If using custom codebase, verify path: `magatfairy config get magat_codebase`
- Check log file: `exports/conversion.log`

### Files Already Exist
- Use `--skip-existing` to skip already-converted files
- Use `--resume` to continue from previous progress

### Progress Tracking
- Progress is saved to `exports/.progress.json`
- Use `--resume` to continue interrupted conversions
- Colored progress: Red (beginning), White (middle), Blue (end)

## Support

For issues or questions:
- Check the troubleshooting section above
- Review field mapping reference: `docs/field-mapping.md`
- Check log files in `exports/` directory

## Changelog

### v0.2.1 (2025-12-10)
- Fixed `derivation_rules` export: MATLAB returns DerivationRules as matlab.object, not dict
- Extract struct fields individually via `eng.eval()` for reliable cross-platform behavior
- Use `require_group()` to prevent "group already exists" errors on fallback

### v0.2.0 (2025-12-10)
- Added `derivation_rules` export (smoothTime, derivTime, interpTime) for INDYsim compatibility
- Fixed stimulus detection for empty onset arrays
- Fixed division-by-zero in progress tracker
- Added unit documentation to all exported fields
- Added `validate_h5_for_analysis.py` validation script

### v0.1.0 (2025-12-05)
- Initial release
- CLI with `magatfairy` command
- Batch conversion of ESET directories
- Bundled MATLAB core classes
- systemfairy environment checker
- Colored progress tracking

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

### MAGAT Analyzer

magatfairy uses the **MAGAT Analyzer** (Multi Animal Gate and Track Analyzer) codebase:

- **Repository**: [samuellab/MAGATAnalyzer-Matlab-Analysis](https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis)
- **License**: Creative Commons Attribution Share Alike 3.0 United States License
- **Copyright**: © 2011 Marc Gershow
- **Citation**: Gershow M, Berck M, Mathew D, Luo L, Kane E, Carlson J, Samuel ADT. Controlling Airborne Chemical Cues For Studying Navigation in Small Animals. Nature Methods. 2012

If you use magatfairy or MAGAT Analyzer in your research, please cite the above publication.

**License Notice**: Any modification or redistribution of MAGAT Analyzer code must include the original license. See the [MAGAT Analyzer repository](https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis) for full license details.
