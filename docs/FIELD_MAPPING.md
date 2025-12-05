# Field Mapping: MATLAB Experiment to H5

## Overview

This document maps every MATLAB experiment field to its corresponding H5 path.
Both pipelines must produce identical outputs when given the same input data.

**Source**: Mason Klein's MATLAB scripts
**Target**: Python H5-based pipeline
**Validation Requirement**: All fields must match identically (tolerances specified below)

---

## Core Data Fields

### Time

| MATLAB Path | H5 Path | Type | Shape | Units | Tolerance |
|-------------|---------|------|-------|-------|-----------|
| `track.dq.eti` | `/tracks/{key}/derived_quantities/eti` | float64 | (N,) | seconds | 0 (exact) |
| N/A | `/eti` | float64 | (M,) | seconds | 0 (exact) |

**Notes**: 
- MATLAB stores time per-track in `dq.eti`
- H5 may have global `/eti` array spanning entire experiment
- Track-level ETI is preferred source; fall back to global ETI if needed

### Position Data

| MATLAB Path | H5 Path | Type | Shape | Units | Tolerance |
|-------------|---------|------|-------|-------|-----------|
| `track.dq.shead` | `/tracks/{key}/derived_quantities/shead` | float64 | (2, N) | pixels | 0 (exact) |
| `track.dq.smid` | `/tracks/{key}/derived_quantities/smid` | float64 | (2, N) | pixels | 0 (exact) |
| `track.dq.sloc` | `/tracks/{key}/derived_quantities/sloc` | float64 | (2, N) | pixels | 0 (exact) |

**⚠️ CRITICAL - Position Data Source:**
- Use `derived_quantities/sloc` (SMOOTHED location) - matches MATLAB `getDerivedQuantity('sloc')`
- Do NOT use `points/loc` (RAW location) - produces ~5-7x larger SpeedRunVel values
- Using wrong source causes incorrect reversal detection

**Notes**:
- `shead`: Smoothed head position [x; y]
- `smid`: Smoothed midpoint position [x; y]
- `sloc` / `loc`: Smoothed centroid location [x; y]
- Shape convention: MATLAB is (2, N), H5 may be (N, 2) - transpose if needed

### Calibration

**H5 Structure (ACTUAL):**
```
/lengthPerPixel                # cm/pixel at root (primary location)
/camcalinfo/                   # Camera calibration group
    @class_name                # "CameraCalibration"
/metadata.attrs['lengthPerPixel']  # Also in metadata attrs (backup)
```

| MATLAB Path | H5 Path | Type | Units | Tolerance |
|-------------|---------|------|-------|-----------|
| `eset.expt(1).camcalinfo` → computed | `/lengthPerPixel` | float64 | cm/pixel | 1e-12 |
| `eset.expt(1).camcalinfo` → computed | `/metadata.attrs['lengthPerPixel']` | float64 | cm/pixel | 1e-12 |

**MATLAB Computation**:
```matlab
cc = eset.expt(1).camcalinfo;
test_pixels_x = [100, 500];
test_pixels_y = [100, 500];
real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
lengthPerPixel = real_dist / pixel_dist;
```

**Actual Value**: `0.01018533 cm/pixel` (for GMR61@GMR61 experiments)

**H5 Export**: `append_camcal_to_h5.py` computes and exports this using the same MATLAB method.

### LED / Stimulus Data

**MATLAB Structure:**
```matlab
GQled1Val = eset.expt(1).globalQuantity(led1_idx);
led1_xdata = GQled1Val.xData;  % timestamps
led1_ydata = GQled1Val.yData;  % intensity/PWM values
```

**H5 Structure (ACTUAL):**
```
/eti                           # Global time array (LED time = frame time)
/global_quantities/
    led1Val/                   # LED1 GROUP (not dataset!)
        yData                  # LED1 intensity values
    led1ValDeriv/              # LED1 derivative group
        yData
    led1ValDiff/               # LED1 diff group
        yData
    led2Val/                   # LED2 GROUP (not dataset!)
        yData                  # LED2 intensity values
    led2ValDeriv/              # LED2 derivative group
        yData
    led2ValDiff/               # LED2 diff group
        yData
```

