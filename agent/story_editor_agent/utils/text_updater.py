from krita import Krita
from .logs import write_log
from .update_text_in_kra import update_svg_text
from .xml_formatter import remove_namespace_prefixes
import xml.etree.ElementTree as ET
from PyQt5.QtCore import QUuid
import uuid
import zipfile
import os
import tempfile
import shutil
import re


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
                        new_text = shape['new_text']

                        # Find tspan elements
                        tspan_elements = text_elem.findall('.//svg:tspan', namespaces)

                        if tspan_elements:
                            # Split new text by newlines to match multiple tspans
                            text_lines = new_text.split('\n')

                            # Update existing tspans
                            for i, tspan in enumerate(tspan_elements):
                                if i < len(text_lines):
                                    tspan.text = text_lines[i]
                                else:
                                    tspan.text = ''

                            # If we have more lines than tspans, add new tspans
                            if len(text_lines) > len(tspan_elements):
                                for i in range(len(tspan_elements), len(text_lines)):
                                    # Create new tspan based on the last one's attributes
                                    last_tspan = tspan_elements[-1]
                                    new_tspan = ET.SubElement(text_elem, '{http://www.w3.org/2000/svg}tspan')
                                    new_tspan.set('x', last_tspan.get('x', '0'))
                                    dy_value = last_tspan.get('dy', '12')
                                    new_tspan.set('dy', dy_value)
                                    new_tspan.text = text_lines[i]
                        else:
                            # No tspans, set text directly (fallback)
                            text_elem.text = new_text
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


def update_offline_kra_file(kra_path, layer_groups):
    """
    Update text in an offline .kra file

    Args:
        kra_path: Path to the .kra file
        layer_groups: Dictionary where keys are layer_ids and values contain shapes to update

    Returns:
        Dictionary with success status and update count
    """
    try:
        updated_layer_count = 0
        removed_shapes_count = 0

        # Get the document name without extension
        doc_name = os.path.splitext(os.path.basename(kra_path))[0]

        # Create a backup
        backup_path = kra_path + '.backup'
        shutil.copy2(kra_path, backup_path)

        try:
            # Read the original .kra file
            with zipfile.ZipFile(kra_path, 'r') as kra_zip:
                all_files = kra_zip.namelist()

                # Store modified files
                modified_files = {}

                # Process each layer group
                for layer_id, layer_data in layer_groups.items():
                    shapes_to_update = layer_data.get('shapes', [])

                    # Build the expected SVG file path inside the .kra
                    svg_path_in_kra = f"{doc_name}/layers/{layer_id}/content.svg"

                    if svg_path_in_kra not in all_files:
                        write_log(
                            f"[WARNING] SVG file not found in .kra: {svg_path_in_kra}")
                        continue

                    # Read the SVG content directly from the zip
                    svg_content = kra_zip.read(svg_path_in_kra).decode('utf-8')

                    # Parse the SVG using ElementTree
                    # Register namespaces to preserve them in output
                    ET.register_namespace('', 'http://www.w3.org/2000/svg')
                    ET.register_namespace(
                        'krita', 'http://krita.org/namespaces/svg/krita')
                    ET.register_namespace(
                        'xlink', 'http://www.w3.org/1999/xlink')
                    ET.register_namespace(
                        'sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')

                    root = ET.fromstring(svg_content)

                    # Define namespaces
                    namespaces = {
                        'svg': 'http://www.w3.org/2000/svg',
                        'krita': 'http://krita.org/namespaces/svg/krita'
                    }

                    # Update each shape in this layer
                    for shape_update in shapes_to_update:
                        shape_id = shape_update.get('shape_id')
                        new_text = shape_update.get('new_text')
                        remove_shape = shape_update.get('remove_shape', False)

                        write_log(
                            f"[DEBUG] Updating shape {shape_id} in layer {layer_id}")

                        # Find the text element by id (without namespace prefix in search)
                        text_elem = None
                        for elem in root.iter():
                            if elem.get('id') == shape_id:
                                text_elem = elem
                                break

                        if text_elem is None:
                            write_log(
                                f"[WARNING] Shape {shape_id} not found in SVG")
                            continue

                        if remove_shape:
                            # Remove the element from the tree
                            root.remove(text_elem)
                            write_log(f"[DEBUG] Removed shape {shape_id}")
                            updated_layer_count += 1
                            removed_shapes_count += 1
                        else:
                            # Update the text content
                            # Find tspan elements
                            tspan_elements = text_elem.findall('.//svg:tspan', namespaces)

                            if tspan_elements:
                                # Split new text by newlines to match multiple tspans
                                text_lines = new_text.split('\n')

                                # Update existing tspans
                                for i, tspan in enumerate(tspan_elements):
                                    if i < len(text_lines):
                                        tspan.text = text_lines[i]
                                    else:
                                        tspan.text = ''

                                # If we have more lines than tspans, add new tspans
                                if len(text_lines) > len(tspan_elements):
                                    for i in range(len(tspan_elements), len(text_lines)):
                                        # Create new tspan based on the last one's attributes
                                        last_tspan = tspan_elements[-1]
                                        new_tspan = ET.SubElement(text_elem, '{http://www.w3.org/2000/svg}tspan')
                                        new_tspan.set('x', last_tspan.get('x', '0'))
                                        dy_value = last_tspan.get('dy', '12')
                                        new_tspan.set('dy', dy_value)
                                        new_tspan.text = text_lines[i]
                            else:
                                # No tspans, set text directly (fallback)
                                text_elem.text = new_text

                            write_log(f"[DEBUG] Updated shape {shape_id}")
                            updated_layer_count += 1

                    # Convert back to string
                    modified_svg = ET.tostring(
                        root, encoding='unicode', method='xml')

                    # Clean namespace prefixes to match Krita's format
                    modified_svg = remove_namespace_prefixes(modified_svg)

                    # Store the modified SVG
                    modified_files[svg_path_in_kra] = modified_svg

            # Create a new .kra file with the updated content
            with zipfile.ZipFile(backup_path, 'r') as original_kra:
                with zipfile.ZipFile(kra_path, 'w', zipfile.ZIP_DEFLATED) as new_kra:
                    # Copy all files from original, replacing modified ones
                    for file_path in original_kra.namelist():
                        if file_path in modified_files:
                            # Write the modified SVG
                            new_kra.writestr(
                                file_path, modified_files[file_path].encode('utf-8'))
                        else:
                            # Copy original file as-is
                            file_data = original_kra.read(file_path)
                            new_kra.writestr(file_path, file_data)

            # Remove backup if successful
            os.remove(backup_path)
            write_log(f"[INFO] Successfully updated {kra_path}")

            return {
                'success': True,
                'updated_layer_count': updated_layer_count,
                'removed_shapes_count': removed_shapes_count
            }

        except Exception as e:
            # Restore from backup if something went wrong
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, kra_path)
                os.remove(backup_path)
            raise e

    except Exception as e:
        write_log(f"[ERROR] Failed to update offline .kra file: {e}")
        import traceback
        write_log(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }
