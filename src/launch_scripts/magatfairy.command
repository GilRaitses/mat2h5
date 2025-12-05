#!/bin/bash
# magatfairy.command - macOS double-clickable script
# Double-click this file to open Terminal and start conversion

# Get directories
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# Run magatfairy with auto command
python3 "$REPO_ROOT/magatfairy.py" convert auto

# Keep terminal open so user can see results
echo ""
echo "Press any key to close..."
read -n 1

