"""Quick check of camcal fields in all H5 files"""
import h5py
from pathlib import Path

BASE_DIR = Path(r"D:\rawdata\GMR61@GMR61")

print("=" * 70)
print("CAMCAL FIELDS CHECK")
print("=" * 70)

for eset_dir in sorted(BASE_DIR.iterdir()):
    if not eset_dir.is_dir():
        continue
    h5_dir = eset_dir / "h5_exports"
    if not h5_dir.exists():
        continue
    
    print(f"\n{eset_dir.name}:")
    for h5_file in sorted(h5_dir.glob("*.h5")):
        with h5py.File(str(h5_file), 'r') as f:
            has_lpp = 'lengthPerPixel' in f
            has_camcal = 'camcalinfo' in f
            
            fields = []
            has_tri = False
            if has_camcal:
                fields = list(f['camcalinfo'].keys())
                has_tri = 'tri_points' in f['camcalinfo']
            
            status = "✓" if (has_lpp and has_camcal and len(fields) >= 4) else "✗"
            tri_status = "TRI" if has_tri else "no-tri"
            print(f"  {status} {h5_file.name}: lpp={has_lpp}, fields={fields}, {tri_status}")

print("\n" + "=" * 70)
print("DONE")

