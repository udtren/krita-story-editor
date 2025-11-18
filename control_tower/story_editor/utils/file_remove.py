import json
import os
import shutil
from datetime import datetime


def remove_page(config_path, page_filename, create_backup=True):
    """
    Remove a page from the config and move it to /removed subfolder.

    Args:
        config_path: Path to comicConfig.json
        page_filename: Filename to remove (e.g., "Test008.kra")
        create_backup: Whether to backup the config before modification

    Returns:
        dict with removal info or None if failed
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Find the page in config
    page_path = f"{config['pagesLocation']}\\{page_filename}"

    if page_path not in config["pages"]:
        print(f"Error: Page '{page_filename}' not found in config")
        print(f"Looking for: {page_path}")
        return None

    # Get the index before removal
    page_index = config["pages"].index(page_path)

    # Create removed directory if it doesn't exist
    removed_dir = os.path.join(config["pagesLocation"], "removed")
    os.makedirs(removed_dir, exist_ok=True)

    # Prepare source and destination paths
    source_file = os.path.join(config["pagesLocation"], page_filename)

    # Add timestamp to avoid overwriting if same file is removed multiple times
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

    # Save updated config
    with open(config_path, "w", encoding="utf-8") as f:
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


def remove_page_by_index(config_path, index, create_backup=True):
    """
    Remove a page by its index in the pages array.

    Args:
        config_path: Path to comicConfig.json
        index: Index of the page to remove (0-based)
        create_backup: Whether to backup the config before modification
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if index < 0 or index >= len(config["pages"]):
        print(f"Error: Index {index} out of range (0-{len(config['pages'])-1})")
        return None

    page_path = config["pages"][index]
    page_filename = os.path.basename(page_path)

    return remove_page(config_path, page_filename, create_backup)


def remove_multiple_pages(config_path, page_filenames, create_backup=True):
    """
    Remove multiple pages at once.

    Args:
        config_path: Path to comicConfig.json
        page_filenames: List of filenames to remove
        create_backup: Whether to backup the config before modification
    """
    if create_backup:
        backup_path = f"{config_path}.backup"
        shutil.copy2(config_path, backup_path)
        print(f"Created backup: {backup_path}\n")

    results = []
    for filename in page_filenames:
        print(f"\nRemoving: {filename}")
        print("-" * 60)
        result = remove_page(config_path, filename, create_backup=False)
        results.append(result)

    return results


def list_removed_pages(config_path):
    """
    List all pages in the /removed subfolder.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    removed_dir = os.path.join(config["pagesLocation"], "removed")

    if not os.path.exists(removed_dir):
        print("No removed pages folder exists yet")
        return []

    removed_files = [f for f in os.listdir(removed_dir) if f.endswith(".kra")]

    if not removed_files:
        print("No removed pages found")
        return []

    print(f"Removed pages in: {removed_dir}")
    print("-" * 60)
    for i, filename in enumerate(sorted(removed_files), 1):
        file_path = os.path.join(removed_dir, filename)
        file_size = os.path.getsize(file_path)
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"{i}. {filename}")
        print(
            f"   Size: {file_size:,} bytes | Modified: {file_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    return removed_files


def restore_page(config_path, removed_filename, insert_at_index=None):
    """
    Restore a removed page back to the active pages.

    Args:
        config_path: Path to comicConfig.json
        removed_filename: Filename in the /removed folder
        insert_at_index: Where to insert (None = at end)
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    removed_dir = os.path.join(config["pagesLocation"], "removed")
    source_file = os.path.join(removed_dir, removed_filename)

    if not os.path.exists(source_file):
        print(f"Error: File not found in removed folder: {removed_filename}")
        return None

    # Extract original filename (remove timestamp if added)
    # Format: "Test008_20241118_143022.kra" -> "Test008.kra"
    import re

    match = re.match(r"^(.+?)(?:_\d{8}_\d{6})?(\.\w+)$", removed_filename)
    if match:
        original_name = match.group(1) + match.group(2)
    else:
        original_name = removed_filename

    dest_file = os.path.join(config["pagesLocation"], original_name)

    # Check if file already exists
    if os.path.exists(dest_file):
        print(f"Warning: File already exists: {original_name}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != "y":
            print("Restore cancelled")
            return None

    # Move file back
    shutil.move(source_file, dest_file)
    print(f"Restored file: {removed_filename}")
    print(f"         to: {original_name}")

    # Add back to config
    page_path = f"{config['pagesLocation']}\\{original_name}"

    if insert_at_index is None:
        config["pages"].append(page_path)
        insert_position = len(config["pages"]) - 1
    else:
        config["pages"].insert(insert_at_index, page_path)
        insert_position = insert_at_index

    config["pageNumber"] = len(config["pages"])

    # Save config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"✓ Restored at index {insert_position}")
    print(f"✓ Updated pageNumber: {config['pageNumber']}")

    return {
        "restored_filename": original_name,
        "position": insert_position,
        "total_pages": config["pageNumber"],
    }


# Example usage
if __name__ == "__main__":
    config_file = "comicConfig.json"

    # Show current pages
    print("=" * 60)
    print("Current Pages")
    print("=" * 60)
    list_pages_with_indices(config_file)

    # Example 1: Remove a single page
    print("\n" + "=" * 60)
    print("Example 1: Remove Test008.kra")
    print("=" * 60)
    remove_page(config_file, "Test008.kra")

    # Example 2: Remove by index
    print("\n" + "=" * 60)
    print("Example 2: Remove page at index 5")
    print("=" * 60)
    remove_page_by_index(config_file, 5)

    # Example 3: Remove multiple pages
    print("\n" + "=" * 60)
    print("Example 3: Remove multiple pages")
    print("=" * 60)
    remove_multiple_pages(config_file, ["Test010.kra", "Test011.kra"])

    # Show removed pages
    print("\n" + "=" * 60)
    print("Removed Pages")
    print("=" * 60)
    list_removed_pages(config_file)

    # Example 4: Restore a page
    print("\n" + "=" * 60)
    print("Example 4: Restore a removed page")
    print("=" * 60)
    # restore_page(config_file, "Test008_20241118_143022.kra", insert_at_index=7)

    # Show final state
    print("\n" + "=" * 60)
    print("Final Pages")
    print("=" * 60)
    list_pages_with_indices(config_file)
