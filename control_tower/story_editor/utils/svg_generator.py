import xml.etree.ElementTree as ET
import uuid


def generate_full_svg_data(text_elements: list[str]) -> str:
    """
    The text_elements example:
    [
    "<text id="shape0" krita:textVersion="3" transform="translate(129.959999999996, 173.516874999995)" paint-order="stroke fill markers" fill="#000000" stroke-opacity="0" stroke="#000000" stroke-width="0" stroke-linecap="square" stroke-linejoin="bevel" style="inline-size: 262.799999999993;font-size: 12;white-space: pre-wrap;">Test Layer1

    Test Line1
    This layer has 2 shapes.</text>,
    "<text id="shape1" krita:textVersion="3" transform="translate(435.84, 296.396875)" paint-order="stroke fill markers" fill="#000000" stroke-opacity="0" stroke="#000000" stroke-width="0" stroke-linecap="square" stroke-linejoin="bevel" style="inline-size: 353.16;font-size: 22.99;white-space: pre-wrap;">Test Layer1/2

    This is the Second Shape.</text>"
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
