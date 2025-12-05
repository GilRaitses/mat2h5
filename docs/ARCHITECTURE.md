# Architecture

## Overview

mat2h5 is organized as a standalone Python tool with a clean separation between the core library, conversion scripts, and analysis tools.

## Directory Structure

```
mat2h5/
├── src/
│   ├── mat2h5/          # Core package
│   │   └── bridge.py    # MAGAT Bridge (MATLAB interface)
│   └── scripts/         # User-facing scripts
│       ├── conversion/   # MATLAB → H5 conversion
│       └── analysis/     # H5 analysis tools
├── validation/          # Validation framework
└── mat2h5.py           # Main CLI entry point
```

## Components

### Core Package (`src/mat2h5/`)

- **bridge.py**: Provides the `MAGATBridge` class that interfaces with MATLAB Engine to load and access MAGAT experiment data.

### Conversion Scripts (`src/scripts/conversion/`)

- **convert_matlab_to_h5.py**: Core conversion logic that exports complete MAGAT structure to H5 format
- **batch_export_esets.py**: Batch processes multiple ESET directories
- **append_camcal_to_h5.py**: Adds camera calibration data to existing H5 files
- **unlock_h5_file.py**: Utility to unlock locked H5 files

### Analysis Scripts (`src/scripts/analysis/`)

- **engineer_dataset_from_h5.py**: Enhanced analysis with stimulus windows and population aggregates
- **engineer_data.py**: Basic analysis script for H5 files

### Main Entry Point

- **mat2h5.py**: Interactive CLI tool that guides users through the conversion process

## Data Flow

1. User runs `mat2h5.py`
2. Tool prompts for MAGAT codebase path (or clones automatically)
3. User selects data path (root folder or single ESET)
4. Tool calls `batch_export_esets.py` with appropriate parameters
5. `batch_export_esets.py` calls `convert_matlab_to_h5.py` for each experiment
6. `convert_matlab_to_h5.py` uses `MAGATBridge` to interface with MATLAB
7. H5 files are written to the output directory

## Dependencies

- **MATLAB Engine for Python**: Required for MATLAB interface
- **MAGAT Codebase**: Required for loading experiments (can be cloned automatically)
  - Repository: [https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis](https://github.com/samuellab/MAGATAnalyzer-Matlab-Analysis)
- **Python packages**: numpy, h5py, scipy (see requirements.txt)

