#!/bin/bash
echo "===================================="
echo "Story Editor - Full Build and Release"
echo "===================================="
echo ""
echo "This will:"
echo "1. Build the executable"
echo "2. Create distribution package"
echo ""
read -p "Press enter to continue..."

# Change to scripts directory where this file is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "===================================="
echo "Step 1: Building Executable"
echo "===================================="
bash build.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed! Aborting."
    exit 1
fi

echo ""
echo ""
echo "===================================="
echo "Step 2: Creating Distribution Package"
echo "===================================="
bash create_release.sh

echo ""
echo ""
echo "===================================="
echo "✅ Complete!"
echo "===================================="
echo ""
echo "Your distribution package is ready in the 'release' folder"
echo ""
