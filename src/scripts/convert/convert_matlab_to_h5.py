"""
H5 Export: Complete MAGAT Structure Export with ETI at Root

Exports complete experiment mirroring MAGAT hierarchy.
CRITICAL: Exports ETI (Experiment Time Index) to root for simulation scripts.

Source: Adapted from D:\mechanosensation\scripts\2025-11-10\H5_clone.py
MAGAT Bridge: D:\mechanosensation\mcp-servers\magat-bridge\server.py
MATLAB Classes: D:\mechanosensation\scripts\2025-10-16
MAGAT Codebase: d:\magniphyq\codebase\Matlab-Track-Analysis-SkanataLab

Author: mechanobro (adapted for INDYsim)
Date: 2025-11-11
"""

import sys
from pathlib import Path
import time
import numpy as np
import h5py
import os

# Import MAGAT Bridge from mat2h5 package
# Path: src/scripts/convert/
src_path = Path(__file__).parent.parent.parent / "mat2h5"
sys.path.insert(0, str(src_path.parent))

try:
    from mat2h5.bridge import MAGATBridge
except ImportError:
    # Fallback: try adding src to path
    sys.path.insert(0, str(src_path.parent))
    from mat2h5.bridge import MAGATBridge


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


def export_tier2_magat(bridge, output_file):
    """Export complete MAGAT structure with ETI at root"""
    
    print("=" * 70)
    print("H5 EXPORT: COMPLETE MAGAT STRUCTURE")
    print("=" * 70)
    print()
    
    # Ensure app is in MATLAB workspace
    bridge.eng.workspace['app'] = bridge.app
    info = bridge.eng.eval("app.getInfo()", nargout=1)
    num_tracks = int(float(info['num_tracks']))
    num_frames = int(float(info['num_frames']))
    
    print(f"Experiment: {num_tracks} tracks, {num_frames} frames")
    print(f"Exporting complete MAGAT structure (no FID)")
    print()
    
    start_time = time.time()
    comp = {'compression': 'gzip', 'compression_opts': 6}
    
    # Check if output file exists and handle locking
    output_path = Path(output_file)
    if output_path.exists():
        print(f"  Output file exists: {output_path.name}")
        try:
            output_path.unlink()
            print(f"  [OK] Removed existing file")
        except (OSError, PermissionError) as e:
            print(f"  [ERROR] Cannot remove existing file (locked): {output_path}")
            print(f"    Error: {e}")
            print(f"    Please close any programs using this file (HDFView, MATLAB, etc.)")
            print(f"    Or delete the file manually: {output_path}")
            print(f"    Skipping export for this experiment.")
            return {
                'success': False,
                'error': f"File locked: {e}",
                'output_file': str(output_path)
            }
    
    with h5py.File(output_file, 'w') as f:
        # === EXPERIMENT GLOBALS ===
        print("Exporting experiment globals...")
        
        # Export derivation rules for head-swing calculation (INDYsim compatibility)
        export_derivation_rules(bridge, f)
        
        bridge.eng.workspace['app'] = bridge.app
        expt_data = bridge.eng.eval("app.getCompleteExperiment()", nargout=1)
        
        # Experiment info
        if 'experiment' in expt_data and expt_data['experiment']:
            exp_grp = f.create_group('experiment_info')
            exp_dict = expt_data['experiment']
            
            for key in exp_dict.keys() if isinstance(exp_dict, dict) else dir(exp_dict):
                try:
                    val = exp_dict[key] if isinstance(exp_dict, dict) else getattr(exp_dict, key)
                    if isinstance(val, (str, int, float)):
                        exp_grp.attrs[key] = val
                except:
                    pass
        
        # Global quantities (ALL fields)
        gq_grp = f.create_group('global_quantities')
        
        bridge.eng.workspace['app'] = bridge.app
        num_gq = int(float(bridge.eng.eval("length(app.eset.expt(1).globalQuantity)", nargout=1)))
        
        print(f"  Exporting {num_gq} global quantities...")
        
        for i in range(1, num_gq + 1):
            bridge.eng.workspace['gq_idx'] = float(i)
            gq_field_data = bridge.eng.eval("app.getGlobalQuantity(gq_idx)", nargout=1)
            
            field_name = str(gq_field_data['fieldname']).replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
            field_grp = gq_grp.create_group(field_name)
            
            if 'yData' in gq_field_data:
                ydata = np.array(gq_field_data['yData']).flatten()
                field_grp.create_dataset('yData', data=ydata, **comp)
            
            field_grp.attrs['fieldname'] = str(gq_field_data['fieldname'])
        
        print(f"    [OK] {num_gq} global quantities exported")
        
        # === EXPORT ETI TO ROOT (CRITICAL FOR SIMULATION SCRIPTS) ===
        print(f"\n  Extracting ETI from experiment.elapsedTime...")
        bridge.eng.workspace['app'] = bridge.app
        eti_result = bridge.eng.eval("app.eset.expt(1).elapsedTime", nargout=1)
        
        if eti_result is not None:
            eti_data = np.array(eti_result).flatten()
            if len(eti_data) > 0:
                print(f"    [OK] Found elapsedTime: {len(eti_data)} frames")
                print(f"         Range: {eti_data[0]:.3f} to {eti_data[-1]:.3f} seconds")
                print(f"  Exporting ETI to root: {len(eti_data)} frames")
                f.create_dataset('eti', data=eti_data, **comp)
                print(f"    [OK] ETI exported to root")
            else:
                print(f"    [WARNING] elapsedTime array is empty!")
                eti_data = None
        else:
            print(f"    [WARNING] elapsedTime not found in experiment!")
            eti_data = None
        
        print("  [OK] Experiment globals exported\n")
        
        # === TRACKS ===
        print(f"Exporting {num_tracks} tracks with complete data...")
        tracks_grp = f.create_group('tracks')
        
        # Process tracks in sorted order (1, 2, 3, ..., num_tracks)
        # This ensures tracks are stored in H5 file in numeric order
        # H5 files preserve insertion order, so this guarantees track_1, track_2, ..., track_N
        for track_id in sorted(range(1, num_tracks + 1)):
            print(f"  Track {track_id}/{num_tracks}...", end=' ', flush=True)
            
            bridge.eng.workspace['track_id'] = float(track_id)
            track_data = bridge.eng.eval("app.getCompleteTrackData(track_id)", nargout=1)
            
            track_grp = tracks_grp.create_group(f'track_{track_id}')
            
            # Metadata
            if 'metadata' in track_data:
                meta_grp = track_grp.create_group('metadata')
                for key in track_data['metadata'].keys() if hasattr(track_data['metadata'], 'keys') else []:
                    val = track_data['metadata'][key]
                    if isinstance(val, (int, float)):
                        meta_grp.attrs[key] = float(val)
            
            # State arrays
            if 'state' in track_data:
                state_grp = track_grp.create_group('state')
                for key in track_data['state'].keys() if hasattr(track_data['state'], 'keys') else []:
                    val = track_data['state'][key]
                    if val is not None and len(val) > 0:
                        state_grp.create_dataset(key, data=np.array(val), **comp)
            
            # Points
            if 'points' in track_data:
                pts_grp = track_grp.create_group('points')
                
                pts_grp.create_dataset('mid', data=np.array(track_data['points']['mid']), **comp)
                pts_grp.create_dataset('head', data=np.array(track_data['points']['head']), **comp)
                pts_grp.create_dataset('tail', data=np.array(track_data['points']['tail']), **comp)
                
                if 'loc' in track_data['points']:
                    pts_grp.create_dataset('loc', data=np.array(track_data['points']['loc']), **comp)
                if 'area' in track_data['points']:
                    pts_grp.create_dataset('area', data=np.array(track_data['points']['area']), **comp)
                
                # Concatenated contours
                if len(track_data['points']['contour_points']) > 0:
                    pts_grp.create_dataset('contour_points', data=np.array(track_data['points']['contour_points']), **comp)
                    pts_grp.create_dataset('contour_indices', data=np.array(track_data['points']['contour_indices']), **comp)
                
                # Concatenated spine
                if len(track_data['points']['spine_points']) > 0:
                    pts_grp.create_dataset('spine_points', data=np.array(track_data['points']['spine_points']), **comp)
                    pts_grp.create_dataset('spine_indices', data=np.array(track_data['points']['spine_indices']), **comp)
            
            # Derived quantities (ALL fields)
            if 'derived' in track_data and track_data['derived']:
                deriv_grp = track_grp.create_group('derived_quantities')
                
                derived_dict = track_data['derived']
                for field_name in derived_dict.keys() if hasattr(derived_dict, 'keys') else []:
                    val = derived_dict[field_name]
                    if val is not None and len(val) > 0:
                        deriv_grp.create_dataset(field_name, data=np.array(val), **comp)
                        
            
            track_grp.attrs['id'] = track_id
            print("[OK]")
        
        print("  [OK] All tracks exported\n")
        
        # Stimulus + LED
        try:
            stimuli = bridge.detect_stimuli()
            stim_grp = f.create_group('stimulus')
            onset_frames = stimuli.get('onset_frames', [])
            num_stimuli = stimuli.get('num_stimuli', 0)
            
            if len(onset_frames) > 0:
                stim_grp.create_dataset('onset_frames', data=np.array(onset_frames, dtype=np.int32))
                stim_grp.attrs['num_cycles'] = num_stimuli
                print(f"  [OK] Detected {num_stimuli} stimulus onsets")
            else:
                stim_grp.create_dataset('onset_frames', data=np.array([], dtype=np.int32))
                stim_grp.attrs['num_cycles'] = 0
                print(f"  [WARNING] No stimulus onsets detected")
        except Exception as e:
            print(f"  [WARNING] Could not detect stimuli: {e}")
            import traceback
            traceback.print_exc()
            stim_grp = f.create_group('stimulus')
            stim_grp.create_dataset('onset_frames', data=np.array([], dtype=np.int32))
            stim_grp.attrs['num_cycles'] = 0
        
        try:
            bridge.eng.workspace['app'] = bridge.app
            led_data = bridge.eng.eval("app.led_data", nargout=1)
            if led_data is not None:
                f.create_dataset('led_data', data=np.array(led_data).flatten().astype(np.float32), **comp)
        except Exception as e:
            print(f"  [WARNING] Could not extract LED data: {e}")
        
        # Metadata
        meta_grp = f.create_group('metadata')
        meta_grp.attrs['num_tracks'] = num_tracks
        meta_grp.attrs['num_frames'] = num_frames
        meta_grp.attrs['export_tier'] = 2
        meta_grp.attrs['export_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        meta_grp.attrs['has_eti'] = eti_data is not None
        if eti_data is not None:
            meta_grp.attrs['eti_length'] = len(eti_data)
        
        # === EXPORT lengthPerPixel FROM CAMERA CALIBRATION ===
        # This is CRITICAL for converting pixel positions to real-world cm
        # MATLAB: cc = eset.expt(1).camcalinfo; lengthPerPixel = computed from c2rX/c2rY
        print("  Extracting lengthPerPixel from camera calibration...")
        try:
            bridge.eng.workspace['app'] = bridge.app
            # Compute lengthPerPixel using same method as MATLAB validation scripts
            lpp_code = """
            cc = app.eset.expt(1).camcalinfo;
            test_pixels_x = [100, 500];
            test_pixels_y = [100, 500];
            real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
            real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
            pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
            real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
            lengthPerPixel = real_dist / pixel_dist;
            """
            bridge.eng.eval(lpp_code, nargout=0)
            length_per_pixel = float(bridge.eng.workspace['lengthPerPixel'])
            
            # Save to root AND metadata for easy access
            f.create_dataset('lengthPerPixel', data=length_per_pixel)
            meta_grp.attrs['lengthPerPixel'] = length_per_pixel
            print(f"    [OK] lengthPerPixel = {length_per_pixel:.8f} cm/pixel")
        except Exception as e:
            print(f"    [WARNING] Could not extract lengthPerPixel: {e}")
            print(f"    Camera calibration may not be available for this experiment.")
    
    export_time = time.time() - start_time
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    
    print("=" * 70)
    print("H5 EXPORT COMPLETE!")
    print("=" * 70)
    print(f"File: {Path(output_file).name}")
    print(f"Size: {file_size:.1f} MB")
    print(f"Time: {export_time/60:.1f} minutes")
    if eti_data is not None:
        print(f"ETI: [OK] Exported to root ({len(eti_data)} frames)")
    else:
        print(f"ETI: [WARNING] NOT FOUND - simulation scripts may have timing issues!")
    print()
    
    return {'file_size_mb': file_size, 'time_min': export_time/60, 'has_eti': eti_data is not None}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='H5 Export: Export complete MAGAT structure with ETI at root')
    parser.add_argument('--mat', required=True, help='Path to .mat file')
    parser.add_argument('--tracks', required=True, help='Path to tracks directory')
    parser.add_argument('--bin', required=True, help='Path to .bin file')
    parser.add_argument('--output', required=True, help='Output H5 file path')
    parser.add_argument('--codebase', default=None, help='Path to MAGAT codebase (or set MAGAT_CODEBASE env var)')
    parser.add_argument('--matlab-classes', default=None, help='Path to MATLAB classes (optional)')
    args = parser.parse_args()
    
    # Get codebase path from argument or environment
    codebase_path = args.codebase or os.environ.get('MAGAT_CODEBASE')
    if not codebase_path:
        raise ValueError(
            "MAGAT codebase path is required. "
            "Provide --codebase argument or set MAGAT_CODEBASE environment variable."
        )
    
    print("Initializing MATLAB...")
    bridge = MAGATBridge(
        matlab_classes_path=args.matlab_classes,
        magat_codebase_path=codebase_path
    )
    
    bridge.load_experiment(args.mat, args.tracks, args.bin)
    
    stats = export_tier2_magat(bridge, args.output)
    
    bridge.close()
    return stats


if __name__ == "__main__":
    main()









