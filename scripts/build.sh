#!/bin/bash
echo "===================================="
echo "Building Control Tower Executable"
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
    echo "Please run from control_tower: python -m venv venv"
    echo "Then run: source venv/bin/activate"
    echo "And install: pip install -r requirements.txt pyinstaller"
    exit 1
fi

# Check if PyInstaller is installed
python -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Check if Pillow is installed (for icon conversion)
python -c "import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Pillow not found. Installing for icon support..."
    pip install Pillow
fi

# Run the build script
echo ""
echo "Running build script..."
python scripts/build_executable.py

echo ""
echo "===================================="
echo "Build process completed!"
echo "===================================="
