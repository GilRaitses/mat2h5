import h5py
import os
from pathlib import Path

exports_dir = Path("exports")
files = sorted([f for f in exports_dir.glob("*.h5") if "GMR61@GMR61" in f.name])

print(f"Found {len(files)} H5 files")
if len(files) == 0:
    print("No files found yet - conversion may still be running")
    exit(0)

all_good = True
for f in files:
    try:
        with h5py.File(f, 'r') as h5:
            if 'stimulus' not in h5:
                print(f"{f.name}: MISSING stimulus group")
                all_good = False
            else:
                num_cycles = h5['stimulus'].attrs.get('num_cycles', 0)
                if 'onset_frames' in h5['stimulus']:
                    num_frames = len(h5['stimulus']['onset_frames'])
                else:
                    num_frames = 0
                print(f"{f.name}: cycles={num_cycles}, frames={num_frames}")
                if num_cycles == 0 or num_frames == 0:
                    all_good = False
    except Exception as e:
        print(f"{f.name}: ERROR - {e}")
        all_good = False

if all_good and len(files) == 14:
    print("\n[OK] All 14 files have valid stimulus data!")
    exit(0)
else:
    print(f"\n[WARNING] {len(files)} files found, but some may be missing stimulus data")
    exit(1)

