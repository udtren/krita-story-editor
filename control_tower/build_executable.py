"""
Script to build Control Tower as a standalone executable using PyInstaller
"""

import PyInstaller.__main__
import os
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to script directory
main_file = os.path.join(script_dir, "main.py")

# Check for .ico file, if not available, try to convert .png to .ico
icon_file = os.path.join(script_dir, "images", "book.ico")
png_icon = os.path.join(script_dir, "images", "book.png")

# Try to convert PNG to ICO if .ico doesn't exist
if not os.path.exists(icon_file) and os.path.exists(png_icon):
    print("Icon file not found, attempting to convert PNG to ICO...")
    try:
        from PIL import Image

        img = Image.open(png_icon)
        # Resize to standard icon sizes
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        img.save(
            icon_file,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
        )
        print(f"✅ Icon converted successfully: {icon_file}")
    except ImportError:
        print("⚠️ Pillow not installed. Building without icon.")
        print("   To add an icon, install Pillow: pip install Pillow")
        icon_file = None
    except Exception as e:
        print(f"⚠️ Failed to convert icon: {e}")
        icon_file = None
elif not os.path.exists(icon_file):
    print("⚠️ No icon file found. Building without icon.")
    icon_file = None

# PyInstaller arguments
args = [
    main_file,  # Main script
    "--onefile",  # Create a single executable
    "--windowed",  # No console window (GUI app)
    "--name=StoryEditor",  # Name of the executable
    # Add data files (non-Python files that need to be included)
    f'--add-data={os.path.join(script_dir, "config")}{os.pathsep}config',
    f'--add-data={os.path.join(script_dir, "fonts")}{os.pathsep}fonts',
    f'--add-data={os.path.join(script_dir, "images")}{os.pathsep}images',
    f'--add-data={os.path.join(script_dir, "story_editor")}{os.pathsep}story_editor',
    # Additional options
    "--clean",  # Clean PyInstaller cache before building
    "--noconfirm",  # Overwrite output directory without asking
]

# Add icon if available
if icon_file:
    args.insert(4, f"--icon={icon_file}")

print("Building Control Tower executable...")
print(f"Main file: {main_file}")
print(f"Build directory: {script_dir}")
print("\nThis may take a few minutes...\n")

try:
    PyInstaller.__main__.run(args)
    print("\n✅ Build complete!")
    print(f"Executable location: {os.path.join(script_dir, 'dist', 'StoryEditor.exe')}")
except Exception as e:
    print(f"\n❌ Build failed: {e}")
    sys.exit(1)
