import xml.etree.ElementTree as ET


def parse_krita_svg(doc_name, doc_path, layer_id, svg_content):

    result = {
        'doc_name': doc_name,
        'doc_path': doc_path,
        layer_id: {}
    }

    root = ET.fromstring(svg_content)

    namespaces = {
        'svg': 'http://www.w3.org/2000/svg',
        'krita': 'http://krita.org/namespaces/svg/krita'
    }

    text_elements = root.findall('.//svg:text', namespaces)
    for text_elem in text_elements:
        element_id = text_elem.get('id')
        text_content = text_elem.text or ''
        result[layer_id][element_id] = text_content

    return result
