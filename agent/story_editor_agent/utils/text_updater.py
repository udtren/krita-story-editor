from krita import Krita
from .logs import write_log
from .update_text_in_kra import update_svg_text
from .xml_formatter import remove_namespace_prefixes
import xml.etree.ElementTree as ET
from PyQt5.QtCore import QUuid
import uuid


def update_doc_layers_svg(doc, layer_groups: dict, client=None):
    """
    Update text content in vector layers using Krita's shape API

    Args:
        doc: Krita document object
        updates: List of update dictionaries containing:
            - layer_id: Unique ID of the layer
            - layer_name: Name of the layer
            - shape_index: Index of the shape within the layer
            - new_text: New text content

    Returns:
        Number of successfully updated layers
    """
    try:
        if not doc:
            write_log("[ERROR] No active document")
            return 0

        updated_layer_count = 0
        removed_shape_count = 0

        for layer_id, layer_data in layer_groups.items():
            layer_id = layer_data.get('layer_id')
            shapes_to_update: list = layer_data.get('shapes', [])

            target_layer = doc.nodeByUniqueID(QUuid(layer_id))
            target_svg = target_layer.toSvg()

            write_log(
                f"Start updating target_layer: {target_layer.name()} with ID: {layer_id}")
            write_log(f"target shapes_to_update: {shapes_to_update}")

            ####################################
            root = ET.fromstring(target_svg)

            namespaces = {
                'svg': 'http://www.w3.org/2000/svg',
                'krita': 'http://krita.org/namespaces/svg/krita'
            }

            text_elements = root.findall('.//svg:text', namespaces)
            for text_elem in text_elements:
                element_id = text_elem.get('id')
                for shape in shapes_to_update:
                    if shape['shape_id'] == element_id:
                        text_elem.text = shape['new_text']
            modified_svg = ET.tostring(root, encoding='unicode')

            modified_svg = remove_namespace_prefixes(modified_svg)

            write_log(
                f"Modified SVG for layer {target_layer.name()}: {modified_svg}")
            ####################################

            for shape in target_layer.shapes():
                shape.remove()
            target_layer.addShapesFromSvg(modified_svg)
            updated_layer_count += 1
            doc.refreshProjection()

            ########################################
            # Handle shape removal

            shapes = target_layer.shapes()
            for shape in shapes:
                for update in shapes_to_update:
                    if shape.name() == update.get('shape_id') and update.get('remove_shape') == True:
                        shape.remove()
                        doc.refreshProjection()
                        removed_shape_count += 1
            ########################################
        return {
            'success': True,
            'updated_layer_count': updated_layer_count,
            'removed_shapes_count': removed_shape_count
        }

    except Exception as e:
        write_log(f"[ERROR] Failed to update text via shapes: {e}")
        import traceback
        write_log(traceback.format_exc())
        return 0


def add_svg_layer_to_doc(doc, svg_content):
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
