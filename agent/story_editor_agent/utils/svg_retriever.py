import zipfile
import json
from krita import Krita
from .logs import write_log
import xml.etree.ElementTree as ET
from ..utils.logs import write_log


def get_opened_doc_svg_data(doc):
    """Extract text content from all vector layers using Krita API"""
    try:
        doc_path = doc.fileName() if doc else "krita_file_not_saved"
        doc_name = doc.name() if doc else "krita_file_not_saved"

        if not doc:
            write_log("[ERROR] No active document")
            return []

        write_log(f"[DEBUG] Document: {doc.name()}")

        svg_data = []
        response_data = {
            'document_name': doc_name,
            'document_path': doc_path,
            'svg_data': svg_data
        }
        root = doc.rootNode()

        # Iterate through all child nodes
        for layer in root.childNodes():
            if str(layer.type()) == "vectorlayer":
                svg_content = layer.toSvg()

                if svg_content:
                    svg_data.append({
                        'layer_name': layer.name(),
                        'layer_id': layer.uniqueId().toString(),
                        'svg': svg_content
                    })

        write_log(json.dumps(svg_data))
        return response_data

    except Exception as e:
        write_log(f"Error extracting vector text: {e}")
        import traceback
        write_log(traceback.format_exc())
        return []


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
            if 'text' in tag_lower and elem.tag.endswith('text'):
                # This is a <text> element, not a <textPath> or similar
                write_log(f"[DEBUG] Found text element with tag: {elem.tag}")

                # Get the text content
                elem_text = ''.join(elem.itertext()).strip()

                if elem_text:
                    # Convert element to HTML string (outer HTML)
                    outer_html = ET.tostring(
                        elem, encoding='unicode', method='xml')

                    text_elements.append({
                        'text': elem_text,
                        'html': outer_html
                    })
                    write_log(
                        f"[DEBUG] Extracted text element #{len(text_elements)}")

        write_log(f"[DEBUG] Total text elements found: {len(text_elements)}")

        return text_elements

    except Exception as e:
        write_log(f"Error parsing SVG: {e}")
        import traceback
        write_log(traceback.format_exc())
        return ''
