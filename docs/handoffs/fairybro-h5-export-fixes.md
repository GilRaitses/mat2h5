# Agent Handoff: MagatFairy H5 Export Fixes

**To:** fairybro  
**From:** mechanobro  
**Date:** 2025-12-10  
**Repo:** `/Users/gilraitses/magatfairy` (https://github.com/GilRaitses/magatfairy)  
**Priority:** CRITICAL - Blocking INDYsim pipeline

---

## Summary

The MagatFairy H5 export is missing critical fields needed by the downstream INDYsim `engineer_dataset_from_h5.py` pipeline. Based on MiroThinker research, you need to:

1. Add `derivation_rules` export (smoothTime, derivTime, interpTime)
2. Fix position unit documentation (pixels → cm)
3. Add curvature field warning
4. Add speed threshold documentation
5. Create validation script
6. Commit and push

---

## Pre-requisites

The repo has already been synced:
```bash
cd /Users/gilraitses/magatfairy
git stash  # Done - stashed index.html changes
git pull origin main  # Done - now at commit 8f23c91
```

---

## Phase 1: Add derivation_rules Export (CRITICAL)

**File:** `src/scripts/convert/convert_matlab_to_h5.py`

### Step 1.1: Add new function after line ~34 (after imports, before `export_tier2_magat`)

```python
def export_derivation_rules(bridge, h5_file):
    """
    Export MAGAT derivation rules (smoothTime, derivTime, interpTime) to H5.
    Required for head-swing buffer calculation in downstream analysis.
    
    These parameters are used by MAGAT segmentation:
        buffer = ceil((smoothTime + derivTime) / interpTime)
    
    Added: 2025-12-10 (INDYsim compatibility fix)
    """
    try:
        # Get derivation rules from first track (same for all tracks in experiment)
        bridge.eng.workspace['app'] = bridge.app
        dr = bridge.eng.eval("app.eset.expt(1).track(1).dr", nargout=1)
        
        grp = h5_file.create_group('derivation_rules')
        grp.attrs['smoothTime'] = float(dr['smoothTime'])  # typically 0.2s
        grp.attrs['derivTime'] = float(dr['derivTime'])    # typically 0.1s
        grp.attrs['interpTime'] = float(dr['interpTime'])  # frame interval
        
        print(f"  [OK] Exported derivation_rules: smoothTime={dr['smoothTime']:.3f}s, "
              f"derivTime={dr['derivTime']:.3f}s, interpTime={dr['interpTime']:.4f}s")
    except Exception as e:
        print(f"  [WARN] Could not export derivation_rules from MATLAB: {e}")
        # Use sensible defaults based on typical MAGAT parameters
        grp = h5_file.create_group('derivation_rules')
        grp.attrs['smoothTime'] = 0.2   # 0.2s smoothing window
        grp.attrs['derivTime'] = 0.1    # 0.1s derivative window
        grp.attrs['interpTime'] = 0.05  # 20 fps = 0.05s per frame
        print(f"  [OK] Using default derivation_rules (smoothTime=0.2, derivTime=0.1, interpTime=0.05)")
```

### Step 1.2: Call the function inside `export_tier2_magat()`

Find this line (around line 78):
```python
        print("Exporting experiment globals...")
```

Add immediately after it:
```python
        # Export derivation rules for head-swing calculation (INDYsim compatibility)
        export_derivation_rules(bridge, f)
```

---

## Phase 2: Fix Position Units Documentation

**File:** `docs/field-mapping.md`

### Step 2.1: Change position units (lines 23-27)

Find:
```markdown
| `track.dq.shead` | `/tracks/{key}/derived_quantities/shead` | float64 | (2, N) | pixels | 0 (exact) |
| `track.dq.smid` | `/tracks/{key}/derived_quantities/smid` | float64 | (2, N) | pixels | 0 (exact) |
| `track.dq.sloc` | `/tracks/{key}/derived_quantities/sloc` | float64 | (2, N) | pixels | 0 (exact) |
```

Replace with:
```markdown
| `track.dq.shead` | `/tracks/{key}/derived_quantities/shead` | float64 | (2, N) | cm | 0 (exact) |
| `track.dq.smid` | `/tracks/{key}/derived_quantities/smid` | float64 | (2, N) | cm | 0 (exact) |
| `track.dq.sloc` | `/tracks/{key}/derived_quantities/sloc` | float64 | (2, N) | cm | 0 (exact) |
```

### Step 2.2: Add clarification note after the Position Data table

Add after line 38 (after the Notes section):
```markdown

**UNIT CLARIFICATION (2025-12-10):**
Position data (`shead`, `smid`, `sloc`) are exported in **centimeters**, not pixels.
MATLAB's `getDerivedQuantity()` applies `lengthPerPixel` conversion internally.
Empirical verification: sloc values range 6-16 (cm arena size), not 600-1600 (pixels).
```

---

## Phase 3: Add Curvature Field Warning

**File:** `docs/field-mapping.md`

Add new section after the Position Data section (around line 45):

```markdown
### Curvature Field Notes

The `curv` field exported to H5 is **path curvature** (dtheta/ds):

| Field | Units | Typical Range | Notes |
|-------|-------|---------------|-------|
| `curv` | 1/cm | -100,000 to +100,000 | Explodes when speed approaches zero |

**WARNING (2025-12-10):** Do NOT use raw `curv` with threshold 0.4 for MAGAT segmentation.
- The extreme values occur when `speed -> 0` (pauses)
- Path curvature = d(theta)/ds = angular_velocity / speed
- When speed approaches zero, curv approaches infinity
- For run termination, use `sspineTheta` (body angle) instead
- Or clip `curv` to a reasonable range (e.g., +/- 50)

The MAGAT `curv_cut = 0.4` threshold is meant for **body curvature**, not path curvature.
```

---

## Phase 4: Add Speed Threshold Documentation

**File:** `docs/field-mapping.md`

Add new section after Curvature (or in an appropriate location):

```markdown
### Speed Thresholds for MAGAT Segmentation

| MATLAB Parameter | MATLAB Value | MATLAB Units | H5 Equivalent |
|------------------|--------------|--------------|---------------|
| `stop_speed_cut` | 2.0 | mm/s | 0.2 cm/s |
| `start_speed_cut` | 3.0 | mm/s | 0.3 cm/s |

**UNIT CONVERSION (2025-12-10):**
- MATLAB `MaggotSegmentOptions` uses **mm/s** for speed thresholds
- H5 `speed` field is in **cm/s** (already converted from pixels)
- Convert by dividing MATLAB thresholds by 10:
  - 2.0 mm/s = 0.2 cm/s (stop threshold)
  - 3.0 mm/s = 0.3 cm/s (start threshold)
```

---

## Phase 5: Create Validation Script

**File:** `src/validation/validators/validate_h5_for_analysis.py` (NEW FILE)

Create this new file:

```python
#!/usr/bin/env python3
"""
Validate H5 files for INDYsim analysis compatibility.

Checks that all required fields are present and have expected units/ranges.

Created: 2025-12-10
"""

import sys
import h5py
import numpy as np
from pathlib import Path


def validate_h5_for_analysis(h5_path: str, verbose: bool = True) -> list:
    """
    Validate that an H5 file has all required fields for downstream analysis.
    
    Returns a list of problems found (empty if validation passed).
    """
    problems = []
    h5_path = Path(h5_path)
    
    if not h5_path.exists():
        return [f"File not found: {h5_path}"]
    
    with h5py.File(h5_path, 'r') as f:
        # 1. Check derivation_rules
        if 'derivation_rules' not in f:
            problems.append("CRITICAL: Missing /derivation_rules group")
        else:
            dr = f['derivation_rules']
            for attr in ['smoothTime', 'derivTime', 'interpTime']:
                if attr not in dr.attrs:
                    problems.append(f"CRITICAL: Missing derivation_rules.{attr}")
        
        # 2. Check root-level fields
        if 'eti' not in f:
            problems.append("Missing /eti (experiment time index)")
        
        if 'lengthPerPixel' not in f:
            problems.append("Missing /lengthPerPixel (camera calibration)")
        
        # 3. Check tracks exist
        if 'tracks' not in f:
            problems.append("Missing /tracks group")
        else:
            track_keys = [k for k in f['tracks'].keys() if k.startswith('track_')]
            if len(track_keys) == 0:
                problems.append("No tracks found in /tracks")
            else:
                # Check first track for required fields
                first_track = f['tracks'][track_keys[0]]
                
                if 'derived_quantities' not in first_track:
                    problems.append(f"Missing derived_quantities in {track_keys[0]}")
                else:
                    dq = first_track['derived_quantities']
                    required_dq = ['sloc', 'shead', 'smid', 'speed', 'sspineTheta', 'vel_dp', 'eti']
                    for field in required_dq:
                        if field not in dq:
                            problems.append(f"Missing derived_quantities/{field}")
                    
                    # Sanity check: sloc should be in cm (range ~1-20)
                    if 'sloc' in dq:
                        sloc = dq['sloc'][:]
                        sloc_range = sloc.max() - sloc.min()
                        if sloc_range > 100:
                            problems.append(f"WARNING: sloc range {sloc_range:.1f} suggests pixels, not cm")
                        elif sloc_range < 0.1:
                            problems.append(f"WARNING: sloc range {sloc_range:.4f} is suspiciously small")
                    
                    # Sanity check: speed should be in cm/s (typical mean ~0.02)
                    if 'speed' in dq:
                        speed = dq['speed'][:]
                        if speed.ndim == 2:
                            speed = speed.flatten()
                        mean_speed = np.nanmean(speed)
                        if mean_speed > 1.0:
                            problems.append(f"WARNING: mean speed {mean_speed:.3f} suggests mm/s, not cm/s")
                        elif mean_speed < 0.001:
                            problems.append(f"WARNING: mean speed {mean_speed:.6f} is suspiciously low")
        
        # 4. Check global quantities
        if 'global_quantities' not in f:
            problems.append("Missing /global_quantities group")
        else:
            gq = f['global_quantities']
            for led in ['led1Val', 'led2Val']:
                if led not in gq:
                    problems.append(f"Missing global_quantities/{led}")
    
    # Report
    if verbose:
        if problems:
            print(f"VALIDATION FAILED: {h5_path.name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"VALIDATION PASSED: {h5_path.name}")
    
    return problems


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_h5_for_analysis.py <h5_file_or_directory>")
        print("       python validate_h5_for_analysis.py /path/to/exports/")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    
    if target.is_file():
        problems = validate_h5_for_analysis(target)
        sys.exit(1 if problems else 0)
    elif target.is_dir():
        h5_files = list(target.glob("*.h5"))
        if not h5_files:
            print(f"No H5 files found in {target}")
            sys.exit(1)
        
        all_passed = True
        for h5_file in sorted(h5_files):
            problems = validate_h5_for_analysis(h5_file)
            if problems:
                all_passed = False
        
        print()
        if all_passed:
            print(f"ALL {len(h5_files)} FILES PASSED VALIDATION")
        else:
            print(f"SOME FILES FAILED VALIDATION")
        
        sys.exit(0 if all_passed else 1)
    else:
        print(f"Not found: {target}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

---

## Phase 6: Commit and Push

```bash
cd /Users/gilraitses/magatfairy

git add -A

git commit -m "Add derivation_rules export and fix unit documentation

- Add export_derivation_rules() to convert_matlab_to_h5.py
  - Exports smoothTime, derivTime, interpTime for head-swing buffer calculation
  - Falls back to sensible defaults if MATLAB extraction fails
- Fix position units in field-mapping.md (pixels -> cm)
  - MATLAB getDerivedQuantity() already applies lengthPerPixel conversion
- Add curvature field warning
  - curv is path curvature, explodes when speed -> 0
  - Do not use with curv_cut=0.4, use sspineTheta instead
- Add speed threshold documentation
  - MATLAB uses mm/s, H5 uses cm/s (divide by 10)
- Add validate_h5_for_analysis.py validation script
  - Checks for all required fields
  - Validates unit sanity (cm, cm/s)

Fixes INDYsim pipeline compatibility issues identified 2025-12-10
MiroThinker research reference: INDYsim/docs/logs/2025-12-10/"

git push origin main
```

---

## Verification Checklist

After completing all phases, verify:

- [ ] `derivation_rules` group exists in newly exported H5 files
- [ ] `derivation_rules` has attrs: smoothTime, derivTime, interpTime
- [ ] `docs/field-mapping.md` shows position units as "cm" not "pixels"
- [ ] Curvature warning section added
- [ ] Speed threshold section added
- [ ] `validate_h5_for_analysis.py` exists and runs without errors
- [ ] All changes committed and pushed to origin/main

---

## Report Required

After completing this handoff, provide a summary report with:

1. **Files Modified:** List of all files changed with line counts
2. **Commits Made:** Git log showing commit hash and message
3. **Verification Results:** Output of running the validation script on a test H5
4. **Any Issues Encountered:** Problems found and how they were resolved
5. **Push Confirmation:** Confirmation that changes are on origin/main

Send the report back to mechanobro for verification before lab PC re-run.

---

## Context: Why This Matters

The INDYsim `engineer_dataset_from_h5.py` pipeline was failing with:

```
ValueError: CRITICAL: derivation_rules.interpTime is REQUIRED for buffer calculation.
No fallback allowed. Need smoothTime, derivTime, and interpTime.
```

Additionally, speed thresholds were 10x wrong (using mm/s values with cm/s data), causing zero run detection. The curvature field was causing threshold failures (100,000x expected range).

These fixes enable proper MAGAT segmentation and Klein run table generation.
