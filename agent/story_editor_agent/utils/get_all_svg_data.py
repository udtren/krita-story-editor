import zipfile
from krita import Krita
from ..utils.logs import write_log
from .extract_text_from_svg import extract_text_from_svg


def get_all_svg_data():
    """Extract text content from all vector layers using Krita API"""
    try:
        doc = Krita.instance().activeDocument()

        if not doc:
            write_log("[ERROR] No active document")
            return []

        write_log(f"[DEBUG] Document: {doc.name()}")

        svg_data = []
        root = doc.rootNode()

        # Iterate through all child nodes
        for layer in root.childNodes():
            if str(layer.type()) == "vectorlayer":
                svg_content = layer.toSvg()

                if svg_content:
                    svg_data.append({
                        'layer_name': layer.name(),
                        'layer_id': str(layer.uniqueId()),
                        'svg': svg_content
                    })
        return svg_data

    except Exception as e:
        write_log(f"Error extracting vector text: {e}")
        import traceback
        write_log(traceback.format_exc())
        return []
