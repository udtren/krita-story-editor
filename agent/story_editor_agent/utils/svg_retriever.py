from krita import Krita
import xml.etree.ElementTree as ET
import zipfile
import json
import os
import base64
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from .logs import write_log


def qimage_to_base64(qimage):
    """Convert QImage to base64-encoded PNG string"""
    if qimage is None or qimage.isNull():
        return None

    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.WriteOnly)
    qimage.save(buffer, "PNG")
    buffer.close()

    # Convert to base64 string
    base64_str = base64.b64encode(byte_array.data()).decode("utf-8")
    return f"data:image/png;base64,{base64_str}"


def krita_file_name_safe(doc):
    if doc.name() == "":
        if doc.fileName():
            doc_path = doc.fileName()
            doc_name = (
                os.path.basename(doc_path).replace(".kra", "")
                if doc
                else "krita_file_not_saved"
            )
        else:
            doc_name = "krita_file_not_saved"
    else:
        doc_name = doc.name()
    return doc_name


def get_opened_doc_svg_data(doc):
    """Extract text content from all vector layers using Krita API"""
    try:
        doc_path = doc.fileName() if doc else "krita_file_not_saved"
        doc_name = (
            os.path.basename(doc_path).replace(".kra", "")
            if doc
            else "krita_file_not_saved"
        )

        # Get thumbnail and convert to base64
        thumbnail_qimage = doc.thumbnail(128, 128)
        thumbnail_base64 = qimage_to_base64(thumbnail_qimage)

        if not doc:
            write_log("[ERROR] No active document")
            return []

        write_log(f"[DEBUG] Document: {doc_name}")

        svg_data = []
        response_data = {
            "document_name": doc_name,
            "document_path": os.path.normpath(doc_path),
            "svg_data": svg_data,
            "opened": True,
            "thumbnail": thumbnail_base64,
        }
        root = doc.rootNode()

        # Iterate through all child nodes
        for layer in root.childNodes():
            if str(layer.type()) == "vectorlayer":
                svg_content = layer.toSvg()

                if svg_content:
                    svg_data.append(
                        {
                            "layer_name": layer.name(),
                            "layer_id": layer.uniqueId().toString(),
                            "svg": svg_content,
                        }
                    )

        write_log(json.dumps(svg_data))
        return response_data

    except Exception as e:
        write_log(f"Error extracting vector text: {e}")
        import traceback

        write_log(traceback.format_exc())
        return []


def get_all_offline_docs_from_folder(folder_path, opened_docs_path=[]):
    """
    Scan a folder for .kra files and extract SVG data from each

    Args:
        folder_path: Path to the folder containing .kra files
        opened_docs_path: List of paths to documents that are already opened (skip these)

    Returns:
        List of dictionaries with SVG data from each .kra file
    """
    response_datas = []

    try:
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".kra") and not filename.lower().endswith(
                ".kra-autosave.kra"
            ):
                kra_path = os.path.join(folder_path, filename)
                kra_path = os.path.normpath(kra_path)

                write_log(f"[DEBUG] Found offline .kra file: {kra_path}")

                # Skip if this file is already opened in Krita
                if kra_path in opened_docs_path:
                    write_log(f"[DEBUG] Skipping opened document: {kra_path}")
                    continue

                response_data = _get_offline_doc_svg_data(kra_path)
                response_datas.append(response_data)

        return response_datas

    except Exception as e:
        raise Exception(f"Error scanning folder for .kra files: {e}")


