import json
import os
import shutil
import re
from pathlib import Path
from datetime import datetime
from .logs import write_log


# ============================================================================
# Check Comic Config
# ============================================================================
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


# ============================================================================
# Helper Functions
# ============================================================================


def get_page_number_info(filename, project_name):
    """
    Extract numeric information from a page filename.
    Returns (base_number, suffix) where suffix is None for sequential.
    """
    name_without_ext = os.path.splitext(filename)[0]
    name_without_prefix = name_without_ext.replace(project_name, "")

    # Format 1: "008" (pure sequential)
    match = re.match(r"^(\d+)$", name_without_prefix)
    if match:
        return (int(match.group(1)), None)

    # Format 2: "007_5" (underscore separator)
    match = re.match(r"^(\d+)_(.+)$", name_without_prefix)
    if match:
        return (int(match.group(1)), match.group(2))

    # Format 3: "007b" (letter suffix)
    match = re.match(r"^(\d+)([a-z]+)$", name_without_prefix)
    if match:
        return (int(match.group(1)), match.group(2))

    return (None, None)


def generate_inbetween_name(prev_filename, next_filename, project_name):
    """
    Generate a non-sequential name that fits between two existing pages.
    """
    prev_name = os.path.splitext(os.path.basename(prev_filename))[0]
    next_name = os.path.splitext(os.path.basename(next_filename))[0]

    prev_num, prev_suffix = get_page_number_info(prev_name, project_name)
    next_num, next_suffix = get_page_number_info(next_name, project_name)

    # If previous page has no suffix (sequential numbering)
    if prev_suffix is None:
        # Check if next file already uses the "_5" suffix (same base number)
        if next_num == prev_num and next_suffix is not None:
            # Next file already has a suffix, need to find a gap
            if next_suffix.isdigit():
                # Generate a suffix between 0 and next_suffix
                next_suffix_int = int(next_suffix)
                new_suffix = (
                    next_suffix_int // 2 if next_suffix_int > 1 else next_suffix_int + 1
                )
                return f"{project_name}{prev_num:03d}_{new_suffix}.kra"
            elif next_suffix.isalpha():
                # Use 'a' as first letter suffix
                return f"{project_name}{prev_num:03d}a.kra"
        # Default: use "_5" suffix
        return f"{project_name}{prev_num:03d}_5.kra"

    # If previous page has numeric suffix
    if prev_suffix.isdigit():
        # Check if next file has a suffix and same base number
        if next_num == prev_num and next_suffix is not None:
            if next_suffix.isdigit():
                # Generate a suffix between prev and next
                prev_suffix_int = int(prev_suffix)
                next_suffix_int = int(next_suffix)
                if next_suffix_int - prev_suffix_int > 1:
                    # There's a gap, use the midpoint
                    new_suffix = (prev_suffix_int + next_suffix_int) // 2
                else:
                    # No gap, use decimal notation (e.g., _5_5)
                    return f"{project_name}{prev_num:03d}_{prev_suffix}_{5}.kra"
                return f"{project_name}{prev_num:03d}_{new_suffix}.kra"
        # Default: increment previous suffix
        new_suffix = int(prev_suffix) + 1
        return f"{project_name}{prev_num:03d}_{new_suffix}.kra"

    # If previous page has letter suffix
    if prev_suffix.isalpha():
        # Check if next file has a suffix and same base number
        if next_num == prev_num and next_suffix is not None:
            if next_suffix.isalpha():
                # Try to insert a letter between prev and next
                if ord(next_suffix) - ord(prev_suffix) > 1:
                    # There's a gap
                    new_letter = chr(ord(prev_suffix) + 1)
                else:
                    # No gap, switch to numeric suffix
                    return f"{project_name}{prev_num:03d}_{prev_suffix}_5.kra"
                return f"{project_name}{prev_num:03d}{new_letter}.kra"
        # Default: increment previous letter
        new_letter = chr(ord(prev_suffix) + 1)
        return f"{project_name}{prev_num:03d}{new_letter}.kra"

    # Fallback
    return f"{project_name}{prev_num:03d}_{prev_suffix}_2.kra"


def get_next_sequential_name(config):
    """
    Get the next sequential page name (for adding at the end).
    """
    page_numbers = []

    for page_path in config["pages"]:
        filename = os.path.basename(page_path)
        base_num, suffix = get_page_number_info(filename, config["projectName"])
        if base_num is not None:
            page_numbers.append(base_num)

    next_number = max(page_numbers) + 1 if page_numbers else 1
    return f"{config['projectName']}{next_number:03d}.kra"


def is_target_at_end_of_list(target_doc_path, config):
    """
    Check if target document is at the end of the pages list.

    Args:
        target_doc_path: Full path to the target document
        config: Config dictionary

    Returns:
        tuple: (is_at_end, target_index)
    """
    target_filename = os.path.basename(target_doc_path)
    pages_location = config.get("pagesLocation", "pages")

    # Construct the path as it appears in config
    target_config_path = f"{pages_location}\\{target_filename}"

    try:
        target_index = config["pages"].index(target_config_path)
        is_at_end = target_index == len(config["pages"]) - 1
        return (is_at_end, target_index)
    except ValueError:
        # Target not found in config
        return (None, None)


