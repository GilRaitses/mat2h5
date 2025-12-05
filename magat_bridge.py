#!/usr/bin/env python3
"""
MAGAT Bridge - Interface between Python and MATLAB MAGAT Analyzer

This bridge provides a Python interface to the MATLAB MAGAT (Maggot Analysis Tool)
codebase, allowing Python scripts to load and export experiment data.

Author: Adapted for mat2h5 standalone tool
Date: 2025-12-04
"""

import matlab.engine
from pathlib import Path
import os


class MAGATBridge:
    """
    Bridge class for interfacing with MATLAB MAGAT Analyzer.
    
    This class manages the MATLAB engine and provides methods to load
    experiments and access data from the MAGAT codebase.
    """
    
    def __init__(self, matlab_classes_path=None, magat_codebase_path=None):
        """
        Initialize the MAGAT Bridge.
        
        Args:
            matlab_classes_path: Path to MATLAB custom classes (e.g., @DataManager)
                                 If None, will try to find from environment or use defaults
            magat_codebase_path: Path to MAGAT codebase (Matlab-Track-Analysis-SkanataLab)
                                 Required for loading experiments
        """
        # Get paths from arguments or environment
        if matlab_classes_path is None:
            matlab_classes_path = os.environ.get('MATLAB_CLASSES_PATH')
        if magat_codebase_path is None:
            magat_codebase_path = os.environ.get('MAGAT_CODEBASE')
        
        if magat_codebase_path is None:
            raise ValueError(
                "MAGAT codebase path is required. "
                "Provide it as argument or set MAGAT_CODEBASE environment variable."
            )
        
        self.matlab_classes_path = Path(matlab_classes_path) if matlab_classes_path else None
        self.magat_codebase_path = Path(magat_codebase_path)
        
        if not self.magat_codebase_path.exists():
            raise FileNotFoundError(
                f"MAGAT codebase not found: {self.magat_codebase_path}\n"
                f"Please ensure the codebase is cloned and the path is correct."
            )
        
        # Start MATLAB engine
        print("Starting MATLAB engine...")
        self.eng = matlab.engine.start_matlab()
        
        # Add paths to MATLAB
        print("Adding MATLAB paths...")
        
        # Add MAGAT codebase (use genpath to add all subdirectories)
        self.eng.addpath(self.eng.genpath(str(self.magat_codebase_path)), nargout=0)
        print(f"  Added: {self.magat_codebase_path}")
        
        # Add MATLAB classes if provided
        if self.matlab_classes_path and self.matlab_classes_path.exists():
            self.eng.addpath(str(self.matlab_classes_path), nargout=0)
            print(f"  Added: {self.matlab_classes_path}")
        
        # Initialize app (DataManager)
        print("Initializing MAGAT DataManager...")
        try:
            # Create DataManager instance
            # This assumes @DataManager class exists in matlab_classes_path or MAGAT codebase
            if self.matlab_classes_path and (self.matlab_classes_path / "@DataManager").exists():
                self.eng.eval("dm = DataManager();", nargout=0)
            else:
                # Try to create from MAGAT codebase
                self.eng.eval("dm = DataManager();", nargout=0)
            
            self.app = self.eng.workspace['dm']
            print("  [OK] DataManager initialized")
            
        except Exception as e:
            print(f"  [WARNING] Could not initialize DataManager: {e}")
            print("  Attempting alternative initialization...")
            # Alternative: try to create app directly
            try:
                self.eng.eval("app = MAGATAnalyzer();", nargout=0)
                self.app = self.eng.workspace['app']
                print("  [OK] MAGATAnalyzer initialized")
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to initialize MATLAB application. "
                    f"Original error: {e}\n"
                    f"Alternative error: {e2}\n"
                    f"Please ensure MAGAT codebase is properly set up."
                )
    
    def load_experiment(self, mat_file, tracks_dir, bin_file):
        """
        Load an experiment from MATLAB files.
        
        Args:
            mat_file: Path to .mat experiment file
            tracks_dir: Path to tracks directory
            bin_file: Path to .bin file
        """
        mat_file = Path(mat_file)
        tracks_dir = Path(tracks_dir)
        bin_file = Path(bin_file)
        
        if not mat_file.exists():
            raise FileNotFoundError(f"MAT file not found: {mat_file}")
        if not tracks_dir.exists():
            raise FileNotFoundError(f"Tracks directory not found: {tracks_dir}")
        if not bin_file.exists():
            raise FileNotFoundError(f"BIN file not found: {bin_file}")
        
        print(f"Loading experiment...")
        print(f"  MAT file: {mat_file.name}")
        print(f"  Tracks: {tracks_dir.name}")
        print(f"  BIN file: {bin_file.name}")
        
        # Set paths in MATLAB workspace
        self.eng.workspace['mat_file'] = str(mat_file.absolute())
        self.eng.workspace['tracks_dir'] = str(tracks_dir.absolute())
        self.eng.workspace['bin_file'] = str(bin_file.absolute())
        
        try:
            # Load experiment using DataManager
            # This assumes DataManager has a method to load experiments
            load_code = f"""
            app = DataManager();
            app.loadExperiment('{mat_file.absolute()}', '{tracks_dir.absolute()}', '{bin_file.absolute()}');
            """
            self.eng.eval(load_code, nargout=0)
            self.app = self.eng.workspace['app']
            
            print("  [OK] Experiment loaded")
            
        except Exception as e:
            # Try alternative loading method
            print(f"  [WARNING] Standard load failed: {e}")
            print("  Attempting alternative load method...")
            
            try:
                # Alternative: use ExperimentSet.fromFiles or similar
                alt_load_code = f"""
                eset = ExperimentSet.fromFiles('{mat_file.absolute()}', '{tracks_dir.absolute()}', '{bin_file.absolute()}');
                app = DataManager();
                app.eset = eset;
                """
                self.eng.eval(alt_load_code, nargout=0)
                self.app = self.eng.workspace['app']
                print("  [OK] Experiment loaded (alternative method)")
                
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to load experiment.\n"
                    f"Standard method error: {e}\n"
                    f"Alternative method error: {e2}\n"
                    f"Please check that files are valid MAGAT experiment files."
                )
    
    def detect_stimuli(self):
        """
        Detect stimulus onsets from the experiment.
        
        Returns:
            dict with 'onset_frames' (list of frame indices) and 'num_stimuli' (int)
        """
        try:
            self.eng.workspace['app'] = self.app
            # Try to detect stimuli from LED data or global quantities
            detect_code = """
            % Try to detect stimuli from LED1 global quantity
            if ~isempty(app.DataManager.eset.expt(1).globalQuantity)
                led1_idx = [];
                for i = 1:length(app.DataManager.eset.expt(1).globalQuantity)
                    if strcmpi(app.DataManager.eset.expt(1).globalQuantity(i).fieldname, 'led1Val')
                        led1_idx = i;
                        break;
                    end
                end
                if ~isempty(led1_idx)
                    led1_data = app.DataManager.eset.expt(1).globalQuantity(led1_idx).yData;
                    % Simple threshold-based detection
                    threshold = max(led1_data) * 0.5;
                    onset_frames = find(diff(led1_data > threshold) == 1) + 1;
                    num_stimuli = length(onset_frames);
                else
                    onset_frames = [];
                    num_stimuli = 0;
                end
            else
                onset_frames = [];
                num_stimuli = 0;
            end
            """
            self.eng.eval(detect_code, nargout=0)
            
            onset_frames = self.eng.workspace['onset_frames']
            num_stimuli = int(float(self.eng.workspace['num_stimuli']))
            
            # Convert MATLAB array to Python list
            if onset_frames.size > 0:
                onset_list = [int(x) for x in onset_frames.flatten()]
            else:
                onset_list = []
            
            return {
                'onset_frames': onset_list,
                'num_stimuli': num_stimuli
            }
            
        except Exception as e:
            print(f"  [WARNING] Could not detect stimuli: {e}")
            return {
                'onset_frames': [],
                'num_stimuli': 0
            }
    
    def close(self):
        """Close the MATLAB engine and clean up resources."""
        if hasattr(self, 'eng') and self.eng:
            print("Closing MATLAB engine...")
            try:
                self.eng.quit()
            except:
                pass
            self.eng = None

