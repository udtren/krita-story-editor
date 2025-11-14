#!/bin/bash
echo "===================================="
echo "Creating Story Editor Release Package"
echo "===================================="
echo ""

# Change to project root (parent of scripts)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Activate virtual environment (in control_tower folder)
if [ -f "control_tower/venv/bin/activate" ]; then
    source control_tower/venv/bin/activate
else
    echo "Error: Virtual environment not found!"
    echo "Please run scripts/build.sh first"
    exit 1
fi

# Check if executable exists
if [ ! -f "dist/StoryEditor" ]; then
    echo "Error: StoryEditor executable not found!"
    echo ""
    echo "Please run scripts/build.sh first to create the executable"
    exit 1
fi

# Run the distribution script
echo ""
echo "Creating distribution package..."
python scripts/create_distribution.py

echo ""
echo "===================================="
echo "Release creation completed!"
echo "===================================="
