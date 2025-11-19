import xml.etree.ElementTree as ET
import re
from .xml_formatter import remove_namespace_prefixes
from .svg_parser import _add_missing_namespaces


def create_new_svg_data(svg_template, shape_id, text_segment) -> str:
    """
    Create new SVG data from a template with shape_id and text replacement.
    Handles line breaks by creating multiple <tspan> elements with dy attribute.

    Args:
        svg_template: Template SVG string with SHAPE_ID and TEXT_TO_REPLACE placeholders
        shape_id: The ID to replace SHAPE_ID with
        text_segment: The text content to insert (may contain line breaks)

    Returns:
        Valid SVG data as a string
    """
    # First, replace SHAPE_ID in the template
    svg_content = svg_template.replace("SHAPE_ID", shape_id)

    # Escape the text for SVG
    escaped_text = escape_text_for_svg(text_segment)

    # Parse the template as XML
    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError:
        # If parsing fails, fall back to simple string replacement
        return svg_content.replace("TEXT_TO_REPLACE", escaped_text)

    root.text = escaped_text

    # Convert any tspan-like text back to actual tspan elements
    convert_text_tspans_to_elements(root)

    # Convert back to string
    svg_data = ET.tostring(root, encoding="unicode")
    svg_data = remove_namespace_prefixes(svg_data)

    return svg_data


def update_existing_svg_data(svg_content, layer_shapes, changes) -> str:
    """
    Update existing SVG data with new text content for Krita 5.3.
    Unlike Krita 5.2, Krita 5.3 does NOT use tspan tags. Text is set directly
    on the <text> element with white-space: pre-wrap to handle line breaks.

    :param svg_content: Original SVG content as a string.
    :param layer_shapes: List of original parsed text data for the layer.
    :param changes: List of changes containing new text from QTextEdit.
    :return: Updated SVG data string, or False if no changes.

    valid svg data example:
    <text id="shape0" krita:textVersion="3" transform="translate(53.4, 60.820625)"
    paint-order="stroke fill markers" fill="#000000" stroke="#000000"
    stroke-width="0" stroke-linecap="square" stroke-linejoin="bevel"
    style="inline-size: 152.76;text-align: left;
    text-align-last: auto;font-size: 12;white-space: pre-wrap;">Placeholder Text</text>
    """
    import xml.etree.ElementTree as ET

    has_changes = False

    svg_content = _add_missing_namespaces(svg_content)
    root = ET.fromstring(svg_content)
    namespaces = {
        "svg": "http://www.w3.org/2000/svg",
        "krita": "http://krita.org/namespaces/svg/krita",
    }

    # Create a mapping of shapeId to new text for quick lookup
    shape_id_to_new_text = {}
    for change in changes:
        shape_id = change["shape_id"]
        new_text_widget = change["new_text"]
        new_text = new_text_widget.toPlainText()
        shape_id_to_new_text[shape_id] = new_text

    # Create a mapping of shapeId to original text for comparison
    shape_id_to_original_text = {}
    for layer_shape in layer_shapes:
        shape_id = layer_shape["element_id"]
        original_text = layer_shape["text_content"]
        shape_id_to_original_text[shape_id] = original_text

    # Find all text elements in the SVG and update them if needed
    text_elements = root.findall(".//svg:text", namespaces)
    # Create a list to track elements to remove (can't modify list while iterating)
    elements_to_remove = []

    for text_elem in text_elements:
        element_id = text_elem.get("id")

        # print(f"each text_elem: {ET.tostring(text_elem, encoding='unicode')}")

        if element_id in shape_id_to_new_text:
            new_text = shape_id_to_new_text[element_id]
            original_text = shape_id_to_original_text.get(element_id, "")

            # print(f"new_text: {new_text}")
            # print(f"original: {original_text}")

            # Only update if text is different
            if new_text != original_text:
                has_changes = True

                # If new_text is empty, mark element for removal
                if new_text == "":
                    elements_to_remove.append(text_elem)
                    continue

                # Remove any existing child elements (like tspan) while preserving attributes
                for child in list(text_elem):
                    text_elem.remove(child)

                # Set the text content directly
                text_elem.text = new_text

                # print(f"text_elem: {text_elem.text}")

    # Remove text elements marked for deletion
    for text_elem in elements_to_remove:
        root.remove(text_elem)

    # Only add to updates if there were actual changes
    if has_changes:
        # print(f"original svg_content: {svg_content}")
        convert_text_tspans_to_elements(root)

        # Convert the modified XML tree back to string
        valid_svg_data = ET.tostring(root, encoding="unicode")
        # print(f"valid_svg_data after ET.tostring: {valid_svg_data}")

        valid_svg_data = remove_namespace_prefixes(valid_svg_data)
        # print(f"valid_svg_data after removing namespaces: {valid_svg_data}")

        return valid_svg_data
    else:
        return False


def convert_text_tspans_to_elements(element):
    """Convert tspan tags stored as text into actual XML elements."""
    if element.text and "<tspan" in element.text:
        # Parse tspan tags from text
        tspan_pattern = r"<tspan[^>]*>.*?</tspan>"
        text = element.text

        # Clear the original text
        element.text = None

        # Parse and convert to actual elements
        parts = re.split(r"(<tspan[^>]*>.*?</tspan>)", text)

        prev_elem = element
        for part in parts:
            if part.startswith("<tspan"):
                # Parse as XML element
                try:
                    tspan = ET.fromstring(part)
                    element.append(tspan)
                    prev_elem = tspan
                except:
                    # If parsing fails, keep as text
                    if prev_elem == element:
                        element.text = (element.text or "") + part
                    else:
                        prev_elem.tail = (prev_elem.tail or "") + part
            elif part:
                # Regular text
                if prev_elem == element:
                    element.text = (element.text or "") + part
                else:
                    prev_elem.tail = (prev_elem.tail or "") + part

    # Recursively process children
    for child in element:
        convert_text_tspans_to_elements(child)


def generate_full_svg_data(text_elements: list[str], svg_placeholder) -> str:
    """
    The text_elements example:
    [
    "<text with parameter>My Text1</text>",
    "<text with parameter>My Text2</text>"
    ]

    """

    full_text_content = ""

    for text_elem in text_elements:
        full_text_content += text_elem + "\n"
    full_svg_content = svg_placeholder.replace("TEXT_TAG_TO_REPLACE", full_text_content)

    # print(f"full_svg_content: {full_svg_content}")

    return full_svg_content


def extract_font_size(text_elem):
    """
    Extract font-size from a text element's style attribute.

    Args:
        text_elem: An XML text element

    Returns:
        Font size as a string with 'pt' suffix (e.g., '12pt'), or None if not found
    """
    import re

    style = text_elem.get("style", "")

    # Look for font-size in the style attribute
    # Match patterns like "font-size:12" or "font-size:12pt"
    match = re.search(r"font-size:\s*(\d+(?:\.\d+)?)(pt)?", style)

    if match:
        font_size_value = match.group(1)
        # If 'pt' suffix is already present, use it; otherwise add it
        if match.group(2):
            return f"{font_size_value}pt"
        else:
            return f"{font_size_value}pt"

    return None


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
    import html

    escaped_text = html.escape(text, quote=True)

    return escaped_text
