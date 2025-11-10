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


def update_existing_svg_data():
    pass
