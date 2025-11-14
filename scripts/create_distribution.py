"""
Create distribution package for Story Editor
Packages the executable and user_data folder into a zip file
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime


def create_distribution_zip():
    """Create a distribution zip file with the executable and user_data folder"""

    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts folder at root
    project_root = os.path.dirname(script_dir)  # project root
    control_tower_dir = os.path.join(project_root, "control_tower")
    dist_dir = os.path.join(project_root, "dist")
    user_data_dir = os.path.join(project_root, "user_data")

    # Check if executable exists
    exe_path = os.path.join(dist_dir, "StoryEditor.exe")
    if not os.path.exists(exe_path):
        print("❌ Error: StoryEditor.exe not found in dist folder")
        print("   Please run build.bat first to create the executable")
        return False

    # Check if user_data exists, if not create it with default configs and templates
    if not os.path.exists(user_data_dir):
        print("⚠️ Warning: user_data folder not found")
        print("   Creating user_data folder with default configs and templates...")
        os.makedirs(os.path.join(user_data_dir, "templates"))
        os.makedirs(os.path.join(user_data_dir, "config"))

        # Copy default config files from control_tower/config
        config_files = ["template.json", "main_window.json", "shortcuts.json", "story_editor.json"]
        src_config_dir = os.path.join(control_tower_dir, "config")

        for config_file in config_files:
            src = os.path.join(src_config_dir, config_file)
            dst = os.path.join(user_data_dir, "config", config_file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"   Copied default config: {config_file}")

        # Copy default templates from control_tower/config/user_templates
        src_templates_dir = os.path.join(control_tower_dir, "config", "user_templates")
        dst_templates_dir = os.path.join(user_data_dir, "templates")

        if os.path.exists(src_templates_dir):
            for filename in os.listdir(src_templates_dir):
                if filename.endswith(".xml"):
                    src = os.path.join(src_templates_dir, filename)
                    dst = os.path.join(dst_templates_dir, filename)
                    shutil.copy2(src, dst)
                    print(f"   Copied default template: {filename}")
    else:
        # Ensure config files exist in user_data
        config_files = ["template.json", "main_window.json", "shortcuts.json", "story_editor.json"]
        src_config_dir = os.path.join(control_tower_dir, "config")
        user_config_dir = os.path.join(user_data_dir, "config")

        for config_file in config_files:
            dst = os.path.join(user_config_dir, config_file)
            if not os.path.exists(dst):
                src = os.path.join(src_config_dir, config_file)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    print(f"   Added missing config: {config_file}")

        # Ensure templates exist in user_data (copy if folder is empty)
        user_templates_dir = os.path.join(user_data_dir, "templates")
        if not os.path.exists(user_templates_dir):
            os.makedirs(user_templates_dir)

        if not os.listdir(user_templates_dir):
            src_templates_dir = os.path.join(control_tower_dir, "config", "user_templates")
            if os.path.exists(src_templates_dir):
                for filename in os.listdir(src_templates_dir):
                    if filename.endswith(".xml"):
                        src = os.path.join(src_templates_dir, filename)
                        dst = os.path.join(user_templates_dir, filename)
                        shutil.copy2(src, dst)
                        print(f"   Copied default template: {filename}")

    # Create distribution folder name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dist_folder_name = f"StoryEditor_v1.0_{timestamp}"
    release_dir = os.path.join(project_root, "release")
    dist_folder = os.path.join(release_dir, dist_folder_name)

    # Clean up old release folder if it exists
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)

    # Create release folder structure
    os.makedirs(dist_folder, exist_ok=True)

    print(f"📦 Creating distribution package...")
    print(f"   Output: {dist_folder}")

    # Copy executable
    print("   Copying StoryEditor.exe...")
    shutil.copy2(exe_path, dist_folder)

    # Copy user_data folder
    print("   Copying user_data folder...")
    shutil.copytree(
        user_data_dir,
        os.path.join(dist_folder, "user_data"),
        dirs_exist_ok=True
    )

    # Create README for distribution
    readme_content = """# Story Editor - Installation Guide

## What's Included
- StoryEditor.exe - The main application
- user_data/ - Configuration and template files (persists between updates)

## Installation

1. Extract this entire folder to any location on your computer
2. Run StoryEditor.exe

## Important Notes

- **DO NOT** move StoryEditor.exe without the user_data folder
- The user_data folder contains:
  - templates/ - Your custom text templates
  - config/ - Application configuration files
- When updating to a new version, keep your existing user_data folder

## First Run

On first run, the application will:
1. Create necessary folders in user_data/ if they don't exist
2. Load any existing templates from user_data/templates/

## Usage

1. Open Krita
2. Load the Story Editor Agent docker
3. Run StoryEditor.exe
4. Click "Connect to Agent"
5. Click "Open Story Editor" to start editing

## Support

For issues or questions, please visit:
https://github.com/your-repo/krita-story-editor

---
Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    readme_path = os.path.join(dist_folder, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("   Creating README.txt...")

    # Create zip file
    zip_path = dist_folder + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"   Creating zip file: {os.path.basename(zip_path)}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from dist_folder
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(dist_folder))
                zipf.write(file_path, arcname)

    # Get file size
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)

    print("\n✅ Distribution package created successfully!")
    print(f"\n📁 Folder: {dist_folder}")
    print(f"📦 Zip file: {zip_path}")
    print(f"📊 Size: {zip_size_mb:.2f} MB")
    print("\nYou can distribute the .zip file to users.")
    print("Users should extract the entire folder and run StoryEditor.exe")

    return True


if __name__ == "__main__":
    try:
        success = create_distribution_zip()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error creating distribution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
