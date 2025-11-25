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
    dist_dir = os.path.join(project_root, "dist")
    user_data_dir = os.path.join(project_root, "user_data")

    # Use GitHub tag if running in GitHub Actions, otherwise use default version
    github_ref = os.environ.get("GITHUB_REF", "")
    if github_ref.startswith("refs/tags/"):
        # Extract tag name from refs/tags/v1.0.0 -> v1.0.0
        dist_folder_name_profix = github_ref.replace("refs/tags/", "")
    else:
        dist_folder_name_profix = "tag_missing_" + datetime.now().strftime("%Y%m%d")

    # Check if executable exists (platform-specific name)
    if sys.platform == "win32":
        exe_name = "StoryEditor.exe"
        build_script = "build.bat"
    else:
        exe_name = "StoryEditor"
        build_script = "build.sh"

    exe_path = os.path.join(dist_dir, exe_name)
    if not os.path.exists(exe_path):
        print(f"Error: {exe_name} not found in dist folder")
        print(f"   Please run scripts/{build_script} first to create the executable")
        return False

    # Create distribution folder name with platform suffix
    platform_suffix = "Windows" if sys.platform == "win32" else "Linux"
    dist_folder_name = f"StoryEditor_{dist_folder_name_profix}_{platform_suffix}"
    release_dir = os.path.join(project_root, "release")
    dist_folder = os.path.join(release_dir, dist_folder_name)

    # Clean up old release folder if it exists
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)

    # Create release folder structure
    os.makedirs(dist_folder, exist_ok=True)

    print(f"Creating distribution package...")
    print(f"   Output: {dist_folder}")

    # Copy executable
    print(f"   Copying {exe_name}...")
    shutil.copy2(exe_path, dist_folder)

    # Copy agent.zip if it exists
    agent_zip_path = os.path.join(dist_dir, "agent.zip")
    if os.path.exists(agent_zip_path):
        print("   Copying agent.zip...")
        shutil.copy2(agent_zip_path, dist_folder)
    else:
        print("   Warning: agent.zip not found, skipping...")

    # Create zip file
    zip_path = dist_folder + ".zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"   Creating zip file: {os.path.basename(zip_path)}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from dist_folder
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(dist_folder))
                zipf.write(file_path, arcname)

    # Get file size
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)

    print("\nDistribution package created successfully!")
    print(f"\nFolder: {dist_folder}")
    print(f"Zip file: {zip_path}")
    print(f"Size: {zip_size_mb:.2f} MB")
    print("\nYou can distribute the .zip file to users.")
    print(f"Users should extract the entire folder and run {exe_name}")

    return True


if __name__ == "__main__":
    try:
        success = create_distribution_zip()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError creating distribution: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
