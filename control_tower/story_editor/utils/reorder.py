"""
Reorder Krita files to sequential naming
"""
import os
import shutil
import re
import json
from datetime import datetime


def backup_folder(folder_path, log_callback=None):
    """
    Create a backup of the folder with timestamp
    Returns the backup folder path
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    parent_dir = os.path.dirname(folder_path)
    folder_name = os.path.basename(folder_path)

    # Create timestamp in mmdd-hhmmss format
    timestamp = datetime.now().strftime("%m%d-%H%M%S")
    backup_name = f"{folder_name}-{timestamp}"
    backup_path = os.path.join(parent_dir, backup_name)

    log(f"📦 Creating backup: {backup_name}")
    shutil.copytree(folder_path, backup_path)
    log(f"✅ Backup created successfully")

    return backup_path


def get_kra_files(folder_path):
    """
    Get all .kra files (not .kra~) from the folder
    Returns a list of tuples: (filename, base_name, number, suffix)
    """
    kra_files = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".kra") and not filename.endswith(".kra~"):
            # Match patterns like Test001.kra, Test062_5.kra, etc.
            match = re.match(r"^(.+?)(\d+)(_\d+)?\.kra$", filename)
            if match:
                base_name = match.group(1)
                number = int(match.group(2))
                suffix = match.group(3) if match.group(3) else ""
                kra_files.append((filename, base_name, number, suffix))

    return kra_files


def is_sequential(kra_files):
    """
    Check if files are already in sequential order
    """
    if not kra_files:
        return True

    # Sort by number and suffix
    sorted_files = sorted(kra_files, key=lambda x: (x[2], x[3]))

    # Check if numbering is sequential (1, 2, 3, ...) without gaps
    expected_num = 1
    for _, _, num, suffix in sorted_files:
        # Only check main numbers (no suffix)
        if not suffix:
            if num != expected_num:
                return False
            expected_num += 1

    # Check for files with suffixes (like _5, _6, _7)
    # These indicate non-sequential naming
    for _, _, _, suffix in sorted_files:
        if suffix:
            return False

    return True


def rename_files_sequential(folder_path, kra_files, log_callback=None):
    """
    Rename all files to sequential naming, starting from the last file
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    if not kra_files:
        log("⚠️ No .kra files found")
        return []

    # Sort files by number and suffix
    sorted_files = sorted(kra_files, key=lambda x: (x[2], x[3]))

    # Get the base name from the first file
    base_name = sorted_files[0][1]

    # Create mapping: old_filename -> new_filename
    rename_map = []
    for idx, (old_filename, _, _, _) in enumerate(sorted_files, start=1):
        new_filename = f"{base_name}{idx:03d}.kra"
        if old_filename != new_filename:
            rename_map.append((old_filename, new_filename))

    if not rename_map:
        log("✅ Files are already sequentially named")
        return []

    log(f"🔄 Renaming {len(rename_map)} files to sequential naming...")

    # Rename from last to first to avoid conflicts
    for old_name, new_name in reversed(rename_map):
        old_path = os.path.join(folder_path, old_name)
        new_path = os.path.join(folder_path, new_name)

        # Use temporary name to avoid conflicts
        temp_path = os.path.join(folder_path, f"_temp_{new_name}")

        # Rename the .kra file
        if os.path.exists(old_path):
            shutil.move(old_path, temp_path)
            log(f"  {old_name} -> {new_name}")

        # Also rename the .kra~ file if it exists
        old_backup_path = old_path + "~"
        new_backup_path = new_path + "~"
        temp_backup_path = temp_path + "~"

        if os.path.exists(old_backup_path):
            shutil.move(old_backup_path, temp_backup_path)
            log(f"  {old_name}~ -> {new_name}~")

    # Remove temp prefix from all files
    for _, new_name in reversed(rename_map):
        temp_path = os.path.join(folder_path, f"_temp_{new_name}")
        new_path = os.path.join(folder_path, new_name)

        if os.path.exists(temp_path):
            shutil.move(temp_path, new_path)

        temp_backup_path = temp_path + "~"
        new_backup_path = new_path + "~"
        if os.path.exists(temp_backup_path):
            shutil.move(temp_backup_path, new_backup_path)

    log(f"✅ Renamed {len(rename_map)} files successfully")
    return rename_map


