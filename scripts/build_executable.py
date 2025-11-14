"""
Script to build Control Tower as a standalone executable using PyInstaller
"""

import PyInstaller.__main__
import os
import sys
import zipfile
import shutil

# Get the directory where this script is located (scripts folder at project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (parent of scripts)
project_root = os.path.dirname(script_dir)
# Get the control_tower directory
control_tower_dir = os.path.join(project_root, "control_tower")

# Define paths
main_file = os.path.join(control_tower_dir, "main.py")

# Check for .ico file, if not available, try to convert .png to .ico
icon_file = os.path.join(control_tower_dir, "images", "book.ico")
png_icon = os.path.join(control_tower_dir, "images", "book.png")

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
        print(f"[SUCCESS] Icon converted successfully: {icon_file}")
    except ImportError:
        print("[WARNING] Pillow not installed. Building without icon.")
        print("   To add an icon, install Pillow: pip install Pillow")
        icon_file = None
    except Exception as e:
        print(f"[WARNING] Failed to convert icon: {e}")
        icon_file = None
elif not os.path.exists(icon_file):
    print("[WARNING] No icon file found. Building without icon.")
    icon_file = None

# PyInstaller arguments
args = [
    main_file,  # Main script
    "--onefile",  # Create a single executable
    "--windowed",  # No console window (GUI app)
    "--name=StoryEditor",  # Name of the executable
    # Add data files (non-Python files that need to be included)
    f'--add-data={os.path.join(control_tower_dir, "config")}{os.pathsep}config',
    f'--add-data={os.path.join(control_tower_dir, "fonts")}{os.pathsep}fonts',
    f'--add-data={os.path.join(control_tower_dir, "images")}{os.pathsep}images',
    f'--add-data={os.path.join(control_tower_dir, "story_editor")}{os.pathsep}story_editor',
    # Additional options
    "--clean",  # Clean PyInstaller cache before building
    "--noconfirm",  # Overwrite output directory without asking
]

# Add icon if available
if icon_file:
    args.insert(4, f"--icon={icon_file}")

print("Building Control Tower executable...")
print(f"Platform: {sys.platform}")
print(f"Main file: {main_file}")
print(f"Control Tower directory: {control_tower_dir}")
print(f"Project root: {project_root}")
print("\nThis may take a few minutes...\n")

try:
    PyInstaller.__main__.run(args)
    print("\n[SUCCESS] Build complete!")

    # Platform-specific executable name
    if sys.platform == "win32":
        exe_name = "StoryEditor.exe"
    else:
        exe_name = "StoryEditor"

    print(f"Executable location: {os.path.join(project_root, 'dist', exe_name)}")

    # Zip the agent folder and place in dist
    agent_dir = os.path.join(project_root, "agent")
    dist_dir = os.path.join(project_root, "dist")

    if os.path.exists(agent_dir):
        print("\nCreating story-editor-agent.zip...")
        agent_zip_path = os.path.join(dist_dir, "agent.zip")

        # Remove existing zip if it exists
        if os.path.exists(agent_zip_path):
            os.remove(agent_zip_path)

        # Create zip file with parent "agent" folder included
        with zipfile.ZipFile(agent_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(agent_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_root)
                    zipf.write(file_path, arcname)

        # Get file size
        zip_size_kb = os.path.getsize(agent_zip_path) / 1024
        print(f"[SUCCESS] story-editor-agent.zip created: {agent_zip_path}")
        print(f"   Size: {zip_size_kb:.2f} KB")
    else:
        print("\n[WARNING] agent folder not found, skipping agent.zip creation")

except Exception as e:
    print(f"\n[ERROR] Build failed: {e}")
    sys.exit(1)
