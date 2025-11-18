import json
import os
from pathlib import Path


def get_comic_config_info(folder_path):
    """
    Check for comicConfig.json in the given folder and extract information.
    Handles UTF-16 LE BOM encoding (used by Krita).

    Args:
        folder_path: Path to the folder to check

    Returns:
        dict: JSON object with config info or None if not found
    """
    try:
        # Convert to Path object for easier manipulation
        folder = Path(folder_path)

        # Get parent directory (one level up from pages folder)
        parent_dir = folder.parent

        # Construct path to comicConfig.json
        config_path = parent_dir / "comicConfig.json"

        # Check if config file exists
        if not config_path.exists():
            print(f"comicConfig.json not found at: {config_path}")
            return None

        # Read the config file with UTF-16 encoding
        with open(config_path, "r", encoding="utf-16") as f:
            config = json.load(f)

        # Extract required values
        page_number = config.get("pageNumber", 0)
        pages = config.get("pages", [])
        template_location = config.get("templateLocation", "templates")

        # Construct full path to template location
        template_dir = parent_dir / template_location

        # Find all .kra files in template location
        template_files = []
        if template_dir.exists() and template_dir.is_dir():
            # Get all .kra files
            kra_files = list(template_dir.glob("*.kra"))
            # Convert to string paths
            template_files = [str(kra_file) for kra_file in sorted(kra_files)]
        else:
            print(f"Warning: Template directory not found: {template_dir}")

        # Prepare result
        result = {
            "config_filepath": str(config_path),
            "pageNumber": page_number,
            "pages": pages,
            "templateLocation": template_location,
            "template_files": template_files,
        }

        return result

    except json.JSONDecodeError as e:
        return {
            "error": f"JSON decode error: {str(e)}",
            "config_filepath": str(config_path) if "config_path" in locals() else None,
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "config_filepath": str(config_path) if "config_path" in locals() else None,
        }


def save_comic_config(config_path, config_data):
    """
    Save comicConfig.json with UTF-16 LE BOM encoding (matching Krita's format).

    Args:
        config_path: Path to comicConfig.json
        config_data: Dictionary to save
    """
    with open(config_path, "w", encoding="utf-16-le") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)


def update_page_manager_for_utf16():
    """
    Updated versions of add_page and remove_page functions to handle UTF-16 LE BOM.
    """
    pass  # I'll provide these below


# Updated add_page function with UTF-16 support
def add_page(config_path, insert_after_index=None, source_file=None):
    """
    Add or replicate a page with intelligent naming based on position.
    Now handles UTF-16 LE BOM encoding.
    """
    # Read with UTF-16 LE
    with open(config_path, "r", encoding="utf-16-le") as f:
        config = json.load(f)

    # Determine insertion position
    if insert_after_index is None:
        insert_position = len(config["pages"])
        is_at_end = True
    else:
        insert_position = insert_after_index + 1
        is_at_end = insert_position >= len(config["pages"])

    # Choose naming strategy
    if is_at_end:
        new_filename = get_next_sequential_name(config)
        naming_strategy = "sequential"
        print(f"Adding at end (position {insert_position})")
        print(f"Using sequential naming: {new_filename}")
    else:
        prev_page = config["pages"][insert_after_index]
        next_page = config["pages"][insert_position]

        prev_filename = os.path.basename(prev_page)
        next_filename = os.path.basename(next_page)

        new_filename = generate_inbetween_name(
            prev_filename, next_filename, config["projectName"]
        )
        naming_strategy = "non-sequential"
        print(f"Inserting between positions {insert_after_index} and {insert_position}")
        print(f"Between: {prev_filename} and {next_filename}")
        print(f"Using non-sequential naming: {new_filename}")

    # Create new page path
    new_page_path = f"{config['pagesLocation']}\\{new_filename}"

    # Insert into config
    config["pages"].insert(insert_position, new_page_path)
    config["pageNumber"] = len(config["pages"])

    # Save config with UTF-16 LE
    with open(config_path, "w", encoding="utf-16-le") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    # If source file is provided, copy it
    if source_file:
        source_path = os.path.join(config["pagesLocation"], source_file)
        dest_path = os.path.join(config["pagesLocation"], new_filename)
        if os.path.exists(source_path):
            import shutil

            shutil.copy2(source_path, dest_path)
            print(f"Copied {source_file} -> {new_filename}")

    result = {
        "new_filename": new_filename,
        "new_page_path": new_page_path,
        "position": insert_position,
        "naming_strategy": naming_strategy,
        "total_pages": config["pageNumber"],
    }

    print(f"Total pages: {config['pageNumber']}\n")
    return result


