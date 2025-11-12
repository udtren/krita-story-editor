import xml.etree.ElementTree as ET
import re


def _add_missing_namespaces(svg_content):
    """
    Add missing namespace declarations to SVG content before parsing.
    This prevents 'unbound prefix' errors when SVG uses namespace prefixes
    without proper xmlns declarations.
    """
    # Check if svg_content already has the namespaces
    has_svg_ns = 'xmlns="http://www.w3.org/2000/svg"' in svg_content
    has_krita_ns = 'xmlns:krita="http://krita.org/namespaces/svg/krita"' in svg_content
    has_sodipodi_ns = 'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"' in svg_content

    # Find the opening <svg tag
    svg_tag_match = re.search(r'<svg\s+([^>]*?)>', svg_content)
    if not svg_tag_match:
        return svg_content

    # Build the new attributes
    new_attrs = []
    if not has_svg_ns:
        new_attrs.append('xmlns="http://www.w3.org/2000/svg"')
    if not has_krita_ns:
        new_attrs.append('xmlns:krita="http://krita.org/namespaces/svg/krita"')
    if not has_sodipodi_ns:
        new_attrs.append('xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"')

    if not new_attrs:
        return svg_content  # All namespaces already present

    # Get the existing attributes
    existing_attrs = svg_tag_match.group(1).strip()

    # Combine new and existing attributes
    all_attrs = ' '.join(new_attrs)
    if existing_attrs:
        all_attrs = all_attrs + ' ' + existing_attrs

    # Replace the svg tag
    new_svg_tag = f'<svg {all_attrs}>'
    new_svg_content = svg_content[:svg_tag_match.start()] + new_svg_tag + svg_content[svg_tag_match.end():]

    return new_svg_content


def parse_krita_svg(doc_name, doc_path, layer_id, svg_content):

    result = {
        "doc_name": doc_name,
        "doc_path": doc_path,
        "layer_id": layer_id,
        "layer_shapes": [],
    }

    # Add missing namespaces before parsing
    svg_content = _add_missing_namespaces(svg_content)

    root = ET.fromstring(svg_content)

    namespaces = {
        "svg": "http://www.w3.org/2000/svg",
        "krita": "http://krita.org/namespaces/svg/krita",
    }

    text_elements = root.findall(".//svg:text", namespaces)
    for text_elem in text_elements:
        element_id = text_elem.get("id")

        # Extract text from all tspan elements
        text_parts = []
        tspan_elements = text_elem.findall(".//svg:tspan", namespaces)
        if tspan_elements:
            for tspan in tspan_elements:
                if tspan.text:
                    text_parts.append(tspan.text)
        else:
            # Fallback to direct text content if no tspan elements
            if text_elem.text:
                text_parts.append(text_elem.text)

        text_content = "\n".join(text_parts)
        text_elem.text = f"{element_id}_TEXT_TO_REPLACE"

        result["layer_shapes"].append(
            {"element_id": element_id, "text_content": text_content}
        )

    return result


def extract_elements_from_svg(svg_content):
    # Add missing namespaces before parsing
    svg_content = _add_missing_namespaces(svg_content)

    root = ET.fromstring(svg_content)
    result = []

    # Define namespace map (important for finding elements with namespaces)
    namespaces = {
        "svg": "http://www.w3.org/2000/svg",
        "krita": "http://krita.org/namespaces/svg/krita",
    }
    text_elements = root.findall(".//svg:text", namespaces)

    for text_elem in text_elements:
        element_id = text_elem.get("id")

        # Extract text from all tspan elements
        text_parts = []
        tspan_elements = text_elem.findall(".//svg:tspan", namespaces)
        if tspan_elements:
            for tspan in tspan_elements:
                if tspan.text:
                    text_parts.append(tspan.text)
        else:
            # Fallback to direct text content if no tspan elements
            if text_elem.text:
                text_parts.append(text_elem.text)

        text_content = "\n".join(text_parts)

        result.append(
            {
                "raw_svg": svg_content,
                "element_id": element_id,
                "text_content": text_content,
            }
        )
    return result
