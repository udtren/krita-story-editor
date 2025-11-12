"""
Text Update Utilities
Handles updating existing texts and adding new texts to Krita
"""

import xml.etree.ElementTree as ET
import uuid
import html
from .svg_generator import (
    generate_full_svg_data,
    update_existing_svg_data_krita5_2,
    create_layer_groups,
    create_new_svg_data_krita5_2,
)
from .xml_formatter import remove_namespace_prefixes


def create_svg_data_for_doc(
    doc_name, doc_path, layer_groups, new_text_widgets, socket_handler, opened
):
    """
    Send update requests for all modified texts and add new texts

    Args:
        doc_name: Kritaドキュメント名
        text_edit_widgets: 既存テキスト更新と新規テキスト追加の両方を含むウィジェットのリスト
        socket_handler: Object with send_request and log methods
        opened: Boolean indicating if the document is opened
    """
    final_result = {
        "doc_name": doc_name,
        "doc_path": doc_path,
        "existing_texts_updated": [],
        "new_texts_added": [],
        "has_changes": False,
        "opened": opened,
    }

    # Process new text widgets
    for item in new_text_widgets:
        # Widget内のテキストを取得
        current_text = item["widget"].toPlainText()

        ##########################################
        ## レイヤ単位で処理を実施
        ##########################################
        # ダブル改行でテキストを分割, 各テキストは別々の<text>要素として追加される
        text_segments: list[str] = split_text_by_double_linebreak(current_text)

        if text_segments:  # Only add if we have segments
            # テンプレート選択
            template_text = ""
            template_combo = item.get("template_combo")
            if template_combo:
                template_path = template_combo.currentData()
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        template_text = f.read()
                except Exception as e:
                    socket_handler.log(
                        f"❌ Error loading template {template_path}: {e}"
                    )
                    continue
            else:
                socket_handler.log("⚠️ No template combo found, skipping")
                continue

            text_elements = []
            # Generate random UUID for shape ID
            shape_id_base = f"shape{uuid.uuid4().hex[:4]}_"

            # リスト型テキストセグメントごとにSVG要素を生成
            for index, segment in enumerate(text_segments):
                shape_id = f"{shape_id_base}{index}"

                # Escape special characters to prevent breaking SVG structure
                escaped_segment = escape_text_for_svg(segment)

                # Replace placeholders in template
                text_section_data = create_new_svg_data_krita5_2(
                    template_text, shape_id, escaped_segment
                )
                text_elements.append(text_section_data)

            # Generate full SVG data
            svg_data = generate_full_svg_data(text_elements)
            svg_data = remove_namespace_prefixes(svg_data)
            final_result["new_texts_added"].append({"svg_data": svg_data})
        ##########################################

    ####################################################
    # Process existing text widgets
    ####################################################
    # Process each layer group
    for layer_id, layer_data in layer_groups.items():
        layer_name = layer_data["layer_name"]
        svg_content = layer_data["svg_content"]
        layer_shapes = layer_data["layer_shapes"]
        changes = layer_data["changes"]

        valid_svg_data = update_existing_svg_data_krita5_2(
            svg_content, layer_shapes, changes
        )
        if valid_svg_data:
            final_result["existing_texts_updated"].append(
                {
                    "layer_name": layer_name,
                    "layer_id": layer_id,
                    "svg_data": valid_svg_data,
                }
            )

    ####################################################

    if (
        len(final_result["existing_texts_updated"]) == 0
        and len(final_result["new_texts_added"]) == 0
    ):
        # socket_handler.log("⚠️ No changes detected")
        return {"success": False, "error": "No changes detected"}
    else:
        final_result["has_changes"] = True
        return final_result


def split_text_by_double_linebreak(text):
    """
    Split text into a list by double linebreaks (two consecutive newlines)

    Args:
        text: The input text string

    Returns:
        List of text segments
    """
    segments = text.split("\n\n")
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