def _get_offline_doc_svg_data(kra_path):
    """
    Extract all text from vector layers in a .kra file

    Args:
        kra_path: Path to the .kra file

    Returns:
        List of dictionaries with text layer information
    """
    svg_data = []
    response_data = {
        "document_name": os.path.basename(kra_path),
        "document_path": kra_path,
        "svg_data": svg_data,
        "opened": False,
        "thumbnail": None,
    }

    try:
        # Open the .kra file as a zip
        with zipfile.ZipFile(kra_path, "r") as kra_zip:
            all_files = kra_zip.namelist()

            # Extract preview.png if available
            if "preview.png" in all_files:
                try:
                    preview_data = kra_zip.read("preview.png")
                    # Convert to base64
                    preview_base64 = base64.b64encode(preview_data).decode("utf-8")
                    response_data["thumbnail"] = (
                        f"data:image/png;base64,{preview_base64}"
                    )
                except Exception as e:
                    write_log(f"[WARNING] Could not read preview.png: {e}")
                    response_data["thumbnail"] = None

            # Search for content.svg files
            for index, file_path in enumerate(all_files):
                if "content.svg" in file_path and "shapelayer" in file_path:
                    # Extract layer folder name from path
                    parts = file_path.split("/")
                    layer_folder = parts[-2] if len(parts) >= 2 else "unknown"

                    # Get SVG content
                    svg_content = kra_zip.read(file_path).decode("utf-8")

                    if svg_content:
                        svg_data.append(
                            {
                                "layer_name": layer_folder,
                                "layer_id": layer_folder,
                                "svg": svg_content,
                            }
                        )

            return response_data

    except Exception as e:
        raise Exception(f"Error reading .kra file: {e}")


def get_svg_from_activenode():
    """
    Get SVG data from the active node (if it's a vector layer)
    Prints shape names and SVG content to stdout
    """
    doc = Krita.instance().activeDocument()

    if not doc:
        print("No active document")
        return

    active_node = doc.activeNode()

    if not active_node:
        print("No active node")
        return

    if str(active_node.type()) == "vectorlayer":
        print(f"Vector Layer Full SVG Data\n")
        print("=" * 60)
        print(active_node.toSvg())
        print("=" * 60)

        shapes = active_node.shapes()

        if not shapes:
            print("No shapes found in vector layer")
            return

        print(f"Layer Name: {active_node.name()}")
        print(f"Node Id: {active_node.uniqueId()}")
        print(f"Node Id String: {active_node.uniqueId().toString()}")
        print(f"Number of shapes: {len(shapes)}\n")
        print("=" * 60)

        for idx, shape in enumerate(shapes):
            print(f"\n--- Shape {idx + 1} ---")
            print(f"Name: {shape.name()}")
            print(f"\nSVG Content:")
            print(shape.toSvg())
            print("=" * 60)
    else:
        print(f"Active node is not a vector layer. Type: {active_node.type()}")


def extract_text_from_svg(svg_content):
    """Extract text from SVG content string"""
    try:
        # Parse SVG
        root = ET.fromstring(svg_content)

        # Collect text elements with their HTML
        text_elements = []

        # Search for text elements (with namespace)
        for elem in root.iter():
            tag_lower = elem.tag.lower()
            if "text" in tag_lower and elem.tag.endswith("text"):
                # This is a <text> element, not a <textPath> or similar
                write_log(f"[DEBUG] Found text element with tag: {elem.tag}")

                # Get the text content
                elem_text = "".join(elem.itertext()).strip()

                if elem_text:
                    # Convert element to HTML string (outer HTML)
                    outer_html = ET.tostring(elem, encoding="unicode", method="xml")

                    text_elements.append({"text": elem_text, "html": outer_html})
                    write_log(f"[DEBUG] Extracted text element #{len(text_elements)}")

        write_log(f"[DEBUG] Total text elements found: {len(text_elements)}")

        return text_elements

    except Exception as e:
        write_log(f"Error parsing SVG: {e}")
        import traceback

        write_log(traceback.format_exc())
        return ""


# def _extract_text_from_svg(svg_content):
#     """Extract text elements from SVG content string"""
#     try:
#         # Parse SVG
#         root = ET.fromstring(svg_content)

#         # Collect text elements with their HTML
#         text_elements = []

#         # Search for text elements
#         for elem in root.iter():
#             tag_lower = elem.tag.lower()
#             if 'text' in tag_lower and elem.tag.endswith('text'):
#                 # Get the text content
#                 elem_text = ''.join(elem.itertext()).strip()

#                 if elem_text:
#                     # Convert element to HTML string (outer HTML)
#                     outer_html = ET.tostring(
#                         elem, encoding='unicode', method='xml')

#                     text_elements.append({
#                         'text': elem_text,
#                         'html': outer_html
#                     })

#         return text_elements

#     except Exception as e:
#         raise Exception(f"Error parsing SVG: {e}")
