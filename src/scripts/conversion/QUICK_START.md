# Quick Start Guide - MATLAB to H5 Conversion

## Process Full Genotype Folder

### Option 1: Windows Batch Script (Easiest)
```bash
cd D:\INDYsim\src\@matlab_conversion
process_genotype.bat GMR61@GMR61
```

### Option 2: Python Script
```bash
cd D:\INDYsim\src\@matlab_conversion
python batch_export_esets.py --genotype "GMR61@GMR61"
```

## Process All Genotypes

```bash
cd D:\INDYsim\src\@matlab_conversion
process_all_genotypes.bat
```

## Process Specific ESET

```bash
cd D:\INDYsim\src\@matlab_conversion
python batch_export_esets.py --genotype "GMR61@GMR61" --eset "T_Re_Sq_0to250PWM_30#C_Bl_7PWM"
```

## Output Location

- Default: `D:\INDYsim\data\{base_name}.h5`
- Files are named to match experiment `.bin` filename (with `.h5` extension)

## Monitor Batch Processing

**Visual Monitor with Aurora Animation:**
```bash
cd D:\INDYsim\src\@matlab_conversion
open_eset_monitor.bat GMR61@GMR61
```

Or directly:
```bash
python monitor_eset_batch.py --genotype-dir "D:\INDYsim\data\matlab_data\GMR61@GMR61" --output-dir "D:\INDYsim\data"
```

**Features:**
- Each bubble/sphere represents an ESET folder
- Currently processing ESET is in center, largest, revolving, changing colors
- Blinking frequency proportional to tracks processed/total tracks
- Completed ESETs dissolve into aurora-colored wind/dust clouds
- Aurora curtain grows as ESETs are processed

## Troubleshooting

### File Locked (Error 33)
```bash
python unlock_h5_file.py --file "path/to/file.h5" --check
python unlock_h5_file.py --file "path/to/file.h5" --force-delete
```

### Check File Integrity
```bash
python unlock_h5_file.py --file "path/to/file.h5" --check
```

## What Gets Exported

- ✅ ETI at root level (CRITICAL for simulation scripts)
- ✅ All tracks with complete data (points, derived quantities, state, metadata)
- ✅ Global quantities (LED values, derivatives)
- ✅ Stimulus onset frames
- ✅ LED data array
- ✅ Experiment metadata

## See Also

- `AGENT_GUIDE.md` - Comprehensive guide with all details
- `unlock_h5_file.py` - Utility for handling locked files

