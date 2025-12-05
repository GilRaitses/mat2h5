"""
camera_calibration.py - Camera calibration utilities for H5 files

Provides functions to load and use camera calibration data from H5 files.
The calibration converts between camera (pixel) and real (cm) coordinates.

Usage:
    from camera_calibration import CameraCalibration
    
    calib = CameraCalibration.from_h5(h5_file)
    real_x, real_y = calib.cam_to_real(pixel_x, pixel_y)
    pixel_x, pixel_y = calib.real_to_cam(real_x, real_y)
"""

import numpy as np
import h5py
from scipy.interpolate import LinearNDInterpolator
from pathlib import Path
from typing import Tuple, Optional


class CameraCalibration:
    """
    Camera calibration for converting between pixel and real-world coordinates.
    
    Reconstructs the same interpolation as MATLAB's TriScatteredInterp using
    scipy.interpolate.LinearNDInterpolator.
    """
    
    def __init__(self, realx: np.ndarray, realy: np.ndarray, 
                 camx: np.ndarray, camy: np.ndarray,
                 length_per_pixel: float):
        """
        Initialize calibration from point arrays.
        
        Args:
            realx: Real-world X coordinates of calibration points
            realy: Real-world Y coordinates of calibration points
            camx: Camera (pixel) X coordinates of calibration points
            camy: Camera (pixel) Y coordinates of calibration points
            length_per_pixel: Pre-computed cm/pixel value
        """
        self.realx = np.asarray(realx).flatten()
        self.realy = np.asarray(realy).flatten()
        self.camx = np.asarray(camx).flatten()
        self.camy = np.asarray(camy).flatten()
        self.length_per_pixel = length_per_pixel
        
        # Build interpolators (same as MATLAB c2rX, c2rY, r2cX, r2cY)
        cam_points = np.column_stack([self.camx, self.camy])
        real_points = np.column_stack([self.realx, self.realy])
        
        # Camera → Real (c2r)
        self._c2rX = LinearNDInterpolator(cam_points, self.realx)
        self._c2rY = LinearNDInterpolator(cam_points, self.realy)
        
        # Real → Camera (r2c)
        self._r2cX = LinearNDInterpolator(real_points, self.camx)
        self._r2cY = LinearNDInterpolator(real_points, self.camy)
    
    @classmethod
    def from_h5(cls, h5_file) -> 'CameraCalibration':
        """
        Load calibration from H5 file.
        
        Args:
            h5_file: Path to H5 file or open h5py.File handle
        
        Returns:
            CameraCalibration instance
        """
        should_close = False
        
        if isinstance(h5_file, (str, Path)):
            h5_file = h5py.File(str(h5_file), 'r')
            should_close = True
        
        try:
            # Get lengthPerPixel
            if 'lengthPerPixel' in h5_file:
                length_per_pixel = float(h5_file['lengthPerPixel'][()])
            elif 'camcalinfo' in h5_file and 'lengthPerPixel' in h5_file['camcalinfo'].attrs:
                length_per_pixel = float(h5_file['camcalinfo'].attrs['lengthPerPixel'])
            else:
                raise ValueError("lengthPerPixel not found in H5 file")
            
            # Get calibration point arrays
            if 'camcalinfo' not in h5_file:
                raise ValueError("camcalinfo group not found in H5 file")
            
            cc = h5_file['camcalinfo']
            
            required = ['realx', 'realy', 'camx', 'camy']
            for field in required:
                if field not in cc:
                    raise ValueError(f"camcalinfo/{field} not found in H5 file")
            
            realx = cc['realx'][:]
            realy = cc['realy'][:]
            camx = cc['camx'][:]
            camy = cc['camy'][:]
            
            return cls(realx, realy, camx, camy, length_per_pixel)
        
        finally:
            if should_close:
                h5_file.close()
    
    def cam_to_real(self, cam_x: np.ndarray, cam_y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert camera (pixel) coordinates to real-world (cm) coordinates.
        
        Equivalent to MATLAB: real_x = cc.c2rX(cam_x, cam_y)
        
        Args:
            cam_x: Camera X coordinates (pixels)
            cam_y: Camera Y coordinates (pixels)
        
        Returns:
            (real_x, real_y): Real-world coordinates (cm)
        """
        cam_x = np.asarray(cam_x)
        cam_y = np.asarray(cam_y)
        
        real_x = self._c2rX(cam_x, cam_y)
        real_y = self._c2rY(cam_x, cam_y)
        
        return real_x, real_y
    
    def real_to_cam(self, real_x: np.ndarray, real_y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert real-world (cm) coordinates to camera (pixel) coordinates.
        
        Equivalent to MATLAB: cam_x = cc.r2cX(real_x, real_y)
        
        Args:
            real_x: Real-world X coordinates (cm)
            real_y: Real-world Y coordinates (cm)
        
        Returns:
            (cam_x, cam_y): Camera coordinates (pixels)
        """
        real_x = np.asarray(real_x)
        real_y = np.asarray(real_y)
        
        cam_x = self._r2cX(real_x, real_y)
        cam_y = self._r2cY(real_x, real_y)
        
        return cam_x, cam_y
    
    def pixels_to_cm(self, pixels: np.ndarray) -> np.ndarray:
        """
        Convert distance in pixels to cm using lengthPerPixel.
        
        Args:
            pixels: Distance in pixels
        
        Returns:
            Distance in cm
        """
        return np.asarray(pixels) * self.length_per_pixel
    
    def cm_to_pixels(self, cm: np.ndarray) -> np.ndarray:
        """
        Convert distance in cm to pixels using lengthPerPixel.
        
        Args:
            cm: Distance in cm
        
        Returns:
            Distance in pixels
        """
        return np.asarray(cm) / self.length_per_pixel


def load_calibration(h5_path: Path) -> Optional[CameraCalibration]:
    """
    Convenience function to load calibration from H5 file.
    
    Args:
        h5_path: Path to H5 file
    
    Returns:
        CameraCalibration instance or None if not available
    """
    try:
        return CameraCalibration.from_h5(h5_path)
    except Exception as e:
        print(f"Warning: Could not load calibration from {h5_path}: {e}")
        return None


if __name__ == '__main__':
    # Test with an H5 file
    import sys
    
    if len(sys.argv) > 1:
        h5_path = Path(sys.argv[1])
    else:
        h5_path = Path(r"D:\rawdata\GMR61@GMR61\T_Re_Sq_50to250PWM_30#C_Bl_7PWM\h5_exports\GMR61@GMR61_T_Re_Sq_50to250PWM_30#C_Bl_7PWM_202506251614.h5")
    
    print(f"Loading calibration from: {h5_path.name}")
    
    calib = CameraCalibration.from_h5(h5_path)
    
    print(f"lengthPerPixel: {calib.length_per_pixel:.8f} cm/pixel")
    print(f"Calibration points: {len(calib.realx)}")
    
    # Test conversion
    test_cam_x = np.array([100, 500, 1000])
    test_cam_y = np.array([100, 500, 1000])
    
    real_x, real_y = calib.cam_to_real(test_cam_x, test_cam_y)
    print(f"\nTest conversion (cam → real):")
    for i in range(len(test_cam_x)):
        print(f"  ({test_cam_x[i]}, {test_cam_y[i]}) pixels → ({real_x[i]:.4f}, {real_y[i]:.4f}) cm")
    
    # Round-trip test
    cam_x_back, cam_y_back = calib.real_to_cam(real_x, real_y)
    print(f"\nRound-trip error:")
    for i in range(len(test_cam_x)):
        err_x = abs(cam_x_back[i] - test_cam_x[i])
        err_y = abs(cam_y_back[i] - test_cam_y[i])
        print(f"  Point {i}: err_x={err_x:.6f}, err_y={err_y:.6f} pixels")

