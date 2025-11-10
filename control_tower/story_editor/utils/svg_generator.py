import xml.etree.ElementTree as ET
import uuid


def generate_full_svg_data(text_elements: list[str]) -> str:
    """
    The text_elements example:
    [
    "<text with parameter>My Text1</text>",
    "<text with parameter>My Text2</text>"
    ]

    """

    svg_start_template = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:krita="http://krita.org/namespaces/svg/krita" xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" width="864pt" height="1368pt" viewBox="0 0 864 1368">'''
    svg_closing_tag = '</svg>'

    # Combine all text elements into the SVG structure
    full_svg_content = svg_start_template + '\n'
    for text_elem in text_elements:
        full_svg_content += text_elem + '\n'
    full_svg_content += svg_closing_tag

    return full_svg_content


def create_layer_groups(updates: list[dict]) -> dict:
    '''
    new_layer_shapes example:
    [
        'layer_name': item['layer_name'],
        'layer_id': item['layer_id'],
        'shape_id': item['shape_id'],
        'new_text': escaped_segment,
        'remove_shape': False,
    ]
    '''
    layer_groups = {}

    for update in updates:
        layer_id = update['layer_id']
        if layer_id not in layer_groups:
            layer_groups[layer_id] = {
                'layer_name': update['layer_name'],
                'layer_id': layer_id,
                'shapes': []
            }
        layer_groups[layer_id]['shapes'].append({
            'shape_id': update['shape_id'],
            'new_text': update['new_text'],
            'remove_shape': update['remove_shape'],

        })

    return layer_groups

    # Now layer_groups is a dict where each value contains all shapes for that layer
    # Example: layer_groups = {
    #     'layer_id_1': {'layer_name': 'Layer 1', 'layer_id': 'layer_id_1', 'shapes': [...]},
    #     'layer_id_2': {'layer_name': 'Layer 2', 'layer_id': 'layer_id_2', 'shapes': [...]}
    # }
