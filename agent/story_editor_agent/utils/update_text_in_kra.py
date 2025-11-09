import zipfile
import xml.etree.ElementTree as ET
import tempfile
import shutil
import os
import re
from krita import Krita
from ..utils.logs import write_log


def update_text_in_kra(doc, updates):
    """
    Update text content in the .kra file

    Args:
        doc: Krita document object
        updates: List of update dictionaries containing:
            - layer_path: Path to the SVG file in the .kra
            - new_text: New text content
            - original_html: Original HTML/SVG element

    Returns:
        Number of successfully updated layers
    """
    try:
        kra_path = doc.fileName()

        if not kra_path:
            write_log("[ERROR] Document not saved - cannot update .kra file")
            return 0

        write_log(f"[DEBUG] Updating .kra file: {kra_path}")
        write_log(f"[DEBUG] Number of updates: {len(updates)}")

        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the .kra file
            with zipfile.ZipFile(kra_path, 'r') as kra_zip:
                kra_zip.extractall(temp_dir)

            updated_count = 0

            # Process each update
            for update in updates:
                layer_path = update.get('layer_path')
                new_text = update.get('new_text')

                write_log(f"[DEBUG] Processing update for: {layer_path}")
                write_log(f"[DEBUG] New text: {new_text}")

                # Full path to the SVG file
                svg_file_path = os.path.join(temp_dir, layer_path)

                if not os.path.exists(svg_file_path):
                    write_log(f"[ERROR] SVG file not found: {svg_file_path}")
                    continue

                # Read and parse the SVG
                with open(svg_file_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()

                # Update the text in SVG
                updated_svg = update_svg_text(svg_content, new_text)

                if updated_svg:
                    # Write back the modified SVG
                    with open(svg_file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_svg)

                    updated_count += 1
                    write_log(f"[DEBUG] Successfully updated: {layer_path}")
                else:
                    write_log(f"[ERROR] Failed to update SVG: {layer_path}")

            # Create a new .kra file with updated content
            # First, backup the original
            backup_path = kra_path + '.backup'
            shutil.copy2(kra_path, backup_path)
            write_log(f"[DEBUG] Created backup: {backup_path}")

            # Create new .kra file
            with zipfile.ZipFile(kra_path, 'w', zipfile.ZIP_DEFLATED) as kra_zip:
                # Add all files from temp directory back to the zip
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        kra_zip.write(file_path, arcname)

            write_log(
                f"[DEBUG] Successfully created new .kra file with {updated_count} updates")

            try:
                #######################################################
                # Reload Document
                #######################################################
                write_log("[INFO] Reloading document in Krita...")

                # Save current document name for reopening
                doc_name = doc.name()

                # Close the document (this releases the file lock)
                doc.close()
                write_log(f"[DEBUG] Closed document: {doc_name}")

                # Reopen the updated document
                krita_app = Krita.instance()
                new_doc = krita_app.openDocument(kra_path)

                if new_doc:
                    # Add the document to the active window to make it visible
                    active_window = krita_app.activeWindow()
                    if active_window:
                        # Add the document to all views in the active window
                        active_window.addView(new_doc)
                        write_log(f"[DEBUG] Added document to active window")

                    # Set as active document
                    krita_app.setActiveDocument(new_doc)
                    write_log(
                        f"[INFO] ✅ Document reloaded and displayed successfully: {doc_name}")
                else:
                    write_log("[ERROR] Failed to reopen document")
                #######################################################

            except Exception as reload_error:
                write_log(f"[ERROR] Failed to reload document: {reload_error}")
                import traceback
                write_log(traceback.format_exc())

            return updated_count

    except Exception as e:
        write_log(f"[ERROR] Failed to update .kra file: {e}")
        import traceback
        write_log(traceback.format_exc())
        return 0


def update_svg_text(svg_content, new_text):
    """
    Update text content in SVG string while preserving the exact structure
    Uses regex-based replacement to maintain Krita's specific XML format

    Args:
        svg_content: SVG content as string
        new_text: New text to replace

    Returns:
        Updated SVG content or None if failed
    """
    try:
        # Escape special XML characters in the new text
        new_text_escaped = (new_text
                            .replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('"', '&quot;')
                            .replace("'", '&apos;'))

        # Find the text element and replace its content
        # Pattern matches: <text ...>CONTENT</text>
        # Where CONTENT can include text and <tspan> elements

        # First, find the opening <text tag and everything up to its closing >
        text_open_match = re.search(r'<text\s+[^>]*>', svg_content)
        if not text_open_match:
            write_log("[ERROR] Could not find <text> opening tag")
            return None

        text_open_tag = text_open_match.group(0)
        text_start = text_open_match.end()

        # Find the closing </text>
        text_close_match = re.search(r'</text>', svg_content[text_start:])
        if not text_close_match:
            write_log("[ERROR] Could not find </text> closing tag")
            return None

        text_end = text_start + text_close_match.start()

        # Build the new SVG with simple tspan structure
        new_content = f'<tspan>{new_text_escaped}</tspan>'

        # Reconstruct the SVG
        updated_svg = (
            svg_content[:text_start] +
            new_content +
            svg_content[text_end:]
        )
        return updated_svg

    except Exception as e:
        write_log(f"[ERROR] Failed to update SVG text: {e}")
        import traceback
        write_log(traceback.format_exc())
        return None