def load_config(comic_config_path):
    """Load config with UTF-16 encoding."""
    with open(comic_config_path, "r", encoding="utf-16") as f:
        return json.load(f)


def save_config(comic_config_path, config):
    """Save config with UTF-16 encoding."""
    with open(comic_config_path, "w", encoding="utf-16") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


# ============================================================================
# Main Functions
# ============================================================================


def add_new_document_from_template(target_doc_path, template_path, comic_config_path):
    """
    Add a new document from template after the target document.

    Args:
        target_doc_path: Full path to the target document (e.g., "C:\\...\\Test009.kra")
        template_path: Full path to the template file (e.g., "C:\\...\\templates\\scene.kra")
        comic_config_path: Full path to comicConfig.json

    Returns:
        dict: Information about the created document
    """
    print(
        f"Adding new document from template after: {os.path.basename(target_doc_path)}"
    )
    print(f"Template: {os.path.basename(template_path)}")
    print("-" * 80)

    # Load config
    config = load_config(comic_config_path)

    # Check if target is at end
    is_at_end, target_index = is_target_at_end_of_list(target_doc_path, config)

    if target_index is None:
        error_msg = (
            f"Target document not found in config: {os.path.basename(target_doc_path)}"
        )
        print(f"Error: {error_msg}")
        return {"error": error_msg}

    # Determine naming strategy
    if is_at_end:
        # Use sequential naming
        new_filename = get_next_sequential_name(config)
        naming_strategy = "sequential"
        print(f"✓ Target is at end of list (index {target_index})")
        print(f"✓ Using sequential naming: {new_filename}")
    else:
        # Use non-sequential naming
        target_filename = os.path.basename(target_doc_path)
        next_page = config["pages"][target_index + 1]
        next_filename = os.path.basename(next_page)

        new_filename = generate_inbetween_name(
            target_filename, next_filename, config["projectName"]
        )
        naming_strategy = "non-sequential"
        print(f"✓ Target is NOT at end (index {target_index})")
        print(f"✓ Next file: {next_filename}")
        print(f"✓ Using non-sequential naming: {new_filename}")

    # Get pages location directory
    pages_dir = os.path.dirname(target_doc_path)
    new_doc_path = os.path.join(pages_dir, new_filename)

    # Copy template to new location
    try:
        if not os.path.exists(template_path):
            error_msg = f"Template file not found: {template_path}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}

        shutil.copy2(template_path, new_doc_path)
        print(f"✓ Created new file: {new_doc_path}")
    except Exception as e:
        error_msg = f"Failed to copy template: {str(e)}"
        print(f"Error: {error_msg}")
        return {"error": error_msg}

    # Update config
    pages_location = config.get("pagesLocation", "pages")
    new_page_path = f"{pages_location}\\{new_filename}"
    insert_position = target_index + 1

    config["pages"].insert(insert_position, new_page_path)
    config["pageNumber"] = len(config["pages"])

    # Save config
    save_config(comic_config_path, config)
    print(f"✓ Updated config: inserted at position {insert_position}")
    print(f"✓ Total pages: {config['pageNumber']}")

    result = {
        "success": True,
        "new_filename": new_filename,
        "new_doc_path": new_doc_path,
        "position": insert_position,
        "naming_strategy": naming_strategy,
        "total_pages": config["pageNumber"],
    }

    return result


def duplicate_document(target_doc_name, target_doc_path, comic_config_path):
    """
    Duplicate an existing document and insert after the target.

    Args:
        target_doc_name: Filename of the target document (e.g., "Test009.kra")
        target_doc_path: Full path to the target document
        comic_config_path: Full path to comicConfig.json

    Returns:
        dict: Information about the duplicated document
    """
    write_log(f"Duplicating document: {target_doc_name}")

    # Load config
    config = load_config(comic_config_path)

    # Check if target is at end
    is_at_end, target_index = is_target_at_end_of_list(target_doc_path, config)

    if target_index is None:
        error_msg = f"Target document not found in config: {target_doc_name}"
        write_log(f"Error: {error_msg}")
        return {"error": error_msg}

    # Determine naming strategy
    if is_at_end:
        # Use sequential naming
        new_filename = get_next_sequential_name(config)
        naming_strategy = "sequential"
        write_log(f"✓ Target is at end of list (index {target_index})")
        write_log(f"✓ Using sequential naming: {new_filename}")
    else:
        # Use non-sequential naming
        target_filename = os.path.basename(target_doc_path)
        next_page = config["pages"][target_index + 1]
        next_filename = os.path.basename(next_page)

        new_filename = generate_inbetween_name(
            target_filename, next_filename, config["projectName"]
        )
        naming_strategy = "non-sequential"
        write_log(f"✓ Target is NOT at end (index {target_index})")
        write_log(f"✓ Next file: {next_filename}")
        write_log(f"✓ Using non-sequential naming: {new_filename}")

    # Get pages location directory
    pages_dir = os.path.dirname(target_doc_path)
    new_doc_path = os.path.join(pages_dir, new_filename)

    # Copy target document to new location
    try:
        if not os.path.exists(target_doc_path):
            error_msg = f"Target file not found: {target_doc_path}"
            write_log(f"Error: {error_msg}")
            return {"error": error_msg}

        shutil.copy2(target_doc_path, new_doc_path)
        write_log(f"✓ Duplicated: {target_doc_name} -> {new_filename}")
        write_log(f"✓ New file path: {new_doc_path}")
    except Exception as e:
        error_msg = f"Failed to duplicate file: {str(e)}"
        write_log(f"Error: {error_msg}")
        return {"error": error_msg}

    # Update config
    pages_location = config.get("pagesLocation", "pages")
    new_page_path = f"{pages_location}\\{new_filename}"
    insert_position = target_index + 1

    config["pages"].insert(insert_position, new_page_path)
    config["pageNumber"] = len(config["pages"])

    # Save config
    save_config(comic_config_path, config)
    write_log(f"✓ Updated config: inserted at position {insert_position}")
    write_log(f"✓ Total pages: {config['pageNumber']}")

    result = {
        "success": True,
        "original_filename": target_doc_name,
        "new_filename": new_filename,
        "new_doc_path": new_doc_path,
        "position": insert_position,
        "naming_strategy": naming_strategy,
        "total_pages": config["pageNumber"],
    }

    return result


