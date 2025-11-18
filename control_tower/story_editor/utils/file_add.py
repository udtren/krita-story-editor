import json
import os
import re


def get_page_number_info(filename, project_name):
    """
    Extract numeric information from a page filename.
    Returns (base_number, suffix) where suffix is None for sequential,
    or a letter/number for non-sequential.

    Examples:
        "Test008.kra" -> (8, None)
        "Test007_5.kra" -> (7, "5")
        "Test007b.kra" -> (7, "b")
    """
    name_without_ext = os.path.splitext(filename)[0]
    name_without_prefix = name_without_ext.replace(project_name, "")

    # Try to parse different formats
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

    Strategy:
    - If prev is "Test007.kra" and next is "Test008.kra" -> "Test007_5.kra"
    - If prev is "Test007_5.kra" -> "Test007_6.kra"
    - If prev is "Test007b.kra" -> "Test007c.kra"
    """
    prev_name = os.path.splitext(os.path.basename(prev_filename))[0]
    next_name = os.path.splitext(os.path.basename(next_filename))[0]

    prev_num, prev_suffix = get_page_number_info(prev_name, project_name)
    next_num, next_suffix = get_page_number_info(next_name, project_name)

    # If previous page has no suffix (sequential numbering)
    if prev_suffix is None:
        return f"{project_name}{prev_num:03d}_5.kra"

    # If previous page has numeric suffix
    if prev_suffix.isdigit():
        new_suffix = int(prev_suffix) + 1
        return f"{project_name}{prev_num:03d}_{new_suffix}.kra"

    # If previous page has letter suffix
    if prev_suffix.isalpha():
        # Increment letter: a->b, b->c, etc.
        new_letter = chr(ord(prev_suffix) + 1)
        return f"{project_name}{prev_num:03d}{new_letter}.kra"

    # Fallback: use underscore notation
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


def add_page(config_path, insert_after_index=None, source_file=None):
    """
    Add or replicate a page with intelligent naming based on position.

    Args:
        config_path: Path to comicConfig.json
        insert_after_index: Index to insert after (None = add at end)
        source_file: If provided, this file will be copied/replicated

    Returns:
        dict with 'new_filename', 'position', 'naming_strategy'
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Determine insertion position
    if insert_after_index is None:
        # Adding at the end
        insert_position = len(config["pages"])
        is_at_end = True
    else:
        insert_position = insert_after_index + 1
        is_at_end = insert_position >= len(config["pages"])

    # Choose naming strategy
    if is_at_end:
        # Use sequential numbering
        new_filename = get_next_sequential_name(config)
        naming_strategy = "sequential"
        print(f"Adding at end (position {insert_position})")
        print(f"Using sequential naming: {new_filename}")
    else:
        # Use non-sequential numbering
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

    # Save config
    with open(config_path, "w", encoding="utf-8") as f:
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


def list_pages_with_indices(config_path):
    """
    Display all pages with their indices for reference.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("Current pages:")
    for idx, page in enumerate(config["pages"]):
        filename = os.path.basename(page)
        print(f"  [{idx}] {filename}")
    print()


# Example usage
if __name__ == "__main__":
    config_file = "comicConfig.json"

    # Show current state
    list_pages_with_indices(config_file)

    # Example 1: Add at the end (will use sequential naming)
    print("=" * 60)
    print("Example 1: Adding at the end")
    print("=" * 60)
    result = add_page(config_file, insert_after_index=None)

    # Example 2: Insert between index 6 and 7 (will use non-sequential)
    print("=" * 60)
    print("Example 2: Inserting between existing pages")
    print("=" * 60)
    result = add_page(config_file, insert_after_index=6)

    # Example 3: Replicate an existing page and insert it
    print("=" * 60)
    print("Example 3: Replicate Test007.kra and insert after it")
    print("=" * 60)
    result = add_page(config_file, insert_after_index=6, source_file="Test007.kra")

    # Show final state
    list_pages_with_indices(config_file)
