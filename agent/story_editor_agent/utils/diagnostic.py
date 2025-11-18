import json
import os
from pathlib import Path
import chardet  # For automatic encoding detection


def detect_encoding(file_path):
    """
    Detect the encoding of a file.

    Args:
        file_path: Path to the file

    Returns:
        str: Detected encoding name
    """
    with open(file_path, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result["encoding"]


def get_comic_config_info(folder_path):
    """
    Check for comicConfig.json in the given folder and extract information.
    Handles various file encodings automatically.

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

        # Try multiple encoding strategies
        config = None
        encodings_to_try = [
            "utf-8",
            "utf-8-sig",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "cp1252",
            "shift_jis",
        ]

        # First, try to detect encoding
        try:
            detected_encoding = detect_encoding(config_path)
            if detected_encoding:
                print(f"Detected encoding: {detected_encoding}")
                encodings_to_try.insert(0, detected_encoding)
        except:
            pass

        # Try each encoding
        last_error = None
        for encoding in encodings_to_try:
            try:
                with open(config_path, "r", encoding=encoding) as f:
                    config = json.load(f)
                print(f"Successfully read file with encoding: {encoding}")
                break
            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                continue
            except json.JSONDecodeError as e:
                # File was decoded but JSON is invalid
                return {
                    "error": f"JSON decode error with {encoding}: {str(e)}",
                    "config_filepath": str(config_path),
                }

        if config is None:
            return {
                "error": f"Could not decode file with any encoding. Last error: {str(last_error)}",
                "config_filepath": str(config_path),
            }

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

    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "config_filepath": str(config_path) if "config_path" in locals() else None,
        }


# Simpler version without chardet dependency
def get_comic_config_info_simple(folder_path):
    """
    Version without chardet dependency - tries common encodings.
    """
    try:
        folder = Path(folder_path)
        parent_dir = folder.parent
        config_path = parent_dir / "comicConfig.json"

        if not config_path.exists():
            print(f"comicConfig.json not found at: {config_path}")
            return None

        # Try common encodings
        encodings = [
            "utf-8-sig",  # UTF-8 with BOM
            "utf-8",  # UTF-8 without BOM
            "utf-16",  # UTF-16 (auto-detects LE/BE)
            "utf-16-le",  # UTF-16 Little Endian
            "utf-16-be",  # UTF-16 Big Endian
            "shift_jis",  # Japanese encoding
            "cp932",  # Windows Japanese
            "cp1252",  # Windows Western
        ]

        config = None
        successful_encoding = None

        for encoding in encodings:
            try:
                with open(config_path, "r", encoding=encoding) as f:
                    config = json.load(f)
                successful_encoding = encoding
                print(f"✓ Successfully read file with encoding: {encoding}")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except json.JSONDecodeError as e:
                return {
                    "error": f"JSON decode error with {encoding}: {str(e)}",
                    "config_filepath": str(config_path),
                }

        if config is None:
            # Try reading as binary to see the first few bytes
            with open(config_path, "rb") as f:
                first_bytes = f.read(10)
                hex_bytes = " ".join(f"{b:02x}" for b in first_bytes)

            return {
                "error": f"Could not decode file with any common encoding. First bytes: {hex_bytes}",
                "config_filepath": str(config_path),
                "hint": "File might be corrupted or in an unusual encoding",
            }

        # Extract required values
        page_number = config.get("pageNumber", 0)
        pages = config.get("pages", [])
        template_location = config.get("templateLocation", "templates")

        # Construct full path to template location
        template_dir = parent_dir / template_location

        # Find all .kra files in template location
        template_files = []
        if template_dir.exists() and template_dir.is_dir():
            kra_files = list(template_dir.glob("*.kra"))
            template_files = [str(kra_file) for kra_file in sorted(kra_files)]
        else:
            print(f"Warning: Template directory not found: {template_dir}")

        result = {
            "config_filepath": str(config_path),
            "pageNumber": page_number,
            "pages": pages,
            "templateLocation": template_location,
            "template_files": template_files,
            "encoding_used": successful_encoding,
        }

        return result

    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "config_filepath": str(config_path) if "config_path" in locals() else None,
        }


# Diagnostic function
def diagnose_json_file(file_path):
    """
    Diagnose encoding issues with a JSON file.
    """
    print(f"Diagnosing file: {file_path}")
    print("-" * 80)

    if not os.path.exists(file_path):
        print("File does not exist!")
        return

    # Read first 100 bytes
    with open(file_path, "rb") as f:
        first_bytes = f.read(100)

    print(f"File size: {os.path.getsize(file_path)} bytes")
    print(f"\nFirst 20 bytes (hex):")
    print(" ".join(f"{b:02x}" for b in first_bytes[:20]))

    print(f"\nFirst 20 bytes (decimal):")
    print(" ".join(f"{b:3d}" for b in first_bytes[:20]))

    # Check for BOM (Byte Order Mark)
    if first_bytes[:3] == b"\xef\xbb\xbf":
        print("\n✓ BOM detected: UTF-8 with BOM (use 'utf-8-sig')")
    elif first_bytes[:2] == b"\xff\xfe":
        print("\n✓ BOM detected: UTF-16 Little Endian (use 'utf-16-le' or 'utf-16')")
    elif first_bytes[:2] == b"\xfe\xff":
        print("\n✓ BOM detected: UTF-16 Big Endian (use 'utf-16-be' or 'utf-16')")
    else:
        print("\n✗ No standard BOM detected")

    # Try to display as text with different encodings
    print("\n" + "=" * 80)
    print("Attempting to read with different encodings:")
    print("=" * 80)

    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "shift_jis", "cp932"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read(200)  # Read first 200 characters
            print(f"\n{encoding}:")
            print(f"  ✓ Success! Preview: {content[:100]}")
        except Exception as e:
            print(f"\n{encoding}:")
            print(f"  ✗ Failed: {type(e).__name__}")


# Example usage
if __name__ == "__main__":
    folder_path = r"C:\Users\udtre\Work\Painting\My_Creations\Comic\タイトル未定\1_part3_new\pages"

    # First, diagnose the file
    config_path = Path(folder_path).parent / "comicConfig.json"
    if config_path.exists():
        print("Running diagnostics on comicConfig.json:")
        print("=" * 80)
        diagnose_json_file(config_path)
        print("\n\n")

    # Then try to read it
    print("Attempting to read config:")
    print("=" * 80)
    result = get_comic_config_info_simple(folder_path)

    if result:
        if "error" in result:
            print(f"\nError: {result['error']}")
            if "hint" in result:
                print(f"Hint: {result['hint']}")
        else:
            print("\n✓ Successfully read config!")
            print(json.dumps(result, indent=4, ensure_ascii=False))
