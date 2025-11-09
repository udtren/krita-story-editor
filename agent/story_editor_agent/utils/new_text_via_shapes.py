from krita import Krita
from .logs import write_log
import uuid


def new_text_via_shapes(doc, update):
    """
    Add new text content in vector layers using Krita's shape API

    Args:
        doc: Krita document object
        update: Single update dictionary containing:
            - layer_id: Unique ID of the layer
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

        # Group updates by layer_id
        layer_id = new_layer.uniqueId()
        svg_content = update.get('svg_content', '')

        root = doc.rootNode()

        # Find the matching vector layer by uniqueId
        target_layer = None
        for layer in root.childNodes():
            if str(layer.type()) == "vectorlayer":
                if str(layer.uniqueId()) == layer_id:
                    target_layer = layer
                    write_log(
                        f"[DEBUG] Found matching layer: {layer.name()}")
                    break

        if not target_layer:
            write_log(
                f"[ERROR] Could not find vector layer with ID: {layer_id}")
            return

        try:
            result = target_layer.addShapesFromSvg(svg_content)

        except Exception as layer_error:
            write_log(
                f"[ERROR] Failed to update layer {layer_id}: {layer_error}")
            import traceback
            write_log(traceback.format_exc())

        # Refresh the document to show changes
        doc.refreshProjection()
        write_log("[DEBUG] Refreshed document projection")

        return result

    except Exception as e:
        write_log(f"[ERROR] Failed to update text via shapes: {e}")
        import traceback
        write_log(traceback.format_exc())
        return 0
