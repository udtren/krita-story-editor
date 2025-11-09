import zipfile
from krita import Krita
from ..utils.logs import write_log
from .extract_text_from_svg import extract_text_from_svg


def get_all_vector_text():
    """Extract text content from all vector layers by reading from .kra zip file"""
    try:
        doc = Krita.instance().activeDocument()
        kra_path = doc.fileName()

        if not kra_path:
            write_log("[ERROR] Document not saved - cannot access .kra file")
            return []

        write_log(f"[DEBUG] KRA file path: {kra_path}")

        text_layers = []

        # Open the .kra file as a zip
        with zipfile.ZipFile(kra_path, 'r') as kra_zip:
            # List all files to find the layer's content.svg
            all_files = kra_zip.namelist()
            write_log(f"[DEBUG] Total files in .kra: {len(all_files)}")

            # Search for content.svg files
            for file_path in all_files:
                if 'content.svg' in file_path and 'shapelayer' in file_path:
                    write_log(f"[DEBUG] Found potential SVG: {file_path}")

                    # Extract layer folder name from path
                    # e.g., "krita_test/layers/layer4.shapelayer/content.svg"
                    parts = file_path.split('/')
                    layer_folder = parts[-2] if len(parts) >= 2 else 'unknown'

                    # Read and extract text
                    svg_content = kra_zip.read(file_path).decode('utf-8')
                    text = extract_text_from_svg(svg_content)

                    if text:
                        # Always use text_elements array format
                        if isinstance(text, list):
                            text_layers.append({
                                'path': file_path,
                                'layer_folder': layer_folder,
                                'text_elements': text
                            })
                            write_log(f"[DEBUG] Found {len(text)} text elements in {file_path}")
                        else:
                            # Single element - still use array format
                            text_layers.append({
                                'path': file_path,
                                'layer_folder': layer_folder,
                                'text_elements': [text]
                            })
                            write_log(f"[DEBUG] Found 1 text element in {file_path}")
                    else:
                        write_log(f"[DEBUG] No text in {file_path}")

            write_log(f"[DEBUG] Total text layers found: {len(text_layers)}")
            return text_layers

    except Exception as e:
        write_log(f"Error extracting vector text: {e}")
        import traceback
        write_log(traceback.format_exc())
        return []