**Note:** `led1Val` and `led2Val` are **groups** containing `yData`, not direct datasets.

| MATLAB Path | H5 Path | Type | Shape | Units | Tolerance |
|-------------|---------|------|-------|-------|-----------|
| `globalQuantity('led1Val').xData` | `/eti` | float64 | (M,) | seconds | 0 (exact) |
| `globalQuantity('led1Val').yData` | `/global_quantities/led1Val` | float64 | (M,) | PWM | 0 (exact) |
| `globalQuantity('led2Val').xData` | `/eti` | float64 | (M,) | seconds | 0 (exact) |
| `globalQuantity('led2Val').yData` | `/global_quantities/led2Val` | float64 | (M,) | PWM | 0 (exact) |

**Notes**:
- LED time (xData) is the global `/eti` array - LED values sampled at each frame
- LED values (yData) used to derive **ton/toff stimulus integration windows**
- Critical for computing responses within stimulus integration windows
- Must match exactly between MATLAB and H5

### Track Metadata

| MATLAB Path | H5 Path | Type | Units | Tolerance |
|-------------|---------|------|-------|-----------|
| `track.trackNum` | `/tracks/{key}` (key = track_XXX) | int | - | 0 (exact) |
| `track.npts` | len(eti) | int | frames | 0 (exact) |
| `track.startFrame` | `/tracks/{key}/startFrame` | int | frame | 0 (exact) |
| `track.endFrame` | `/tracks/{key}/endFrame` | int | frame | 0 (exact) |

---

## Computed Values (Validation Points)

These values are computed from source data. Both pipelines must produce identical results.

### SpeedRunVel Computation Chain

| Step | MATLAB Variable | Python Variable | Shape | Tolerance |
|------|-----------------|-----------------|-------|-----------|
| 1 | `HeadVec = shead - smid` | `head_vec = shead - smid` | (2, N) | 0 (exact) |
| 2 | `HeadUnitVec = HeadVec ./ norm` | `head_unit_vec = head_vec / norms` | (2, N) | < 1e-10 |
| 3 | `dx, dy, dt` | `dx, dy, dt` | (N-1,) | 0 (exact) |
| 4 | `distance = sqrt(dx.^2 + dy.^2)` | `distance = sqrt(dx**2 + dy**2)` | (N-1,) | < 1e-14 |
| 5 | `SpeedRun = distance ./ dt` | `speed = distance / dt` | (N-1,) | < 1e-10 |
| 6 | `VelocityVec = [dx; dy] ./ distance` | `velocity_vec = [dx, dy] / distance` | (2, N-1) | < 1e-10 |
| 7 | `CosThetaFactor = dot(VelocityVec, HeadUnitVec)` | `cos_theta = sum(velocity_vec * head_unit_vec, axis=0)` | (N-1,) | < 1e-10 |
| 8 | `SpeedRunVel = SpeedRun .* CosThetaFactor` | `speedrunvel = speed * cos_theta` | (N-1,) | < 1e-10 |

### Reversal Detection

| Field | MATLAB | Python | Tolerance |
|-------|--------|--------|-----------|
| Reversal count | `length(reversals)` | `len(reversals)` | 0 (exact) |
| Start indices | `[reversals.start_idx]` | `[r['start_idx'] for r in reversals]` | 0 (exact) |
| End indices | `[reversals.end_idx]` | `[r['end_idx'] for r in reversals]` | 0 (exact) |
| Start times | `[reversals.start_time]` | `[r['start_time'] for r in reversals]` | < 0.001s |
| End times | `[reversals.end_time]` | `[r['end_time'] for r in reversals]` | < 0.001s |
| Durations | `[reversals.duration]` | `[r['duration'] for r in reversals]` | < 0.001s |

---

## H5 File Structure (ACTUAL Schema)

