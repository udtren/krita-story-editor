"""
Text Update Utilities
Handles updating existing texts and adding new texts to Krita
"""

import uuid
import html
from .svg_generator import generate_full_svg_data


def update_all_texts(text_edit_widgets, socket_handler):
    """
    Send update requests for all modified texts and add new texts

    Args:
        text_edit_widgets: List of dictionaries containing widget references and metadata
        socket_handler: Object with send_request and log methods
    """
    socket_handler.log("\n--- Updating texts in Krita ---")

    updates = []
    new_texts = []

    for item in text_edit_widgets:
        current_text = item['widget'].toPlainText()

        # Split by double linebreaks
        text_segments = split_text_by_double_linebreak(current_text)

        if item.get('is_new'):
            # This is a new text element
            if text_segments:  # Only add if we have segments
                # Get selected template from combo box
                template_combo = item.get('template_combo')
                if template_combo:
                    template_path = template_combo.currentData()
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_text = f.read()
                    except Exception as e:
                        socket_handler.log(
                            f"❌ Error loading template {template_path}: {e}")
                        continue
                else:
                    socket_handler.log(
                        "⚠️ No template combo found, skipping")
                    continue

                text_elements = []
                # Generate random UUID for shape ID
                shape_id_base = f"shape{uuid.uuid4().hex[:4]}"

                # Create a new text element for each segment
                for index, segment in enumerate(text_segments):
                    shape_id = f"{shape_id_base}_{index}"

                    # Escape special characters to prevent breaking SVG structure
                    escaped_segment = escape_text_for_svg(segment)

                    # Replace placeholders in template
                    text_section_data = template_text.replace(
                        'TEXT_TO_REPLACE', escaped_segment)
                    text_section_data = text_section_data.replace(
                        'SHAPE_ID', shape_id)
                    text_elements.append(text_section_data)

                # Generate full SVG data
                svg_data = generate_full_svg_data(text_elements)
                new_texts.append({
                    'svg_data': svg_data,
                    'text_content': segment
                })
        else:
            # Existing text - only update if changed
            if current_text != item['original_text']:
                if text_segments:
                    # Escape special characters for existing text updates
                    escaped_segment = escape_text_for_svg(current_text)

                    updates.append({
                        'document_name': item['document_name'],
                        'document_path': item['document_path'],
                        'layer_name': item['layer_name'],
                        'layer_id': item['layer_id'],
                        'shape_index': item['shape_index'],
                        'new_text': escaped_segment
                    })

    # First, update existing texts
    if updates:
        socket_handler.log(
            f"📝 Sending {len(updates)} text update(s)...")
        socket_handler.send_request(
            'update_layer_text', updates=updates)

    # Then, add new texts
    if new_texts:
        socket_handler.log(
            f"🆕 Adding {len(new_texts)} new text(s) to new layer(s)...")
        socket_handler.send_request(
            'add_text_to_new_layer', new_texts=new_texts)

    if not updates and not new_texts:
        socket_handler.log("⚠️ No changes detected")


def split_text_by_double_linebreak(text):
    """
    Split text into a list by double linebreaks (two consecutive newlines)

    Args:
        text: The input text string

    Returns:
        List of text segments
    """
    segments = text.split('\n\n')
    segments = [seg.strip() for seg in segments if seg.strip()]
    return segments


def escape_text_for_svg(text):
    """
    Escape special characters in text to prevent breaking SVG structure

    Args:
        text: The input text string

    Returns:
        Escaped text safe for SVG insertion
    """
    # Escape HTML/XML entities
    # This will convert: < to &lt;, > to &gt;, & to &amp;, " to &quot;, ' to &#x27;
    escaped_text = html.escape(text, quote=True)

    return escaped_text
