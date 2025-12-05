# Validation Framework

This directory contains scripts for validating that converted H5 files produce identical analysis results to the original MATLAB implementation.

## Quick Start

Run the full validation suite:

```bash
python run_full_validation.py --base-dir /path/to/experiment/data
```

## Directory Structure

```
validation/
├── matlab/              # MATLAB reference scripts
│   ├── load_experiment_and_compute.m
│   ├── compute_speedrunvel.m
│   ├── detect_reversals.m
│   └── ...
├── python/              # Python validation scripts
│   ├── validate_h5_schema.py
│   ├── validate_data_integrity.py
│   ├── load_experiment_and_compute.py
│   └── ...
├── run_full_validation.py      # Master validation script
├── run_matlab_validation.py   # Run MATLAB validation via engine
├── compare_real_data.py        # Compare MATLAB vs Python outputs
└── README.md                   # This file
```

## Validation Layers

1. **Schema Validation** - Verify H5 file structure
2. **Data Integrity** - Compare H5 data to source .mat files
3. **Computation** - Compare intermediate computed values
4. **Results** - Compare final analysis outputs

## Usage

See [docs/VALIDATION.md](../docs/VALIDATION.md) for detailed documentation on running validation and interpreting results.

## Field Mapping Reference

See [docs/FIELD_MAPPING.md](../docs/FIELD_MAPPING.md) for complete MATLAB to H5 field mapping reference.
