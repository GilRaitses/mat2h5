#!/bin/bash
# mat2h5.command - macOS double-clickable script
# Double-click this file to open Terminal and start conversion

# Get the directory where this script is located
cd "$(dirname "$0")"

# Run mat2h5 with auto command
python3 mat2h5.py convert auto

# Keep terminal open so user can see results
echo ""
echo "Press any key to close..."
read -n 1