```
/
├── eti                              # Global elapsed time array (M,)
├── lengthPerPixel                   # Camera calibration cm/pixel (scalar)
├── camcalinfo/                      # Camera calibration group
│   └── @class_name                  # "CameraCalibration"
├── experiment_info/                 # Experiment metadata
├── led_data                         # LED data (dataset)
├── metadata/
│   ├── @num_tracks                  # Number of tracks
│   ├── @num_frames                  # Number of frames
│   ├── @lengthPerPixel              # cm/pixel (also here)
│   └── ...
├── stimulus/
│   ├── onset_frames                 # Stimulus onset frame indices
│   └── @num_cycles                  # Number of stimulus cycles
├── global_quantities/
│   ├── led1Val                      # LED1 intensity values (M,)
│   ├── led1ValDeriv                 # LED1 derivative
│   ├── led1ValDiff                  # LED1 diff
│   ├── led2Val                      # LED2 intensity values (M,)
│   ├── led2ValDeriv                 # LED2 derivative
│   └── led2ValDiff                  # LED2 diff
└── tracks/
    ├── track_1/
    │   ├── @id                      # Track ID number
    │   ├── metadata/                # Track metadata
    │   ├── state/                   # State arrays
    │   ├── derived_quantities/
    │   │   ├── eti                  # Track-level elapsed time (N,)
    │   │   ├── shead                # Smoothed head positions (2, N)
    │   │   ├── smid                 # Smoothed midpoint positions (2, N)
    │   │   ├── sloc                 # Smoothed centroid positions (2, N)
    │   │   ├── speed                # Speed
    │   │   ├── vel                  # Velocity
    │   │   ├── theta                # Heading angle
    │   │   ├── led1Val              # LED1 values at track frames
    │   │   ├── led2Val              # LED2 values at track frames
    │   │   └── ...                  # Many more derived quantities
    │   └── points/
    │       ├── loc                  # Centroid positions (2, N)
    │       ├── head                 # Head positions
    │       ├── mid                  # Midpoint positions
    │       ├── tail                 # Tail positions
    │       └── ...
    ├── track_2/
    │   └── ...
    └── ...
```

---

## Shape Conventions

### MATLAB
- Position arrays: (2, N) where row 1 = x, row 2 = y
- Time arrays: (1, N) or (N, 1) - must flatten

### Python/H5
- Position arrays: (2, N) preferred, (N, 2) acceptable with transpose
- Time arrays: (N,) 1D array

### Validation Check
```python
# Always verify shape and transpose if needed
if array.shape[0] != 2:
    array = array.T
assert array.shape[0] == 2, f"Expected shape (2, N), got {array.shape}"
```

---

## Track Identity Verification

**Critical**: Track numbering must match between MATLAB and H5.

| MATLAB | H5 | Verification |
|--------|-----|--------------|
| `track.trackNum` | Key suffix in `track_XXX` | Must match |
| Array index | H5 key order | **DO NOT USE** - order not guaranteed |

**Correct Approach**:
```matlab
% MATLAB: Get track by number
target_track_num = 5;
for i = 1:length(tracks)
    if tracks(i).trackNum == target_track_num
        t = tracks(i);
        break;
    end
end
```

```python
# Python: Get track by number
target_track_num = 5
track_key = f"track_{target_track_num:03d}"
if track_key in f['tracks']:
    track = f['tracks'][track_key]
```

---

## Potential Discrepancy Sources

1. **Array shape**: MATLAB (2,N) vs Python (N,2)
2. **Floating point precision**: Double vs float32
3. **Edge case handling**: Division by zero, empty arrays
4. **Track indexing**: 1-based vs 0-based
5. **lengthPerPixel computation**: Must use identical calibration method
6. **LED array alignment**: Time arrays must correspond exactly

---

## Validation Checklist

- [ ] All position arrays have identical values (shead, smid, sloc/loc)
- [ ] Time arrays (eti) match exactly
- [ ] lengthPerPixel values match within 1e-12
- [ ] LED arrays (led1Val, led2Val) match exactly
- [ ] Track count matches
- [ ] Track numbering (not index) matches
- [ ] HeadUnitVec values match within 1e-10
- [ ] VelocityVec values match within 1e-10
- [ ] SpeedRun values match within 1e-10
- [ ] CosThetaFactor values match within 1e-10
- [ ] SpeedRunVel values match within 1e-10
- [ ] Reversal counts match exactly
- [ ] Reversal indices match exactly
- [ ] Reversal times match within 0.001s

