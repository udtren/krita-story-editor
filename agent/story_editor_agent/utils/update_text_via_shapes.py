from krita import Krita
from .logs import write_log
from .update_text_in_kra import update_svg_text
import re


def update_text_via_shapes(doc, updates):
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

        write_log(f"[DEBUG] Updating text via shapes API")
        write_log(f"[DEBUG] Number of updates: {len(updates)}")

        # Group updates by layer_id
        updates_by_layer = {}
        for update in updates:
            layer_id = update.get('layer_id')
            if layer_id not in updates_by_layer:
                updates_by_layer[layer_id] = []
            updates_by_layer[layer_id].append(update)

        updated_count = 0
        root = doc.rootNode()

        # Process each layer
        for layer_id, layer_updates in updates_by_layer.items():
            write_log(f"[DEBUG] Processing layer ID: {layer_id} with {len(layer_updates)} update(s)")

            # Find the matching vector layer by uniqueId
            target_layer = None
            for layer in root.childNodes():
                if str(layer.type()) == "vectorlayer":
                    if str(layer.uniqueId()) == layer_id:
                        target_layer = layer
                        write_log(f"[DEBUG] Found matching layer: {layer.name()}")
                        break

            if not target_layer:
                write_log(f"[ERROR] Could not find vector layer with ID: {layer_id}")
                continue

            try:
                # Get the complete layer SVG
                layer_svg = target_layer.toSvg()
                write_log(f"[DEBUG] Original layer SVG length: {len(layer_svg)}")

                # Apply all updates to this layer's SVG
                modified_svg = layer_svg
                for update in layer_updates:
                    shape_index = update.get('shape_index', 0)
                    new_text = update.get('new_text')
                    layer_name = update.get('layer_name', 'unknown')

                    write_log(f"[DEBUG] Updating shape {shape_index} in layer {layer_name}")
                    write_log(f"[DEBUG] New text: {new_text}")

                    # Get the shape ID by index
                    shapes = target_layer.shapes()
                    if shape_index >= len(shapes):
                        write_log(f"[ERROR] Shape index {shape_index} out of range")
                        continue

                    shape_id = shapes[shape_index].name()
                    write_log(f"[DEBUG] Shape ID: {shape_id}")

                    # Find and update the specific text element in the SVG
                    pattern = rf'<text[^>]*id="{re.escape(shape_id)}"[^>]*>.*?</text>'
                    match = re.search(pattern, modified_svg, re.DOTALL)

                    if not match:
                        write_log(f"[ERROR] Could not find shape {shape_id} in SVG")
                        continue

                    old_text_element = match.group(0)
                    write_log(f"[DEBUG] Found text element:\n{old_text_element}")

                    # Update the text content
                    new_text_element = update_svg_text(old_text_element, new_text)

                    if not new_text_element:
                        write_log(f"[ERROR] Failed to update text for shape {shape_id}")
                        continue

                    # Replace in the SVG
                    modified_svg = modified_svg.replace(old_text_element, new_text_element)
                    write_log(f"[DEBUG] Updated text element in SVG")

                # Now update the entire layer
                write_log(f"[DEBUG] Removing all shapes from layer")
                for shape in target_layer.shapes():
                    shape.remove()

                write_log(f"[DEBUG] Adding updated SVG to layer")
                write_log(f"[DEBUG] Modified SVG length: {len(modified_svg)}")

                result = target_layer.addShapesFromSvg(modified_svg)

                if result and len(result) > 0:
                    write_log(f"[DEBUG] Successfully updated layer with {len(result)} shape(s)")
                    updated_count += 1
                else:
                    write_log(f"[ERROR] addShapesFromSvg returned empty list for layer {layer_id}")

            except Exception as layer_error:
                write_log(f"[ERROR] Failed to update layer {layer_id}: {layer_error}")
                import traceback
                write_log(traceback.format_exc())

        write_log(f"[INFO] Successfully updated {updated_count} layer(s)")

        # Refresh the document to show changes
        doc.refreshProjection()
        write_log("[DEBUG] Refreshed document projection")

        return updated_count

    except Exception as e:
        write_log(f"[ERROR] Failed to update text via shapes: {e}")
        import traceback
        write_log(traceback.format_exc())
        return 0
