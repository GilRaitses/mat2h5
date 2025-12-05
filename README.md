# mat2h5 - MATLAB to H5 Conversion Tool

A standalone tool for converting MAGAT (MATLAB Track Analysis) experiment data to H5 format for use in Python analysis pipelines.

## Overview

This tool is designed for researchers who:
- Use MATLAB and MAGAT Analyzer
- Process data from optogenetic genotype experiments
- Have root folders containing ESET directories (or single ESET folders)
- Want to convert their data to H5 format for Python analysis

## Quick Start

### 1. Clone mat2h5

```bash
git clone https://github.com/GilRaitses/mat2h5.git
cd mat2h5
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

```bash
python mat2h5.py
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
- **Git** - Required for automatic codebase cloning (if you cloned mat2h5, you have git!)

## MAGAT Codebase

The MAGAT (MATLAB Track Analysis) codebase is required for conversion. You have two options:

### Option 1: Automatic Cloning (Recommended)

If git is installed, the tool can clone it automatically:
- Repository: `https://github.com/SkanataLab/Matlab-Track-Analysis-SkanataLab.git`
- Default location: `~/codebase/Matlab-Track-Analysis-SkanataLab`

### Option 2: Manual Setup

If you already have the codebase:
1. Clone manually: `git clone https://github.com/SkanataLab/Matlab-Track-Analysis-SkanataLab.git`
2. Provide the path when prompted by `mat2h5.py`

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
python mat2h5.py
# Select: Process multiple ESETs
# Enter: /path/to/GMR61@GMR61/
# Output: /path/to/h5_output/
```

### Process Single ESET

```bash
python mat2h5.py
# Select: Process single ESET
# Enter: /path/to/T_Re_Sq_0to250PWM_30#C_Bl_7PWM/
# Output: /path/to/h5_output/
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
   git clone https://github.com/SkanataLab/Matlab-Track-Analysis-SkanataLab.git
   ```

### No ESET Directories Found

Ensure your data folder contains subdirectories with `matfiles/` folders containing `.mat` files.

### Conversion Errors

- Check that MATLAB can access the MAGAT codebase
- Verify that `.mat` files are in `matfiles/` subdirectories
- Ensure output directory is writable

## Directory Structure

```
mat2h5/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── install.py                   # Installation script
├── mat2h5.py                   # Main entry point (CLI tool)
│
├── src/                         # Source code
│   ├── mat2h5/                 # Package directory
│   │   ├── __init__.py         # Package initialization
│   │   └── bridge.py           # MAGAT Bridge (MATLAB interface)
│   └── scripts/                 # User-facing scripts
│       ├── conversion/          # MATLAB → H5 conversion tools
│       │   ├── convert_matlab_to_h5.py    # Core conversion logic
│       │   ├── batch_export_esets.py      # Batch processing
│       │   ├── append_camcal_to_h5.py     # Camera calibration
│       │   └── unlock_h5_file.py          # H5 file utilities
│       └── analysis/            # H5 analysis scripts
│           ├── engineer_data.py           # Basic analysis
│           └── engineer_dataset_from_h5.py # Enhanced analysis
│
├── validation/                  # Validation framework (optional)
│   ├── matlab/                 # MATLAB reference scripts
│   ├── python/                 # Python validation scripts
│   └── README.md               # Validation documentation
│
└── docs/                        # Additional documentation
    ├── SETUP_REMOTE.md         # Remote repository setup
    └── REPO_DESCRIPTION.md     # Repository description
```

**Note:** The MAGAT Bridge code is included in `mat2h5/bridge.py`, so you don't need any external dependencies beyond MATLAB and the MAGAT codebase.

## Advanced Usage

### Command-Line Interface (Future)

Direct command-line usage is planned for future versions:

```bash
python mat2h5.py --root-dir /path/to/data --output /path/to/output --codebase /path/to/codebase
```

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the validation documentation in `validation/README.md`
- Check MATLAB Engine installation: https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **MAGAT Analyzer**: Samuel Lab (SkanataLab)
- **MATLAB Track Analysis**: [https://github.com/SkanataLab/Matlab-Track-Analysis-SkanataLab](https://github.com/SkanataLab/Matlab-Track-Analysis-SkanataLab)