def update_comic_config(folder_path, rename_map=None, log_callback=None):
    """
    Update comicConfig.json if it exists
    If rename_map is None, sync with actual files in folder
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    # Find comicConfig.json in the parent directory
    parent_dir = os.path.dirname(folder_path)
    config_path = os.path.join(parent_dir, "comicConfig.json")

    if not os.path.exists(config_path):
        log("ℹ️ No comicConfig.json found")
        return

    log(f"📝 Updating comicConfig.json...")

    try:
        # Read the config file
        with open(config_path, "r", encoding="utf-16") as f:
            config = json.load(f)

        if rename_map is not None:
            # Mode 1: Update based on rename mapping
            if not rename_map:
                return

            # Create a mapping dict for quick lookup
            rename_dict = {old: new for old, new in rename_map}

            # Update the pages array if it exists
            if "pages" in config and isinstance(config["pages"], list):
                updated_count = 0
                for page in config["pages"]:
                    if isinstance(page, str):
                        # Check if this page name needs to be updated
                        if page in rename_dict:
                            old_name = page
                            new_name = rename_dict[page]
                            # Update in the list
                            idx = config["pages"].index(old_name)
                            config["pages"][idx] = new_name
                            updated_count += 1

                if updated_count > 0:
                    # Write back to file
                    with open(config_path, "w", encoding="utf-16") as f:
                        json.dump(config, f, indent=4, ensure_ascii=False)
                    log(
                        f"✅ Updated {updated_count} page references in comicConfig.json"
                    )
                else:
                    log("ℹ️ No page references needed updating in comicConfig.json")
            else:
                log("ℹ️ No 'pages' array found in comicConfig.json")

        else:
            # Mode 2: Sync with actual files in folder
            kra_files = get_kra_files(folder_path)
            if not kra_files:
                log("⚠️ No .kra files found in folder")
                return

            # Sort files by number and suffix to get them in order
            sorted_files = sorted(kra_files, key=lambda x: (x[2], x[3]))

            # Get folder name and create paths with folder prefix
            folder_name = os.path.basename(folder_path)
            file_names = [
                f"{folder_name}\\{filename}" for filename, _, _, _ in sorted_files
            ]

            # Update the pages array
            if "pages" in config:
                old_pages = config["pages"] if isinstance(config["pages"], list) else []
                config["pages"] = file_names

                # Write back to file
                with open(config_path, "w", encoding="utf-16") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)

                log(f"✅ Updated comicConfig.json with {len(file_names)} files")
            else:
                log("ℹ️ No 'pages' key found in comicConfig.json")

    except Exception as e:
        log(f"❌ Error updating comicConfig.json: {str(e)}")


def reorder_krita_files(folder_path, mode="full", log_callback=None):
    """
    Main entry point for reordering krita files

    Args:
        folder_path: Path to the krita files folder
        mode: Either "full" (backup, rename, update config) or "config_only" (just update config)
        log_callback: Optional callback function for logging messages

    Returns:
        tuple: (success: bool, message: str)
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    # Validate folder path
    if not os.path.exists(folder_path):
        return (False, f"Folder does not exist: {folder_path}")

    if not os.path.isdir(folder_path):
        return (False, f"Path is not a directory: {folder_path}")

    log(f"📁 Processing folder: {folder_path}")
    log(f"ℹ️ Mode: {mode}")

    # Config-only mode: just update comicConfig.json
    if mode == "config_only":
        try:
            update_comic_config(folder_path, rename_map=None, log_callback=log_callback)
            return (True, "comicConfig.json updated successfully")
        except Exception as e:
            return (False, f"Error updating comicConfig.json: {str(e)}")

    # Full mode: backup, rename, and update config
    backup_path = None

    try:
        # Step 1: Backup the folder
        backup_path = backup_folder(folder_path, log_callback=log_callback)

        # Step 2: Get all .kra files
        kra_files = get_kra_files(folder_path)

        if not kra_files:
            log("⚠️ No .kra files found in the folder")
            return (True, "No .kra files found")

        log(f"📊 Found {len(kra_files)} .kra files")

        # Step 3: Check if files are already sequential
        if is_sequential(kra_files):
            log("✅ Files are already in sequential order")
            return (True, "Files are already in sequential order")

        log("⚠️ Non-sequential naming detected")

        # Step 4: Rename files to sequential naming
        rename_map = rename_files_sequential(folder_path, kra_files, log_callback=log_callback)

        # Step 5: Update comicConfig.json if it exists
        update_comic_config(folder_path, rename_map, log_callback=log_callback)

        log("✅ All operations completed successfully")
        log(f"💾 Backup saved at: {backup_path}")

        return (True, "All operations completed successfully")

    except Exception as e:
        error_msg = f"Error during reordering: {str(e)}"
        if backup_path:
            error_msg += f"\nBackup available at: {backup_path}"
        return (False, error_msg)