# Updated remove_page function with UTF-16 support
def remove_page(config_path, page_filename, create_backup=True):
    """
    Remove a page from the config and move it to /removed subfolder.
    Now handles UTF-16 LE BOM encoding.
    """
    from datetime import datetime
    import shutil

    # Read with UTF-16 LE
    with open(config_path, "r", encoding="utf-16-le") as f:
        config = json.load(f)

    # Find the page in config
    page_path = f"{config['pagesLocation']}\\{page_filename}"

    if page_path not in config["pages"]:
        print(f"Error: Page '{page_filename}' not found in config")
        return None

    # Get the index before removal
    page_index = config["pages"].index(page_path)

    # Create removed directory if it doesn't exist
    removed_dir = os.path.join(config["pagesLocation"], "removed")
    os.makedirs(removed_dir, exist_ok=True)

    # Prepare source and destination paths
    source_file = os.path.join(config["pagesLocation"], page_filename)

    # Add timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_without_ext, ext = os.path.splitext(page_filename)
    dest_filename = f"{name_without_ext}_{timestamp}{ext}"
    dest_file = os.path.join(removed_dir, dest_filename)

    # Backup config if requested
    if create_backup:
        backup_path = f"{config_path}.backup"
        shutil.copy2(config_path, backup_path)
        print(f"Created backup: {backup_path}")

    # Move the file
    try:
        if os.path.exists(source_file):
            shutil.move(source_file, dest_file)
            print(f"Moved file: {source_file}")
            print(f"       to: {dest_file}")
            file_moved = True
        else:
            print(f"Warning: Physical file not found: {source_file}")
            print(f"Will only update config")
            file_moved = False
    except Exception as e:
        print(f"Error moving file: {e}")
        return None

    # Remove from config
    config["pages"].remove(page_path)
    config["pageNumber"] = len(config["pages"])

    # Save updated config with UTF-16 LE
    with open(config_path, "w", encoding="utf-16-le") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    result = {
        "removed_filename": page_filename,
        "original_index": page_index,
        "moved_to": dest_file if file_moved else None,
        "total_pages": config["pageNumber"],
        "file_moved": file_moved,
    }

    print(f"\n✓ Removed page at index {page_index}")
    print(f"✓ Updated pageNumber: {config['pageNumber']}")

    return result


# Helper functions (keep these from before, they don't need encoding changes)
def get_page_number_info(filename, project_name):
    """Extract numeric information from a page filename."""
    import re

    name_without_ext = os.path.splitext(filename)[0]
    name_without_prefix = name_without_ext.replace(project_name, "")

    match = re.match(r"^(\d+)$", name_without_prefix)
    if match:
        return (int(match.group(1)), None)

    match = re.match(r"^(\d+)_(.+)$", name_without_prefix)
    if match:
        return (int(match.group(1)), match.group(2))

    match = re.match(r"^(\d+)([a-z]+)$", name_without_prefix)
    if match:
        return (int(match.group(1)), match.group(2))

    return (None, None)


def generate_inbetween_name(prev_filename, next_filename, project_name):
    """Generate a non-sequential name that fits between two existing pages."""
    prev_name = os.path.splitext(os.path.basename(prev_filename))[0]
    prev_num, prev_suffix = get_page_number_info(prev_name, project_name)

    if prev_suffix is None:
        return f"{project_name}{prev_num:03d}_5.kra"

    if prev_suffix.isdigit():
        new_suffix = int(prev_suffix) + 1
        return f"{project_name}{prev_num:03d}_{new_suffix}.kra"

    if prev_suffix.isalpha():
        new_letter = chr(ord(prev_suffix) + 1)
        return f"{project_name}{prev_num:03d}{new_letter}.kra"

    return f"{project_name}{prev_num:03d}_{prev_suffix}_2.kra"


def get_next_sequential_name(config):
    """Get the next sequential page name (for adding at the end)."""
    page_numbers = []

    for page_path in config["pages"]:
        filename = os.path.basename(page_path)
        base_num, suffix = get_page_number_info(filename, config["projectName"])
        if base_num is not None:
            page_numbers.append(base_num)

    next_number = max(page_numbers) + 1 if page_numbers else 1
    return f"{config['projectName']}{next_number:03d}.kra"
