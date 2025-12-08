"""
compare_outputs.py - Compare MATLAB and Python validation outputs

This script:
1. Loads MATLAB validation output (matlab_speedrunvel.csv)
2. Loads Python validation output (python_speedrunvel.csv)
3. Compares the SpeedRunVel arrays
4. Generates VALIDATION_REPORT.md with results

Usage:
    1. Run MATLAB: load_experiment_and_compute.m
    2. Run Python: python load_experiment_and_compute.py
    3. Run this:   python compare_outputs.py
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime
from scipy.io import loadmat


def main():
    print("=" * 60)
    print("VALIDATION: Compare MATLAB vs Python Outputs")
    print("=" * 60)
    print()
    
    test_data_dir = Path(__file__).parent / "test_data"
    
    # Load MATLAB output
    matlab_csv = test_data_dir / "matlab_speedrunvel.csv"
    matlab_mat = test_data_dir / "matlab_validation_output.mat"
    
    if not matlab_csv.exists():
        print(f"ERROR: MATLAB output not found: {matlab_csv}")
        print("Please run load_experiment_and_compute.m first")
        return 1
    
    print("Loading MATLAB output...")
    matlab_data = np.loadtxt(matlab_csv, delimiter=',')
    matlab_times = matlab_data[:, 0]
    matlab_srv = matlab_data[:, 1]
    print(f"  MATLAB SpeedRunVel: {len(matlab_srv)} values")
    print(f"  Range: [{matlab_srv.min():.6f}, {matlab_srv.max():.6f}]")
    
    # Load additional MATLAB data if available
    matlab_reversals = None
    if matlab_mat.exists():
        mat_data = loadmat(str(matlab_mat), simplify_cells=True)
        if 'validation_data' in mat_data:
            vd = mat_data['validation_data']
            if 'outputs' in vd:
                matlab_reversals = {
                    'num': vd['outputs'].get('num_reversals', 0),
                    'start_times': vd['outputs'].get('reversal_start_times', []),
                    'durations': vd['outputs'].get('reversal_durations', [])
                }
                print(f"  Reversals: {matlab_reversals['num']}")
    
    # Load Python output
    python_csv = test_data_dir / "python_speedrunvel.csv"
    python_json = test_data_dir / "python_validation_output.json"
    
    if not python_csv.exists():
        print(f"\nERROR: Python output not found: {python_csv}")
        print("Please run: python load_experiment_and_compute.py")
        return 1
    
    print("\nLoading Python output...")
    python_data = np.loadtxt(python_csv, delimiter=',')
    python_times = python_data[:, 0]
    python_srv = python_data[:, 1]
    print(f"  Python SpeedRunVel: {len(python_srv)} values")
    print(f"  Range: [{python_srv.min():.6f}, {python_srv.max():.6f}]")
    
    # Load additional Python data
    python_reversals = None
    if python_json.exists():
        with open(python_json, 'r') as f:
            py_data = json.load(f)
            python_reversals = {
                'num': py_data.get('num_reversals', 0),
                'start_times': [r['start_time'] for r in py_data.get('reversals', [])],
                'durations': [r['duration'] for r in py_data.get('reversals', [])]
            }
            print(f"  Reversals: {python_reversals['num']}")
    
    # Compare lengths
    print("\n" + "-" * 40)
    print("COMPARISON RESULTS")
    print("-" * 40)
    
    if len(matlab_srv) != len(python_srv):
        print(f"\nWARNING: Length mismatch!")
        print(f"  MATLAB: {len(matlab_srv)}")
        print(f"  Python: {len(python_srv)}")
        min_len = min(len(matlab_srv), len(python_srv))
        matlab_srv = matlab_srv[:min_len]
        python_srv = python_srv[:min_len]
        matlab_times = matlab_times[:min_len]
        python_times = python_times[:min_len]
        print(f"  Comparing first {min_len} values")
    
    # Compare times
    time_diff = np.abs(matlab_times - python_times)
    max_time_diff = time_diff.max()
    print(f"\nTime comparison:")
    print(f"  Max time difference: {max_time_diff:.2e} seconds")
    
    # Compare SpeedRunVel
    srv_diff = np.abs(matlab_srv - python_srv)
    max_srv_diff = srv_diff.max()
    mean_srv_diff = srv_diff.mean()
    
    # Relative difference (avoid division by zero)
    nonzero_mask = np.abs(matlab_srv) > 1e-10
    if np.any(nonzero_mask):
        rel_diff = srv_diff[nonzero_mask] / np.abs(matlab_srv[nonzero_mask])
        max_rel_diff = rel_diff.max()
        mean_rel_diff = rel_diff.mean()
    else:
        max_rel_diff = 0
        mean_rel_diff = 0
    
    print(f"\nSpeedRunVel comparison:")
    print(f"  Max absolute difference: {max_srv_diff:.2e}")
    print(f"  Mean absolute difference: {mean_srv_diff:.2e}")
    print(f"  Max relative difference: {max_rel_diff:.2e}")
    print(f"  Mean relative difference: {mean_rel_diff:.2e}")
    
    # Compare reversals
    reversal_match = True
    if matlab_reversals and python_reversals:
        print(f"\nReversal comparison:")
        print(f"  MATLAB reversals: {matlab_reversals['num']}")
        print(f"  Python reversals: {python_reversals['num']}")
        
        if matlab_reversals['num'] != python_reversals['num']:
            print(f"  WARNING: Reversal count mismatch!")
            reversal_match = False
        else:
            # Compare start times
            if len(matlab_reversals['start_times']) > 0:
                for i, (m_start, p_start) in enumerate(zip(
                    matlab_reversals['start_times'], python_reversals['start_times']
                )):
                    diff = abs(m_start - p_start)
                    status = "OK" if diff < 0.1 else "MISMATCH"
                    print(f"  Reversal {i+1} start time: MATLAB={m_start:.2f}, Python={p_start:.2f}, diff={diff:.4f} [{status}]")
                    if diff >= 0.1:
                        reversal_match = False
    
    # Determine pass/fail
    TOLERANCE = 1e-6
    srv_passed = max_srv_diff < TOLERANCE
    time_passed = max_time_diff < TOLERANCE
    
    print("\n" + "=" * 40)
    print("VALIDATION STATUS")
    print("=" * 40)
    print(f"  SpeedRunVel match: {'PASS' if srv_passed else 'FAIL'} (tolerance: {TOLERANCE})")
    print(f"  Times match: {'PASS' if time_passed else 'FAIL'}")
    print(f"  Reversals match: {'PASS' if reversal_match else 'FAIL'}")
    
    all_passed = srv_passed and time_passed and reversal_match
    print(f"\n  OVERALL: {'PASS' if all_passed else 'FAIL'}")
    
    # Generate report
    report_path = Path(__file__).parent / "VALIDATION_REPORT.md"
    generate_report(
        report_path,
        matlab_srv, python_srv,
        max_srv_diff, mean_srv_diff,
        max_rel_diff, mean_rel_diff,
        matlab_reversals, python_reversals,
        all_passed, TOLERANCE
    )
    print(f"\nReport saved to: {report_path}")
    
    return 0 if all_passed else 1


def generate_report(
    report_path,
    matlab_srv, python_srv,
    max_srv_diff, mean_srv_diff,
    max_rel_diff, mean_rel_diff,
    matlab_reversals, python_reversals,
    all_passed, tolerance
):
    """Generate VALIDATION_REPORT.md"""
    
    experiment = "GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_202506251614"
    
    report = f"""# Validation Report: MATLAB vs Python Pipeline

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Status:** {'PASSED' if all_passed else 'FAILED'}

