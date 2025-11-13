from krita import Krita
from .logs import write_log
import xml.etree.ElementTree as ET
from PyQt5.QtCore import QUuid
import uuid
import zipfile
import os
import tempfile
import shutil
import re


def update_doc_layers_svg(doc, existing_texts_updated: [dict]):
    """
    layer_svg_data format:
    {
        "layer_name": layer_name,
        "layer_id": layer_id,
        "svg_data": valid_svg_data,
    }
    """
    updated_layer_count = 0
    try:
        for layer_svg_data in existing_texts_updated:
            layer_id = layer_svg_data.get("layer_id")
            svg_data = layer_svg_data.get("svg_data")
            target_layer = doc.nodeByUniqueID(QUuid(layer_id))

            if target_layer:
                for shape in target_layer.shapes():
                    shape.remove()
                target_layer.addShapesFromSvg(svg_data)
                updated_layer_count += 1
                doc.refreshProjection()
        return {
            "success": True,
            "result": f"Updated {updated_layer_count} layers.",
            "count": updated_layer_count,
        }

    except Exception as e:
        write_log(f"[ERROR] Failed to update layer SVG: {str(e)}")


def add_svg_layer_to_doc(doc, new_texts_added: [dict]):
    """
    Add new text content in vector layers using Krita's shape API

    Args:
        doc: Krita document object
        svg_data: Single svg_data dictionary containing:
            - svg_data: Full SVG content of the layer

    Returns:
        Number of successfully updated layers
    """
    new_layer_count = 0
    try:
        for new_text in new_texts_added:
            svg_data = new_text.get("svg_data", "")

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

            new_layer.addShapesFromSvg(svg_data)

            # Refresh the document to show changes
            doc.refreshProjection()
            new_layer_count += 1

        return {
            "success": True,
            "result": f"Added {new_layer_count} new layers.",
            "count": new_layer_count,
        }

    except Exception as e:
        write_log(f"[ERROR] Failed to add new svg data: {e}")
        return {"success": False}


def update_offline_kra_file(doc_path, existing_texts_updated: [dict]):
    """
    Update text in an offline .kra file

    Args:
        doc_path: Path to the .kra file
        existing_texts_updated: List of dictionaries containing updated text information for layers
            {
                "layer_name": layer_name,
                "layer_id": layer_id,
                "svg_data": valid_svg_data,
            }
        layer_name = layer_id = krita_folder_name
    Returns:
        Dictionary with success status and update count
    """
    layer_updated_count = 0

    try:
        # Get the document name without extension
        doc_name = os.path.splitext(os.path.basename(doc_path))[0]

        # Create a backup
        backup_path = doc_path + ".backup"
        shutil.copy2(doc_path, backup_path)

        # Create a mapping of file paths to new SVG data
        modified_files = {}
        for layer_data in existing_texts_updated:
            layer_name = layer_data.get("layer_name")
            layer_id = layer_data.get("layer_id")
            svg_data = layer_data.get("svg_data")

            # Build the expected SVG file path inside the .kra
            svg_path_in_kra = f"{doc_name}/layers/{layer_id}/content.svg"
            modified_files[svg_path_in_kra] = svg_data

        # Create a temporary file for the new .kra
        temp_kra = tempfile.NamedTemporaryFile(delete=False, suffix=".kra")
        temp_kra_path = temp_kra.name
        temp_kra.close()

        # Read from original and write to temporary file
        with zipfile.ZipFile(backup_path, "r") as original_kra:
            with zipfile.ZipFile(temp_kra_path, "w", zipfile.ZIP_DEFLATED) as new_kra:
                # Copy all files from original, replacing modified ones
                for file_path in original_kra.namelist():
                    if file_path in modified_files:
                        # Write the modified SVG
                        new_kra.writestr(
                            file_path, modified_files[file_path].encode("utf-8")
                        )
                        layer_updated_count += 1
                    else:
                        # Copy original file unchanged
                        file_data = original_kra.read(file_path)
                        new_kra.writestr(file_path, file_data)

        # Replace original with updated file
        shutil.move(temp_kra_path, doc_path)

        return {
            "success": True,
            "result": f"{doc_name} (offline):\n  Updated {layer_updated_count} layers.",
            "count": layer_updated_count,
        }

    except Exception as e:
        write_log(f"[ERROR] Failed to update offline .kra file: {e}")
        # Try to restore from backup if something went wrong
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, doc_path)
            except:
                pass
        return {
            "success": False,
            "error": str(e),
        }
