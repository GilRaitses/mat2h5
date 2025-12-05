# mat2h5 - MATLAB to H5 Conversion Tool

A standalone tool for converting MAGAT (MATLAB Track Analysis) experiment data to H5 format for use in Python analysis pipelines.

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

### 2. Install Dependencies

```bash
python install.py
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

### 3. Run the Conversion Tool

**Quick Start (Recommended):**
```bash
python magatfairy.py convert auto
```

This will auto-detect your data type and guide you through conversion.

**Interactive Mode:**
```bash
python magatfairy.py
```

The tool will guide you through:
1. **MAGAT Codebase Setup** - Provide path to existing codebase or clone automatically
2. **Data Path Selection** - Choose root folder with multiple ESETs or single ESET directory
3. **Output Directory** - Specify where H5 files should be saved
4. **Conversion** - Process your data

## Requirements

### Required
- **Python 3.8+**
- **MATLAB** (with MATLAB Engine for Python installed)
- **MAGAT Codebase** - Can be cloned automatically or provided manually

### Optional
- **Git** - Required for automatic codebase cloning (if you cloned magatfairy, you have git!)

## MAGAT Codebase

The MAGAT (MATLAB Track Analysis) codebase is required for conversion. You have two options:

### Option 1: Automatic Cloning (Recommended)

If git is installed, the tool can clone it automatically:
- Repository: [https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis](https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis)
- Default location: `~/codebase/MAGATAnalyzer-Matlab-Analysis`

### Option 2: Manual Setup

If you already have the codebase:
1. Clone manually: `git clone https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git`
2. Provide the path when prompted by `magatfairy.py`

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
python magatfairy.py convert batch --root-dir /path/to/GMR61@GMR61 --output-dir /path/to/h5_output --codebase /path/to/magat
```

Or use auto-detect:
```bash
python magatfairy.py convert auto /path/to/GMR61@GMR61
```

### Process Single ESET

```bash
python magatfairy.py convert auto /path/to/T_Re_Sq_0to250PWM_30#C_Bl_7PWM/
```

Or use batch mode with ESET directory:
```bash
python magatfairy.py convert batch --root-dir /path/to/T_Re_Sq_0to250PWM_30#C_Bl_7PWM --output-dir /path/to/h5_output --codebase /path/to/magat
```

## Troubleshooting

### MATLAB Engine Not Found

If you see "MATLAB Engine Not Found":
1. Ensure MATLAB is installed
2. Install MATLAB Engine for Python:
   ```bash
   cd matlabroot/extern/engines/python
   python setup.py install
   ```

### Git Not Found (for codebase cloning)

If git is not installed:
1. Install git: https://git-scm.com/downloads
2. Or clone the codebase manually:
   ```bash
   git clone https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis.git
   ```

### No ESET Directories Found

Ensure your data folder contains subdirectories with `matfiles/` folders containing `.mat` files.

### Conversion Errors

- Check that MATLAB can access the MAGAT codebase
- Verify that `.mat` files are in `matfiles/` subdirectories
- Ensure output directory is writable

## Directory Structure

```
magatfairy/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── install.py                   # Installation script
├── magatfairy.py               # Main entry point (CLI tool)
├── magatfairy.sh               # Linux/macOS double-click script
├── magatfairy.bat              # Windows double-click script
├── magatfairy.command          # macOS double-click script
│
├── src/                         # Source code
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
└── docs/                        # Additional documentation
    ├── field-mapping.md        # MATLAB to H5 field reference
    └── magat-license.md        # MAGAT Analyzer license info
```

**Note:** The MAGAT Bridge code is included in `src/mat2h5/bridge.py`, so you don't need any external dependencies beyond MATLAB and the MAGAT codebase.

## Advanced Usage

### Command-Line Interface

magatfairy provides a CLI with subcommands for all operations:

#### Quick Start: Click-and-Go (Easiest!)

**macOS:** Double-click `magatfairy.command`  
**Linux:** Double-click `magatfairy.sh`  
**Windows:** Double-click `magatfairy.bat`

This opens a terminal window. Drag your data folder into it and press Enter. H5 files will be saved to `exports/` folder in the magatfairy repository.

#### Command-Line: Auto-Detect (Drag-and-Drop)

```bash
# Drag a folder into the terminal and press Enter
python magatfairy.py convert auto

# Or provide the path directly
python magatfairy.py convert auto /path/to/your/data
```

The tool will automatically detect:
- **Genotype** (root directory with multiple ESET folders)
- **ESET** (single folder with matfiles/ subdirectory)
- **Experiment** (single .mat file)
- **Track** (track file or tracks directory)

You'll be prompted for:
- MAGAT codebase path (or set `MAGAT_CODEBASE` environment variable)
- Output directory (default: `exports/` folder in the magatfairy repository)

#### Manual Commands

```bash
# Conversion commands
python magatfairy.py convert batch --root-dir /path/to/data --output-dir /path/to/output --codebase /path/to/magat
python magatfairy.py convert single --mat file.mat --output file.h5 --codebase /path/to/magat
python magatfairy.py convert append-camcal --eset-dir /path/to/eset
python magatfairy.py convert unlock --file file.h5

# Analysis commands
python magatfairy.py analyze engineer --h5 file.h5
python magatfairy.py analyze dataset --h5 file.h5

# Validation commands
python magatfairy.py validate schema --h5 file.h5
python magatfairy.py validate integrity --mat file.mat --h5 file.h5
python magatfairy.py validate full --base-dir /path/to/data

# Help
python magatfairy.py --help
python magatfairy.py convert --help
```

Scripts can also be run directly:
```bash
python src/scripts/convert/batch_export_esets.py --root-dir /path/to/data --output-dir /path/to/output
```

## Configuration

Save your MAGAT codebase path to avoid entering it every time:

```bash
python magatfairy.py config set magat_codebase /path/to/magat
python magatfairy.py config set default_output /path/to/exports
python magatfairy.py config show  # View all settings
```

## Troubleshooting

### MATLAB Engine Not Found
- Install MATLAB Engine for Python:
  ```bash
  cd matlabroot/extern/engines/python
  python setup.py install
  ```
- See: https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

### Conversion Fails
- Check that MAGAT codebase path is correct: `python magatfairy.py config get magat_codebase`
- Verify MATLAB can access the codebase
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
