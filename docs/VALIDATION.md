# Validation Framework

The mat2h5 validation framework ensures that converted H5 files produce identical analysis results to the original MATLAB implementation.

## Overview

The validation framework uses a three-layer architecture to verify data integrity and computational correctness:

| Layer | Name | Purpose | Scripts |
|-------|------|---------|---------|
| 1a | H5 Schema | Verify H5 has all required fields | `validate_h5_schema.py` |
| 1b | Data Integrity | Verify H5 matches source .mat | `validate_data_integrity.py`, `validate_h5_against_mat.m` |
| 2 | Computation | Compare intermediate values | `load_experiment_and_compute.m`, `load_experiment_and_compute.py` |
| 3 | Results | Compare final analysis outputs | `run_full_validation.py` |

## Key Principle

All validation is performed on **real experiment files**, not synthetic test cases.

## Running Validation

### Full Validation Suite

```bash
cd validation
python run_full_validation.py --base-dir /path/to/experiment/data
```

This will:
1. Validate H5 schema (Layer 1a)
2. Compare H5 data to source .mat files (Layer 1b)
3. Run MATLAB and Python computation pipelines (Layer 2)
4. Compare final analysis outputs (Layer 3)

### Individual Layer Validation

**Layer 1a - Schema Validation:**
```bash
cd validation/python
python validate_h5_schema.py /path/to/file.h5
```

**Layer 1b - Data Integrity:**
```bash
cd validation/python
python validate_data_integrity.py --mat /path/to/file.mat --h5 /path/to/file.h5
```

**Layer 2 - Computation:**
```bash
# MATLAB
cd validation/matlab
load_experiment_and_compute

# Python
cd validation/python
python load_experiment_and_compute.py /path/to/file.h5
```

**Layer 3 - Results Comparison:**
```bash
cd validation
python compare_real_data.py
```

## What is Validated

### SpeedRunVel Computation

The signed velocity computed using the dot product method:

```
HeadVec = shead - smid
HeadUnitVec = HeadVec / ||HeadVec||
VelocityVec = [dx, dy] / ||[dx, dy]||
SpeedRun = ||[dx, dy]|| / dt
CosThetaFactor = VelocityVec · HeadUnitVec
SpeedRunVel = SpeedRun × CosThetaFactor
```

### Reversal Detection

Events where SpeedRunVel < 0 for duration ≥ 3 seconds.

### Acceptance Criteria

| Metric | Threshold |
|--------|-----------|
| Max absolute difference (SpeedRunVel) | < 1e-6 |
| Time alignment | < 1e-6 seconds |
| Reversal count | Exact match |
| Reversal start times | < 0.1 seconds |

## Critical Data Source Requirements

⚠️ **IMPORTANT**: Always use `derived_quantities/sloc` (smoothed location), NOT `points/loc` (raw location).

Using the wrong data source causes:
- SpeedRunVel values 5-7x larger
- False negatives in reversal detection
- Incorrect analysis results

See [FIELD_MAPPING.md](FIELD_MAPPING.md) for complete field mapping reference.

## Field Mapping Reference

For detailed information on MATLAB to H5 field mappings, see [FIELD_MAPPING.md](FIELD_MAPPING.md).

## Troubleshooting

### "H5 file not found"
Run the conversion pipeline first to generate `.h5` files from MATLAB data.

### "Length mismatch"
Ensure both pipelines are loading the same track and using the same time base.

### "SpeedRunVel mismatch"
Check `lengthPerPixel` values - both pipelines must use identical camera calibration.

### "Schema validation failed"
Verify that the H5 file contains all required fields. See [FIELD_MAPPING.md](FIELD_MAPPING.md) for required fields.

## Validation Scripts Location

All validation scripts are located in the `validation/` directory:
- `validation/matlab/` - MATLAB reference scripts
- `validation/python/` - Python validation scripts
- `validation/run_full_validation.py` - Master validation script

