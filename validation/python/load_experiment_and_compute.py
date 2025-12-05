"""
load_experiment_and_compute.py - Load H5 experiment and compute validation outputs

ORIGINAL MASON SCRIPTS REFERENCED:
  - Just_ReverseCrawl_Matlab.m (SpeedRunVel computation)
  - Behavior_analysis_ReverseCrawl_Stop_Continue_Turn_Matlab.m (reversal detection)
  Location: scripts/2025-11-20/mason's scritps/
  Documentation: scripts/2025-11-24/mason_scripts_documentation.qmd

This script loads actual experiment data from H5 and computes:
  - SpeedRunVel for each track (using Mason's dot product method)
  - Reversal detection (SpeedRunVel < 0 for >= 3 seconds)
  - LED-derived ton/toff stimulus windows

The outputs are compared with the MATLAB pipeline.

Experiment: GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_202506251614
"""

import numpy as np
import h5py
from pathlib import Path
import json
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def compute_heading_unit_vector(shead: np.ndarray, smid: np.ndarray) -> np.ndarray:
    """Compute normalized heading unit vector."""
    if shead.shape[0] != 2:
        shead = shead.T
    if smid.shape[0] != 2:
        smid = smid.T
    
    head_vec = shead - smid
    norms = np.sqrt(head_vec[0, :]**2 + head_vec[1, :]**2)
    norms[norms == 0] = 1.0
    head_unit_vec = head_vec / norms
    
    return head_unit_vec


def compute_velocity_and_speed(xpos, ypos, times):
    """Compute velocity unit vectors and speed."""
    dx = np.diff(xpos)
    dy = np.diff(ypos)
    dt = np.diff(times)
    
    distance = np.sqrt(dx**2 + dy**2)
    
    speed = np.zeros_like(distance)
    valid = dt > 0
    speed[valid] = distance[valid] / dt[valid]
    
    velocity_vec = np.zeros((2, len(dx)))
    valid_dist = distance > 0
    velocity_vec[0, valid_dist] = dx[valid_dist] / distance[valid_dist]
    velocity_vec[1, valid_dist] = dy[valid_dist] / distance[valid_dist]
    
    return velocity_vec, speed


def compute_speedrunvel(shead, smid, xpos, ypos, times, length_per_pixel=1.0):
    """Compute SpeedRunVel using dot product method."""
    xpos_cm = np.asarray(xpos).ravel() * length_per_pixel
    ypos_cm = np.asarray(ypos).ravel() * length_per_pixel
    times = np.asarray(times).ravel()
    
    head_unit_vec = compute_heading_unit_vector(shead, smid)
    velocity_vec, speed = compute_velocity_and_speed(xpos_cm, ypos_cm, times)
    
    N = len(times) - 1
    cos_theta = np.sum(velocity_vec * head_unit_vec[:, :N], axis=0)
    speedrunvel = speed * cos_theta
    times_out = times[:-1]
    
    return speedrunvel, times_out


def compute_speedrunvel_with_intermediates(shead, smid, xpos, ypos, times, length_per_pixel=1.0):
    """
    Compute SpeedRunVel and return ALL intermediate values for validation.
    
    Returns dict with:
        - HeadUnitVec: (2, N)
        - VelocityVec: (2, N-1)
        - SpeedRun: (N-1,)
        - CosThetaFactor: (N-1,)
        - SpeedRunVel: (N-1,)
        - times_srv: (N-1,)
    """
    xpos_cm = np.asarray(xpos).ravel() * length_per_pixel
    ypos_cm = np.asarray(ypos).ravel() * length_per_pixel
    times = np.asarray(times).ravel()
    
    # Step 1: HeadUnitVec
    head_unit_vec = compute_heading_unit_vector(shead, smid)
    
    # Step 2: VelocityVec and SpeedRun
    velocity_vec, speed_run = compute_velocity_and_speed(xpos_cm, ypos_cm, times)
    
    # Step 3: CosThetaFactor (dot product)
    N = len(times) - 1
    cos_theta_factor = np.sum(velocity_vec * head_unit_vec[:, :N], axis=0)
    
    # Step 4: SpeedRunVel
    speedrunvel = speed_run * cos_theta_factor
    times_out = times[:-1]
    
    return {
        'HeadUnitVec': head_unit_vec,
        'VelocityVec': velocity_vec,
        'SpeedRun': speed_run,
        'CosThetaFactor': cos_theta_factor,
        'SpeedRunVel': speedrunvel,
        'times_srv': times_out
    }


