"""
copy_validated_h5s.py - Copy all validated H5 files to INDYsim repository

Creates:
  D:\INDYsim\data\h5_validated\
    ├── GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202509051125.h5
    ├── GMR61@GMR61_T_Re_Sq_0to250PWM_30#C_Bl_7PWM_202509051201.h5
    ├── ...
    └── manifest.json

manifest.json contains:
  - Source paths
  - Validation timestamps
  - File checksums (MD5)
"""

import sys
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime


def md5_checksum(file_path: Path) -> str:
    """Compute MD5 checksum of file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def main():
    BASE_DIR = Path(r"D:\rawdata\GMR61@GMR61")
    DEST_DIR = Path(r"D:\INDYsim\data\h5_validated")
    
    print("=" * 70)
    print("COPY VALIDATED H5 FILES TO INDYsim")
    print("=" * 70)
    print(f"Source: {BASE_DIR}")
    print(f"Destination: {DEST_DIR}")
    
    # Create destination directory
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all H5 files
    h5_files = []
    for eset_dir in sorted(BASE_DIR.iterdir()):
        if not eset_dir.is_dir():
            continue
        h5_dir = eset_dir / "h5_exports"
        if h5_dir.exists():
            for h5_file in sorted(h5_dir.glob("*.h5")):
                h5_files.append((eset_dir.name, h5_file))
    
    print(f"\nFound {len(h5_files)} H5 files to copy\n")
    
    # Copy files and build manifest
    manifest = {
        "created": datetime.now().isoformat(),
        "source_base": str(BASE_DIR),
        "destination": str(DEST_DIR),
        "validation_date": "2025-12-04",
        "files": []
    }
    
    for eset_name, src_path in h5_files:
        dest_path = DEST_DIR / src_path.name
        
        print(f"Copying: {src_path.name}")
        print(f"  From: {src_path.parent}")
        
        # Copy file
        shutil.copy2(src_path, dest_path)
        
        # Compute checksum
        checksum = md5_checksum(dest_path)
        file_size = dest_path.stat().st_size
        
        manifest["files"].append({
            "filename": src_path.name,
            "eset": eset_name,
            "source_path": str(src_path),
            "md5": checksum,
            "size_bytes": file_size
        })
        
        print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
        print(f"  MD5: {checksum}")
    
    # Write manifest
    manifest_path = DEST_DIR / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n{'=' * 70}")
    print("COPY COMPLETE")
    print(f"{'=' * 70}")
    print(f"Files copied: {len(h5_files)}")
    print(f"Manifest: {manifest_path}")
    print(f"Destination: {DEST_DIR}")
    
    # List final contents
    print(f"\nContents of {DEST_DIR}:")
    for f in sorted(DEST_DIR.iterdir()):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.name} ({size_mb:.2f} MB)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

