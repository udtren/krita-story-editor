import xml.etree.ElementTree as ET


def parse_krita_svg(doc_name, doc_path, layer_id, svg_content):

    result = {
        'doc_name': doc_name,
        'doc_path': doc_path,
        'layer_id': layer_id,
        'layer_shapes': [],
        'merged_text_elem_for_replace': ""
    }

    root = ET.fromstring(svg_content)

    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
        'krita': 'http://krita.org/namespaces/svg/krita'
    }
    merged_text_elem_for_replace = ""

    text_elements = root.findall('.//svg:text', namespaces)
    for text_elem in text_elements:
        element_id = text_elem.get('id')

        # Extract text from all tspan elements
        text_parts = []
        tspan_elements = text_elem.findall('.//svg:tspan', namespaces)
        if tspan_elements:
            for tspan in tspan_elements:
                if tspan.text:
                    text_parts.append(tspan.text)
        else:
            # Fallback to direct text content if no tspan elements
            if text_elem.text:
                text_parts.append(text_elem.text)

        text_content = '\n'.join(text_parts)
        text_elem.text = f"{element_id}_TEXT_TO_REPLACE"

        result['layer_shapes'].append({
            'element_id': element_id,
            'text_content': text_content
        })

        merged_text_elem_for_replace += ET.tostring(
            text_elem, encoding='unicode') + '\n'

    result['merged_text_elem_for_replace'] = merged_text_elem_for_replace

    return result


def extract_elements_from_svg(svg_content):
    root = ET.fromstring(svg_content)
    result = []

    # Define namespace map (important for finding elements with namespaces)
    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
        'krita': 'http://krita.org/namespaces/svg/krita'
    }
    text_elements = root.findall('.//svg:text', namespaces)

    for text_elem in text_elements:
        element_id = text_elem.get('id')

        # Extract text from all tspan elements
        text_parts = []
        tspan_elements = text_elem.findall('.//svg:tspan', namespaces)
        if tspan_elements:
            for tspan in tspan_elements:
                if tspan.text:
                    text_parts.append(tspan.text)
        else:
            # Fallback to direct text content if no tspan elements
            if text_elem.text:
                text_parts.append(text_elem.text)

        text_content = '\n'.join(text_parts)

        result.append({
            'raw_svg': svg_content,
            'element_id': element_id,
            'text_content': text_content
        })
    return result