def detect_reversals(times, speedrunvel, min_duration=3.0):
    """Detect reversals where SpeedRunVel < 0 for >= min_duration."""
    times = np.asarray(times).ravel()
    speedrunvel = np.asarray(speedrunvel).ravel()
    
    reversals = []
    in_reversal = False
    start_idx = None
    start_time = None
    
    for i in range(len(speedrunvel)):
        is_negative = speedrunvel[i] < 0
        
        if is_negative and not in_reversal:
            in_reversal = True
            start_idx = i
            start_time = times[i]
        
        elif not is_negative and in_reversal:
            in_reversal = False
            if start_idx is not None:
                duration = times[i] - start_time
                if duration >= min_duration:
                    reversals.append({
                        'start_idx': start_idx,
                        'end_idx': i - 1,
                        'start_time': start_time,
                        'end_time': times[i - 1],
                        'duration': duration
                    })
            start_idx = None
    
    # Handle reversal at end
    if in_reversal and start_idx is not None:
        duration = times[-1] - start_time
        if duration >= min_duration:
            reversals.append({
                'start_idx': start_idx,
                'end_idx': len(speedrunvel) - 1,
                'start_time': start_time,
                'end_time': times[-1],
                'duration': duration
            })
    
    return reversals


def main():
    print("=" * 60)
    print("PYTHON Validation: Load H5 Experiment")
    print("=" * 60)
    print()
    
    # Configuration
    h5_dir = Path(r"D:\rawdata\GMR61@GMR61\T_Re_Sq_50to250PWM_30#C_Bl_7PWM\h5_exports")
    experiment_name = "GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_202506251614"
    h5_file = h5_dir / f"{experiment_name}.h5"
    
    output_dir = Path(__file__).parent.parent / "test_data"
    output_dir.mkdir(exist_ok=True)
    
    print(f"H5 File: {h5_file}")
    print()
    
    if not h5_file.exists():
        print(f"ERROR: H5 file not found: {h5_file}")
        return 1
    
    # Load H5 file
    print("--- Loading H5 Experiment ---")
    with h5py.File(str(h5_file), 'r') as f:
        # List available groups
        print(f"Root keys: {list(f.keys())}")
        
        # Get ETI (elapsed time) from root
        if 'eti' in f:
            global_eti = f['eti'][:]
            print(f"Global ETI: {len(global_eti)} points, range [{global_eti[0]:.2f}, {global_eti[-1]:.2f}]")
        
        # Get lengthPerPixel - check root first (new location), then metadata
        length_per_pixel = 0.01  # default
        if 'lengthPerPixel' in f:
            # New location: at root level
            length_per_pixel = float(f['lengthPerPixel'][()])
        elif 'metadata' in f:
            meta = f['metadata']
            if 'lengthPerPixel' in meta.attrs:
                length_per_pixel = float(meta.attrs['lengthPerPixel'])
            elif 'lengthPerPixel' in meta:
                length_per_pixel = float(meta['lengthPerPixel'][()])
        print(f"lengthPerPixel: {length_per_pixel:.8f} cm/pixel")
        
        # Get LED values (used for ton/toff stimulus integration windows)
        # H5 structure:
        #   /global_quantities/led1Val, led2Val = intensity values (yData)
        #   /eti = time array (xData) - LED values sampled at each frame
        print("\n--- Loading LED Values ---")
        led1_ydata = np.array([])  # LED intensity/PWM values
        led2_ydata = np.array([])
        led_xdata = np.array([])   # timestamps - shared (global eti)
        
        # LED time comes from global ETI (LED sampled at each frame)
        if 'eti' in f:
            led_xdata = f['eti'][:]
            print(f"LED time (from /eti): {len(led_xdata)} points")
        
        if 'global_quantities' in f:
            gq = f['global_quantities']
            print(f"  Available global quantities: {list(gq.keys())}")
            
            # LED1 values - could be dataset directly or group with yData inside
            if 'led1Val' in gq:
                led1_obj = gq['led1Val']
                if isinstance(led1_obj, h5py.Dataset):
                    led1_ydata = led1_obj[:]
                elif isinstance(led1_obj, h5py.Group) and 'yData' in led1_obj:
                    led1_ydata = led1_obj['yData'][:]
                else:
                    print(f"  WARNING: led1Val structure unknown: {type(led1_obj)}")
                if len(led1_ydata) > 0:
                    print(f"LED1 values: {len(led1_ydata)} points, range [{led1_ydata.min():.1f}, {led1_ydata.max():.1f}]")
            
            # LED2 values - could be dataset directly or group with yData inside
            if 'led2Val' in gq:
                led2_obj = gq['led2Val']
                if isinstance(led2_obj, h5py.Dataset):
                    led2_ydata = led2_obj[:]
                elif isinstance(led2_obj, h5py.Group) and 'yData' in led2_obj:
                    led2_ydata = led2_obj['yData'][:]
                else:
                    print(f"  WARNING: led2Val structure unknown: {type(led2_obj)}")
                if len(led2_ydata) > 0:
                    print(f"LED2 values: {len(led2_ydata)} points, range [{led2_ydata.min():.1f}, {led2_ydata.max():.1f}]")
        else:
            print("  No global_quantities group found")
        
        # Get tracks
        if 'tracks' not in f:
            print("ERROR: No tracks group in H5 file")
            return 1
        
        track_keys = list(f['tracks'].keys())
        print(f"\nFound {len(track_keys)} tracks")
        
        # Select track by NUMBER (not array index) - must match MATLAB selection
        # CRITICAL: Use track number for identity, NOT array position
        # See FIELD_MAPPING.md for explanation
        target_track_num = 1  # The track NUMBER we want
        
        # Find track by number
        track_key = None
        for key in track_keys:
            try:
                key_num = int(key.replace('track_', '').replace('track', ''))
                if key_num == target_track_num:
                    track_key = key
                    break
            except ValueError:
                continue
        
        if track_key is None:
            # Fallback: use first track but warn
            print(f"WARNING: Track number {target_track_num} not found. Using first track.")
            track_key = track_keys[0]
            try:
                target_track_num = int(track_key.replace('track_', '').replace('track', ''))
            except ValueError:
                target_track_num = 0
        
        print(f"\n--- Computing SpeedRunVel for Track Number {target_track_num} (key: {track_key}) ---")
        
        track = f['tracks'][track_key]
        
        # Get derived quantities
        dq = track['derived_quantities']
        
        # Get shead and smid
        shead = dq['shead'][:]
        smid = dq['smid'][:]
        print(f"shead shape: {shead.shape}")
        print(f"smid shape: {smid.shape}")
        
        # Get positions - use SMOOTHED location (sloc) to match MATLAB's getDerivedQuantity('sloc')
        # NOT points/loc which is raw location
        if 'sloc' in dq:
            loc = dq['sloc'][:]
        elif 'points' in track and 'loc' in track['points']:
            print("WARNING: Using points/loc (raw) instead of sloc (smoothed)")
            loc = track['points']['loc'][:]
        else:
            loc = None
        
        if loc is None:
            print("ERROR: Could not find position data")
            return 1
        
        print(f"loc shape: {loc.shape}")
        
        # Ensure correct shape (2, N)
        if loc.shape[0] == 2:
            xpos_pixels = loc[0, :]
            ypos_pixels = loc[1, :]
        else:
            xpos_pixels = loc[:, 0]
            ypos_pixels = loc[:, 1]
        
        # Get time
        if 'eti' in dq:
            times = dq['eti'][:]
        else:
            times = global_eti[:len(xpos_pixels)]
        
        times = np.asarray(times).ravel()
        print(f"Track has {len(times)} points")
        print(f"Time range: {times[0]:.2f} to {times[-1]:.2f} seconds")
    
    # Compute SpeedRunVel WITH ALL INTERMEDIATE VALUES for validation
    print("\n--- Computing SpeedRunVel (with intermediates) ---")
    intermediates = compute_speedrunvel_with_intermediates(
        shead, smid, xpos_pixels, ypos_pixels, times, length_per_pixel
    )
    
    speedrunvel = intermediates['SpeedRunVel']
    times_srv = intermediates['times_srv']
    
    print(f"HeadUnitVec shape: {intermediates['HeadUnitVec'].shape}")
    print(f"VelocityVec shape: {intermediates['VelocityVec'].shape}")
    print(f"SpeedRun shape: {intermediates['SpeedRun'].shape}, range: [{intermediates['SpeedRun'].min():.4f}, {intermediates['SpeedRun'].max():.4f}]")
    print(f"CosThetaFactor shape: {intermediates['CosThetaFactor'].shape}, range: [{intermediates['CosThetaFactor'].min():.4f}, {intermediates['CosThetaFactor'].max():.4f}]")
    print(f"SpeedRunVel computed: {len(speedrunvel)} values")
    print(f"SpeedRunVel range: [{speedrunvel.min():.4f}, {speedrunvel.max():.4f}]")
    print(f"Negative SpeedRunVel points: {np.sum(speedrunvel < 0)} ({100*np.sum(speedrunvel < 0)/len(speedrunvel):.1f}%)")
    
    # Detect reversals
    print("\n--- Detecting Reversals ---")
    min_duration = 3.0
    reversals = detect_reversals(times_srv, speedrunvel, min_duration)
    
    print(f"Reversals detected: {len(reversals)}")
    for i, rev in enumerate(reversals):
        print(f"  Reversal {i+1}: t={rev['start_time']:.2f} to {rev['end_time']:.2f} ({rev['duration']:.2f} s)")
    
    # Save outputs
    print("\n--- Saving Validation Data ---")
    
    # Summary JSON (human-readable)
    validation_data = {
        'experiment_name': experiment_name,
        'track_num': target_track_num,  # Use track NUMBER not index
        'track_key': track_key,  # H5 key for reference
        'length_per_pixel': length_per_pixel,
        'num_points': len(times),
        'time_range': [float(times[0]), float(times[-1])],
        'speedrunvel_range': [float(speedrunvel.min()), float(speedrunvel.max())],
        'num_reversals': len(reversals),
        'reversals': reversals
    }
    
    # Save as JSON
    json_output = output_dir / "python_validation_output.json"
    with open(json_output, 'w') as f:
        json.dump(validation_data, f, indent=2)
    print(f"Saved Python output to: {json_output}")
    
    # Save SpeedRunVel as CSV for comparison
    csv_output = output_dir / "python_speedrunvel.csv"
    np.savetxt(csv_output, np.column_stack([times_srv, speedrunvel]), delimiter=',')
    print(f"Saved SpeedRunVel CSV to: {csv_output}")
    
    # Save ALL data as NPZ for detailed validation comparison with MATLAB
    npz_output = output_dir / "python_validation_full.npz"
    np.savez(
        npz_output,
        # Input data
        times=times,
        xpos_pixels=xpos_pixels,
        ypos_pixels=ypos_pixels,
        shead=shead,
        smid=smid,
        # LED data (for ton/toff stimulus windows)
        # LED time is global ETI (shared), values are per-LED
        led_xdata=led_xdata,    # timestamps (from /eti)
        led1_ydata=led1_ydata,  # LED1 intensity/PWM values
        led2_ydata=led2_ydata,  # LED2 intensity/PWM values
        # Intermediate computations (must match MATLAB exactly)
        HeadUnitVec=intermediates['HeadUnitVec'],
        VelocityVec=intermediates['VelocityVec'],
        SpeedRun=intermediates['SpeedRun'],
        CosThetaFactor=intermediates['CosThetaFactor'],
        # Final outputs
        SpeedRunVel=speedrunvel,
        times_srv=times_srv,
        # Metadata
        length_per_pixel=np.array([length_per_pixel]),
        track_num=np.array([target_track_num]),
        # Reversal info
        num_reversals=np.array([len(reversals)]),
        reversal_start_times=np.array([r['start_time'] for r in reversals]) if reversals else np.array([]),
        reversal_end_times=np.array([r['end_time'] for r in reversals]) if reversals else np.array([]),
        reversal_durations=np.array([r['duration'] for r in reversals]) if reversals else np.array([])
    )
    print(f"Saved full validation data to: {npz_output}")
    
    print("\n" + "=" * 60)
    print("PYTHON Validation Complete")
    print("=" * 60)
    print(f"Track number {target_track_num} from {experiment_name}")
    print(f"SpeedRunVel: {len(speedrunvel)} values")
    print(f"Reversals: {len(reversals)} detected")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

