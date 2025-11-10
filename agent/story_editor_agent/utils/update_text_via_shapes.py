from krita import Krita
from .logs import write_log
from .update_text_in_kra import update_svg_text
import xml.etree.ElementTree as ET
from PyQt5.QtCore import QUuid
import re
import json


def update_text_via_shapes(doc, layer_groups: dict, client=None):
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

        for layer_id, layer_data in layer_groups.items():
            layer_id = layer_data.get('layer_id')
            shapes_to_update: list = layer_data.get('shapes', [])

            target_layer = doc.nodeByUniqueId(QUuid(layer_id))
            target_svg = target_layer.toSvg()

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
            ####################################

            for shape in target_layer.shapes():
                shape.remove()
            target_layer.addShapesFromSvg(modified_svg)
            doc.refreshProjection()

            ########################################
            # Handle shape removal
            shapes = target_layer.shapes()
            for shape in shapes:
                for update in shapes_to_update:
                    if shape.name() == update.get('shape_id') and update.get('remove_shape') == True:
                        shape.remove()
                        doc.refreshProjection()
                        if client:
                            progress_message = {
                                'type': 'shape_removal',
                                'message': f"{shape.name()} removed successfully"
                            }
                            client.write(json.dumps(
                                progress_message).encode('utf-8'))
                            client.flush()  # Ensure message is sent immediately

            ########################################
        return True

        # updated_count = 0
        # root = doc.rootNode()

        # # Process each layer
        # for layer_id, layer_updates in updates_by_layer.items():
        #     # Find the matching vector layer by uniqueId
        #     target_layer = None
        #     for layer in root.childNodes():
        #         if str(layer.type()) == "vectorlayer":
        #             if str(layer.uniqueId()) == layer_id:
        #                 target_layer = layer
        #                 write_log(
        #                     f"[DEBUG] Found matching layer: {layer.name()}")
        #                 break

        #     if not target_layer:
        #         write_log(
        #             f"[ERROR] Could not find vector layer with ID: {layer_id}")
        #         continue

        #     try:
        #         # Get the complete layer SVG
        #         layer_svg = target_layer.toSvg()
        #         write_log(
        #             f"[DEBUG] Original layer SVG length: {len(layer_svg)}")

        #         # Apply all updates to this layer's SVG
        #         modified_svg = layer_svg
        #         for update in layer_updates:
        #             shape_index = update.get('shape_index', 0)
        #             new_text = update.get('new_text')

        #             # Get the shape ID by index
        #             shapes = target_layer.shapes()
        #             if shape_index >= len(shapes):
        #                 write_log(
        #                     f"[ERROR] Shape index {shape_index} out of range")
        #                 continue

        #             shape_id = shapes[shape_index].name()
        #             write_log(f"[DEBUG] Shape ID: {shape_id}")

        #             # Find and update the specific text element in the SVG
        #             pattern = rf'<text[^>]*id="{re.escape(shape_id)}"[^>]*>.*?</text>'
        #             match = re.search(pattern, modified_svg, re.DOTALL)

        #             if not match:
        #                 write_log(
        #                     f"[ERROR] Could not find shape {shape_id} in SVG")
        #                 continue

        #             old_text_element = match.group(0)
        #             write_log(
        #                 f"[DEBUG] Found text element:\n{old_text_element}")

        #             # Update the text content
        #             new_text_element = update_svg_text(
        #                 old_text_element, new_text)

        #             if not new_text_element:
        #                 write_log(
        #                     f"[ERROR] Failed to update text for shape {shape_id}")
        #                 continue

        #             # Replace in the SVG
        #             modified_svg = modified_svg.replace(
        #                 old_text_element, new_text_element)
        #             write_log(f"[DEBUG] Updated text element in SVG")

        #         # Now update the entire layer
        #         write_log(f"[DEBUG] Removing all shapes from layer")
        #         for shape in target_layer.shapes():
        #             shape.remove()

        #         write_log(f"[DEBUG] Adding updated SVG to layer")
        #         write_log(f"[DEBUG] Modified SVG length: {len(modified_svg)}")

        #         result = target_layer.addShapesFromSvg(modified_svg)

        #         # ########################################
        #         # # Handle shape removal
        #         shapes = target_layer.shapes()
        #         for shape in shapes:
        #             for update in layer_updates:
        #                 if shape.name() == f"shape{update.get('shape_index')}" and update.get('remove_shape') == True:
        #                     shape.remove()
        #                     if client:
        #                         progress_message = {
        #                             'type': 'shape_removal',
        #                             'message': f"{shape.name()} removed successfully"
        #                         }
        #                         client.write(json.dumps(
        #                             progress_message).encode('utf-8'))
        #                         client.flush()  # Ensure message is sent immediately
        #         # if update.get('remove_shape') == True:
        #         #     shapes[shape_index].remove()
        #         #     # Send progress update to client if available
        #         #     if client:
        #         #         progress_message = {
        #         #             'type': 'progress',
        #         #             'message': f"Text shape {shape_id} removed successfully"
        #         #         }
        #         #         client.write(json.dumps(
        #         #             progress_message).encode('utf-8'))
        #         #         client.flush()  # Ensure message is sent immediately
        #         #     continue
        #         ########################################

        #         if result and len(result) > 0:
        #             write_log(
        #                 f"[DEBUG] Successfully updated layer with {len(result)} shape(s)")
        #             updated_count += 1
        #         else:
        #             write_log(
        #                 f"[ERROR] addShapesFromSvg returned empty list for layer {layer_id}")

        #     except Exception as layer_error:
        #         write_log(
        #             f"[ERROR] Failed to update layer {layer_id}: {layer_error}")
        #         import traceback
        #         write_log(traceback.format_exc())

        # write_log(f"[INFO] Successfully updated {updated_count} layer(s)")

        # # Refresh the document to show changes
        # doc.refreshProjection()
        # write_log("[DEBUG] Refreshed document projection")

        # return updated_count

    except Exception as e:
        write_log(f"[ERROR] Failed to update text via shapes: {e}")
        import traceback
        write_log(traceback.format_exc())
        return 0