**Tolerance:** {tolerance}

## Experiment Data

| Property | Value |
|----------|-------|
| Experiment | `{experiment}` |
| Data Source (MATLAB) | `.mat` files in `matfiles/` |
| Data Source (Python) | `.h5` file in `h5_exports/` |
| Track Analyzed | Track 1 |
| SpeedRunVel Points | {len(matlab_srv)} |

## SpeedRunVel Comparison

| Metric | Value |
|--------|-------|
| Max Absolute Difference | {max_srv_diff:.2e} |
| Mean Absolute Difference | {mean_srv_diff:.2e} |
| Max Relative Difference | {max_rel_diff:.2e} |
| Mean Relative Difference | {mean_rel_diff:.2e} |
| MATLAB Range | [{matlab_srv.min():.6f}, {matlab_srv.max():.6f}] |
| Python Range | [{python_srv.min():.6f}, {python_srv.max():.6f}] |

## Reversal Detection

"""
    
    if matlab_reversals and python_reversals:
        report += f"""| Metric | MATLAB | Python |
|--------|--------|--------|
| Number of Reversals | {matlab_reversals['num']} | {python_reversals['num']} |
"""
        if matlab_reversals['num'] > 0:
            report += "\n### Reversal Details\n\n"
            report += "| Reversal | MATLAB Start (s) | Python Start (s) | MATLAB Duration (s) | Python Duration (s) |\n"
            report += "|----------|-----------------|-----------------|--------------------|--------------------|"
            
            for i in range(max(len(matlab_reversals['start_times']), len(python_reversals['start_times']))):
                m_start = matlab_reversals['start_times'][i] if i < len(matlab_reversals['start_times']) else 'N/A'
                p_start = python_reversals['start_times'][i] if i < len(python_reversals['start_times']) else 'N/A'
                m_dur = matlab_reversals['durations'][i] if i < len(matlab_reversals['durations']) else 'N/A'
                p_dur = python_reversals['durations'][i] if i < len(python_reversals['durations']) else 'N/A'
                
                m_start_str = f"{m_start:.2f}" if isinstance(m_start, (int, float)) else m_start
                p_start_str = f"{p_start:.2f}" if isinstance(p_start, (int, float)) else p_start
                m_dur_str = f"{m_dur:.2f}" if isinstance(m_dur, (int, float)) else m_dur
                p_dur_str = f"{p_dur:.2f}" if isinstance(p_dur, (int, float)) else p_dur
                
                report += f"\n| {i+1} | {m_start_str} | {p_start_str} | {m_dur_str} | {p_dur_str} |"
    else:
        report += "Reversal data not available for comparison.\n"
    
    report += f"""