def delete_document(target_doc_name, target_doc_path, comic_config_path):
    """
    Delete a document by moving it to a backup folder.

    Args:
        target_doc_name: Filename of the target document (e.g., "Test009.kra")
        target_doc_path: Full path to the target document
        comic_config_path: Full path to comicConfig.json

    Returns:
        dict: Information about the deleted document
    """
    print(f"Deleting document: {target_doc_name}")
    print("-" * 80)

    # Load config
    config = load_config(comic_config_path)

    # Find the page in config
    pages_location = config.get("pagesLocation", "pages")
    target_config_path = f"{pages_location}\\{target_doc_name}"

    if target_config_path not in config["pages"]:
        error_msg = f"Document not found in config: {target_doc_name}"
        print(f"Error: {error_msg}")
        return {"error": error_msg}

    target_index = config["pages"].index(target_config_path)
    print(f"✓ Found in config at index {target_index}")

    # Create backup/removed directory
    pages_dir = os.path.dirname(target_doc_path)
    backup_dir = os.path.join(pages_dir, "removed")
    os.makedirs(backup_dir, exist_ok=True)

    # Add timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_without_ext, ext = os.path.splitext(target_doc_name)
    backup_filename = f"{name_without_ext}_{timestamp}{ext}"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Move file to backup
    try:
        if os.path.exists(target_doc_path):
            shutil.move(target_doc_path, backup_path)
            print(f"✓ Moved file to backup:")
            print(f"  From: {target_doc_path}")
            print(f"  To:   {backup_path}")
            file_moved = True
        else:
            print(f"⚠ Warning: Physical file not found: {target_doc_path}")
            print(f"⚠ Will only update config")
            file_moved = False
    except Exception as e:
        error_msg = f"Failed to move file: {str(e)}"
        print(f"Error: {error_msg}")
        return {"error": error_msg}

    # Remove from config
    config["pages"].remove(target_config_path)
    config["pageNumber"] = len(config["pages"])

    # Save config
    save_config(comic_config_path, config)
    print(f"✓ Updated config: removed from position {target_index}")
    print(f"✓ Total pages: {config['pageNumber']}")

    result = {
        "success": True,
        "deleted_filename": target_doc_name,
        "original_index": target_index,
        "backup_path": backup_path if file_moved else None,
        "file_moved": file_moved,
        "total_pages": config["pageNumber"],
    }

    return result


# ============================================================================
# Utility Functions
# ============================================================================


def list_pages(comic_config_path):
    """
    List all pages in the config with their indices.
    """
    config = load_config(comic_config_path)

    print("\nCurrent Pages:")
    print("=" * 80)
    for idx, page in enumerate(config["pages"]):
        filename = os.path.basename(page)
        print(f"  [{idx:2d}] {filename}")
    print(f"\nTotal: {config['pageNumber']} pages")
    print("=" * 80 + "\n")


def list_removed_files(comic_config_path):
    """
    List all files in the removed/backup folder.
    """
    config = load_config(comic_config_path)
    config_dir = os.path.dirname(comic_config_path)
    pages_location = config.get("pagesLocation", "pages")
    removed_dir = os.path.join(config_dir, pages_location, "removed")

    if not os.path.exists(removed_dir):
        print("No removed files folder exists yet")
        return []

    removed_files = [f for f in os.listdir(removed_dir) if f.endswith(".kra")]

    if not removed_files:
        print("No removed files found")
        return []

    print(f"\nRemoved Files in: {removed_dir}")
    print("=" * 80)
    for i, filename in enumerate(sorted(removed_files), 1):
        file_path = os.path.join(removed_dir, filename)
        file_size = os.path.getsize(file_path)
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"{i:2d}. {filename}")
        print(
            f"    Size: {file_size:,} bytes | Modified: {file_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    print("=" * 80 + "\n")

    return removed_files
