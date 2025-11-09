from krita import Krita
from .logs import write_log
import uuid


def new_text_via_shapes(doc, svg_content):
    """
    Add new text content in vector layers using Krita's shape API

    Args:
        doc: Krita document object
        svg_content: Single svg_content dictionary containing:
            - svg_content: Full SVG content of the layer

    Returns:
        Number of successfully updated layers
    """
    try:
        if not doc:
            write_log("[ERROR] No active document")
            return 0

        ###################################
        # Create new vector layer
        ###################################
        layer_name = f"Text-{uuid.uuid4().hex[:4]}"
        new_layer = doc.createVectorLayer(layer_name)
        doc.rootNode().addChildNode(new_layer, None)
        doc.refreshProjection()

        result = new_layer.addShapesFromSvg(svg_content)

        # Refresh the document to show changes
        doc.refreshProjection()
        write_log("[DEBUG] Refreshed document projection")

        return result

    except Exception as e:
        write_log(f"[ERROR] Failed to update text via shapes: {e}")
        import traceback
        write_log(traceback.format_exc())
        return 0
