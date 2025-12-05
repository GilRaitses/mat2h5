"""
append_camcal_to_h5.py - Append full camera calibration to existing H5 files

This script adds the complete camera calibration (camcalinfo) to H5 files that
were exported without it. It reads from the source .mat file and appends to H5:

  /camcalinfo/                    # Camera calibration group
      @class_name                 # Original MATLAB class
      c2rX_coeffs                 # Coefficients for pixel->real X transform
      c2rY_coeffs                 # Coefficients for pixel->real Y transform  
      r2cX_coeffs                 # Coefficients for real->pixel X transform
      r2cY_coeffs                 # Coefficients for real->pixel Y transform
      arena_center_x              # Arena center in real coords
      arena_center_y
      arena_radius                # Arena radius in real coords
      
  /lengthPerPixel                 # Computed cm/pixel (at root for easy access)
  /metadata@lengthPerPixel        # Also in metadata attrs

Usage:
  python append_camcal_to_h5.py --mat <experiment.mat> --h5 <experiment.h5>
  python append_camcal_to_h5.py --eset-dir <eset_directory>  # Process all experiments

Author: mechanosensation validation framework
Date: 2025-12-04
"""

import sys
from pathlib import Path
import numpy as np
import h5py
import argparse


def get_camcal_from_mat(mat_file: Path) -> dict:
    """
    Extract full camera calibration from MATLAB experiment file.
    
    Args:
        mat_file: Path to experiment .mat file
    
    Returns:
        Dictionary with all camera calibration data
    """
    import matlab.engine
    
    print(f"  Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    
    try:
        # Add MAGAT paths
        eng.addpath(r"D:\mechanosensation\scripts\2025-10-16", nargout=0)
        eng.addpath(eng.genpath(r"d:\magniphyq\codebase\Matlab-Track-Analysis-SkanataLab"), nargout=0)
        
        # Load the experiment
        print(f"  Loading experiment: {mat_file.name}")
        eng.eval(f"load('{str(mat_file)}')", nargout=0)
        
        # Handle different variable names
        eng.eval("""
            if exist('experiment', 'var')
                eset = ExperimentSet();
                eset.expt = experiment;
                clear experiment;
            end
        """, nargout=0)
        
        # Extract camera calibration object
        print(f"  Extracting camcalinfo...")
        
        camcal_data = {}
        
        # Get class name
        eng.eval("cc = eset.expt(1).camcalinfo;", nargout=0)
        camcal_data['class_name'] = str(eng.eval("class(cc)", nargout=1))
        
        # Get all properties of camcalinfo
        props_code = """
            cc = eset.expt(1).camcalinfo;
            props = properties(cc);
            camcal_struct = struct();
            for i = 1:length(props)
                prop_name = props{i};
                try
                    val = cc.(prop_name);
                    if isnumeric(val) || islogical(val)
                        camcal_struct.(prop_name) = val;
                    elseif ischar(val) || isstring(val)
                        camcal_struct.(prop_name) = char(val);
                    end
                catch
                end
            end
        """
        eng.eval(props_code, nargout=0)
        
        # Get the struct
        camcal_struct = eng.workspace['camcal_struct']
        
        # Convert to Python dict
        if hasattr(camcal_struct, '_fieldnames'):
            for field in camcal_struct._fieldnames:
                val = getattr(camcal_struct, field)
                if val is not None:
                    if isinstance(val, str):
                        camcal_data[field] = val
                    else:
                        camcal_data[field] = np.array(val).flatten()
        
        # Compute lengthPerPixel
        print(f"  Computing lengthPerPixel...")
        lpp_code = """
            cc = eset.expt(1).camcalinfo;
            test_pixels_x = [100, 500];
            test_pixels_y = [100, 500];
            real_coords_x = cc.c2rX(test_pixels_x, test_pixels_y);
            real_coords_y = cc.c2rY(test_pixels_x, test_pixels_y);
            pixel_dist = sqrt((test_pixels_x(2) - test_pixels_x(1))^2 + (test_pixels_y(2) - test_pixels_y(1))^2);
            real_dist = sqrt((real_coords_x(2) - real_coords_x(1))^2 + (real_coords_y(2) - real_coords_y(1))^2);
            lengthPerPixel = real_dist / pixel_dist;
        """
        eng.eval(lpp_code, nargout=0)
        camcal_data['lengthPerPixel'] = float(eng.workspace['lengthPerPixel'])
        
        # Export calibration point arrays (for reconstructing interpolation in Python)
        # CameraCalibration class has: realx, realy, camx, camy (calibration grid points)
        # and c2rX, c2rY, r2cX, r2cY (TriScatteredInterp objects)
        print(f"  Extracting calibration point arrays...")
        
        calib_arrays = ['realx', 'realy', 'camx', 'camy']
        for arr_name in calib_arrays:
            try:
                eng.eval(f"calib_arr = cc.{arr_name};", nargout=0)
                val = eng.workspace['calib_arr']
                if val is not None:
                    arr = np.array(val).flatten()
                    if len(arr) > 0:
                        camcal_data[arr_name] = arr
                        print(f"    {arr_name}: {len(arr)} points")
            except Exception as e:
                print(f"    {arr_name}: not available ({e})")
        
        # Extract/compute triangulation for direct use in scipy
        # Two approaches: 
        #   1. Try to extract from TriScatteredInterp/scatteredInterpolant
        #   2. Compute fresh using delaunay() from camx/camy points
        print(f"  Computing Delaunay triangulation from calibration points...")
        
        try:
            # Compute triangulation directly from camx/camy (more robust than extracting)
            tri_code = """
                cc = eset.expt(1).camcalinfo;
                % Compute Delaunay triangulation from camera calibration points
                tri_connectivity = delaunay(cc.camx, cc.camy);  % [M x 3] triangle vertex indices (1-based)
                tri_points = [cc.camx(:), cc.camy(:)];  % [N x 2] points
                tri_num_triangles = size(tri_connectivity, 1);
                tri_num_points = size(tri_points, 1);
            """
            eng.eval(tri_code, nargout=0)
            
            tri_points = np.array(eng.workspace['tri_points'])
            tri_connectivity = np.array(eng.workspace['tri_connectivity']).astype(np.int32)
            num_triangles = int(eng.workspace['tri_num_triangles'])
            num_points = int(eng.workspace['tri_num_points'])
            
            # Convert to 0-based indexing for Python
            tri_connectivity = tri_connectivity - 1
            
            camcal_data['tri_points'] = tri_points
            camcal_data['tri_connectivity'] = tri_connectivity
            print(f"    tri_points: {tri_points.shape} ({num_points} vertices)")
            print(f"    tri_connectivity: {tri_connectivity.shape} ({num_triangles} triangles)")
            
        except Exception as e:
            print(f"    [WARNING] Triangulation computation failed: {e}")
            print(f"    (Interpolation can still be reconstructed from point arrays)")
        
        return camcal_data
        
    finally:
        eng.quit()


def append_camcal_to_h5(h5_file: Path, camcal_data: dict) -> bool:
    """
    Append full camera calibration to an existing H5 file.
    
    Args:
        h5_file: Path to H5 file
        camcal_data: Dictionary with camera calibration data
    
    Returns:
        True if successful
    """
    print(f"  Appending to H5: {h5_file.name}")
    
    comp = {'compression': 'gzip', 'compression_opts': 6}
    
    with h5py.File(str(h5_file), 'r+') as f:
        # Remove existing camcalinfo if present
        if 'camcalinfo' in f:
            print(f"    Removing existing /camcalinfo group")
            del f['camcalinfo']
        
        # Create camcalinfo group
        cc_grp = f.create_group('camcalinfo')
        print(f"    Created /camcalinfo group")
        
        # Add all fields
        for key, val in camcal_data.items():
            if key == 'class_name':
                cc_grp.attrs['class_name'] = val
                print(f"      @class_name = {val}")
            elif key == 'lengthPerPixel':
                # Skip - will add to root separately
                pass
            elif isinstance(val, str):
                cc_grp.attrs[key] = val
                print(f"      @{key} = {val}")
            elif isinstance(val, np.ndarray):
                if val.size > 0:
                    cc_grp.create_dataset(key, data=val, **comp)
                    print(f"      {key}: shape={val.shape}")
            elif isinstance(val, (int, float)):
                cc_grp.attrs[key] = val
                print(f"      @{key} = {val}")
        
        # Add lengthPerPixel to root for easy access
        length_per_pixel = camcal_data.get('lengthPerPixel', None)
        if length_per_pixel is not None:
            if 'lengthPerPixel' in f:
                del f['lengthPerPixel']
            f.create_dataset('lengthPerPixel', data=length_per_pixel)
            print(f"    Added /lengthPerPixel = {length_per_pixel:.8f}")
            
            # Add to metadata attrs
            if 'metadata' in f:
                f['metadata'].attrs['lengthPerPixel'] = length_per_pixel
                print(f"    Added /metadata@lengthPerPixel = {length_per_pixel:.8f}")
        
    return True


def process_eset_directory(eset_dir: Path):
    """
    Process all experiments in an eset directory.
    
    Looks for:
      - matfiles/*.mat (experiment files)
      - h5_exports/*.h5 (corresponding H5 files)
    """
    matfiles_dir = eset_dir / "matfiles"
    h5_dir = eset_dir / "h5_exports"
    
    if not matfiles_dir.exists():
        print(f"ERROR: matfiles directory not found: {matfiles_dir}")
        return False
    
    if not h5_dir.exists():
        print(f"ERROR: h5_exports directory not found: {h5_dir}")
        return False
    
    # Find all experiment .mat files (not track files)
    mat_files = [f for f in matfiles_dir.glob("*.mat") 
                 if "track" not in f.name.lower() and " - tracks" not in f.name]
    
    print(f"Found {len(mat_files)} experiment files")
    print()
    
    results = []
    
    for mat_file in mat_files:
        print(f"Processing: {mat_file.name}")
        
        # Find corresponding H5 file
        h5_file = h5_dir / f"{mat_file.stem}.h5"
        
        if not h5_file.exists():
            print(f"  WARNING: H5 file not found: {h5_file.name}")
            results.append((mat_file.name, "H5 not found"))
            continue
        
        try:
            # Get full camera calibration from MATLAB
            camcal_data = get_camcal_from_mat(mat_file)
            lpp = camcal_data.get('lengthPerPixel', 0)
            print(f"  lengthPerPixel = {lpp:.8f} cm/pixel")
            print(f"  Total camcal fields: {len(camcal_data)}")
            
            # Append to H5
            append_camcal_to_h5(h5_file, camcal_data)
            
            results.append((mat_file.name, f"OK: lpp={lpp:.8f}"))
            print(f"  [OK] Done\n")
            
        except Exception as e:
            print(f"  ERROR: {e}\n")
            import traceback
            traceback.print_exc()
            results.append((mat_file.name, f"ERROR: {e}"))
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, status in results:
        print(f"  {name}: {status}")
    
    return all("OK" in status for _, status in results)


def main():
    parser = argparse.ArgumentParser(
        description='Append lengthPerPixel from camera calibration to H5 files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single experiment
  python append_camcal_to_h5.py --mat experiment.mat --h5 experiment.h5
  
  # All experiments in an eset directory
  python append_camcal_to_h5.py --eset-dir D:\\rawdata\\GMR61@GMR61\\T_Re_Sq_50to250PWM_30#C_Bl_7PWM
  
  # All esets in a base directory (processes all subdirectories)
  python append_camcal_to_h5.py --base-dir D:\\rawdata\\GMR61@GMR61
        """
    )
    
    parser.add_argument('--mat', type=str, help='Path to experiment .mat file')
    parser.add_argument('--h5', type=str, help='Path to H5 file to update')
    parser.add_argument('--eset-dir', type=str, help='Path to eset directory (process all)')
    parser.add_argument('--base-dir', type=str, help='Path to base directory containing multiple esets')
    
    args = parser.parse_args()
    
    if args.base_dir:
        # Process all eset subdirectories
        base_dir = Path(args.base_dir)
        if not base_dir.exists():
            print(f"ERROR: Base directory not found: {base_dir}")
            return 1
        
        # Find all eset directories (contain matfiles/ subdirectory)
        eset_dirs = []
        for subdir in sorted(base_dir.iterdir()):
            if subdir.is_dir() and (subdir / 'matfiles').exists():
                eset_dirs.append(subdir)
        
        if not eset_dirs:
            print(f"No eset directories found in {base_dir}")
            return 1
        
        print("=" * 70)
        print(f"BATCH PROCESSING: {len(eset_dirs)} esets in {base_dir.name}")
        print("=" * 70)
        
        all_results = []
        for i, eset_dir in enumerate(eset_dirs, 1):
            print(f"\n[{i}/{len(eset_dirs)}] Processing: {eset_dir.name}")
            print("-" * 70)
            success = process_eset_directory(eset_dir)
            all_results.append((eset_dir.name, success))
        
        print("\n" + "=" * 70)
        print("BATCH SUMMARY")
        print("=" * 70)
        for name, success in all_results:
            status = "OK" if success else "FAILED"
            print(f"  {name}: {status}")
        
        total_ok = sum(1 for _, s in all_results if s)
        print(f"\nTotal: {total_ok}/{len(all_results)} esets processed successfully")
        
        return 0 if all(s for _, s in all_results) else 1
    
    elif args.eset_dir:
        # Process entire directory
        success = process_eset_directory(Path(args.eset_dir))
        return 0 if success else 1
    
    elif args.mat and args.h5:
        # Single file mode
        mat_file = Path(args.mat)
        h5_file = Path(args.h5)
        
        if not mat_file.exists():
            print(f"ERROR: MAT file not found: {mat_file}")
            return 1
        
        if not h5_file.exists():
            print(f"ERROR: H5 file not found: {h5_file}")
            return 1
        
        try:
            # Get full camera calibration
            camcal_data = get_camcal_from_mat(mat_file)
            lpp = camcal_data.get('lengthPerPixel', 0)
            print(f"lengthPerPixel = {lpp:.8f} cm/pixel")
            print(f"Total camcal fields: {len(camcal_data)}")
            
            # Append to H5
            append_camcal_to_h5(h5_file, camcal_data)
            print("[OK] Done")
            return 0
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

