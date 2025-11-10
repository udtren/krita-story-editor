"""
Text Update Utilities
Handles updating existing texts and adding new texts to Krita
"""

import uuid
import html
from .svg_generator import generate_full_svg_data


def update_all_texts(doc_name, text_edit_widgets, socket_handler):
    """
    Send update requests for all modified texts and add new texts

    Args:
        doc_name: Kritaドキュメント名
        text_edit_widgets: 既存テキスト更新と新規テキスト追加の両方を含むウィジェットのリスト
        socket_handler: Object with send_request and log methods
    """
    socket_handler.log("\n--- Updating texts in Krita ---")

    response = []  # Final response list to hold all updates and new texts
    updates = []
    updates_with_doc_info = {
        'document_name': doc_name,
        'updates': updates
    }
    new_texts = []
    new_texts_with_doc_info = {
        'document_name': doc_name,
        'new_texts': new_texts
    }

    for item in text_edit_widgets:
        # Widget内のテキストを取得
        current_text = item['widget'].toPlainText()

        # ダブル改行でテキストを分割
        text_segments: list[str] = split_text_by_double_linebreak(current_text)

        # 新規テキスト追加の場合
        if item.get('is_new'):
            if text_segments:  # Only add if we have segments
                # テンプレート選択
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

                # リスト型テキストセグメントごとにSVG要素を生成
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
                    'svg_data': svg_data
                })
        else:
            # 既存テキスト - 変更があった場合のみ更新
            if current_text != item['original_text']:
                if text_segments:
                    # Escape special characters for existing text updates
                    escaped_segment = escape_text_for_svg(current_text)

                    updates.append({
                        'layer_name': item['layer_name'],
                        'layer_id': item['layer_id'],
                        'shape_index': item['shape_index'],
                        'new_text': escaped_segment
                    })

    '''
    既存テキスト更新と新規テキスト追加、もし両方がある場合は、同時にこの関数に渡されるため、
    戻り値は両者を結合したリストとして返す必要がある。
    '''
    if len(updates) > 0:
        response.append({
            "text_edit_type": "existing_texts_updated",
            "data": updates_with_doc_info
        })

    # Then, add new texts
    if len(new_texts) > 0:
        response.append({
            "text_edit_type": "new_texts_added",
            "data": new_texts_with_doc_info
        })

    if len(updates) == 0 and len(new_texts) == 0:
        socket_handler.log("⚠️ No changes detected")
        return {'success': False, 'error': 'No changes detected'}
    else:
        return {'success': True, 'requests': {
            'document_name': doc_name,
            'requests': response
        }}


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