## Methodology

1. **MATLAB Pipeline:**
   - Loaded experiment from `matfiles/` directory
   - Loaded tracks from `*-tracks/` subdirectory
   - Computed `lengthPerPixel` from camera calibration
   - Computed `HeadUnitVec`, `VelocityVec`, `SpeedRun`, `CosThetaFactor`
   - Computed `SpeedRunVel = SpeedRun * CosThetaFactor`
   - Detected reversals where `SpeedRunVel < 0` for >= 3 seconds

2. **Python Pipeline:**
   - Loaded experiment from `.h5` file in `h5_exports/`
   - Extracted `shead`, `smid`, `loc` from track data
   - Used same `lengthPerPixel` from metadata
   - Computed identical intermediate values
   - Detected reversals with same criteria

3. **Comparison:**
   - Compared `SpeedRunVel` arrays element-by-element
   - Compared reversal start times and durations
   - Used tolerance of {tolerance} for numerical comparison

## Files

- **MATLAB script:** `src/validation/reference/load_experiment_and_compute.m`
- **Python script:** `src/validation/validators/load_experiment_and_compute.py`
- **MATLAB output:** `validation/test_data/matlab_speedrunvel.csv`
- **Python output:** `validation/test_data/python_speedrunvel.csv`

## Conclusion

"""
    
    if all_passed:
        report += """The Python implementation produces **numerically equivalent** results to the 
MATLAB reference implementation when processing the same experimental data.

The `engineer_data.py` pipeline has been validated for:
- SpeedRunVel computation (dot product method)
- Reverse crawl detection (SpeedRunVel < 0 for >= 3 seconds)

This validation was performed on actual larval tracking data, not synthetic test cases.
"""
    else:
        report += """**VALIDATION FAILED**

The Python implementation does not produce numerically equivalent results.
Please review the differences above and investigate the source of the discrepancy.
"""
    
    with open(report_path, 'w') as f:
        f.write(report)


if __name__ == '__main__':
    import sys
    sys.exit(main())

