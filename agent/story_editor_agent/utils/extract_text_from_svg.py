import xml.etree.ElementTree as ET
from ..utils.logs import write_log


def extract_text_from_svg(svg_content):
    """Extract text from SVG content string"""
    try:
        write_log(f"[DEBUG] SVG Content length: {len(svg_content)}")
        write_log(f"[DEBUG] First 1000 chars: {svg_content[:1000]}")

        # Parse SVG
        root = ET.fromstring(svg_content)
        write_log(f"[DEBUG] Root tag: {root.tag}")

        # Collect text elements with their HTML
        text_elements = []

        # Search for text elements (with namespace)
        for elem in root.iter():
            tag_lower = elem.tag.lower()
            if 'text' in tag_lower and elem.tag.endswith('text'):
                # This is a <text> element, not a <textPath> or similar
                write_log(f"[DEBUG] Found text element with tag: {elem.tag}")

                # Get the text content
                elem_text = ''.join(elem.itertext()).strip()

                if elem_text:
                    # Convert element to HTML string (outer HTML)
                    outer_html = ET.tostring(elem, encoding='unicode', method='xml')

                    text_elements.append({
                        'text': elem_text,
                        'html': outer_html
                    })
                    write_log(f"[DEBUG] Extracted text element #{len(text_elements)}")
                    write_log(f"[DEBUG] Text: '{elem_text}'")
                    write_log(f"[DEBUG] HTML: {outer_html[:200]}...")

        write_log(f"[DEBUG] Total text elements found: {len(text_elements)}")

        # Return as list if multiple elements, single object if one, empty string if none
        if len(text_elements) > 1:
            write_log(f"[DEBUG] Returning {len(text_elements)} separate text elements")
            return text_elements
        elif len(text_elements) == 1:
            return text_elements[0]
        else:
            return ''

    except Exception as e:
        write_log(f"Error parsing SVG: {e}")
        import traceback
        write_log(traceback.format_exc())
        return ''
