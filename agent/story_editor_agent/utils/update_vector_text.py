import xml.etree.ElementTree as ET
from ..utils.logs import write_log


def update_vector_text(layer, new_text):
    """Update text content in a vector layer"""
    try:
        # Get SVG content using the correct Krita API
        svg_content = layer.shapesAsXml()

        # Parse SVG
        root = ET.fromstring(svg_content)

        # Define SVG namespace
        ns = {'svg': 'http://www.w3.org/2000/svg'}

        # Find and update text elements
        text_found = False

        # Try with namespace
        for text_elem in root.findall('.//{http://www.w3.org/2000/svg}text'):
            # Update direct text content
            if text_elem.text:
                text_elem.text = new_text
                text_found = True

            # Also check tspan elements (Krita often uses these)
            for tspan in text_elem.findall('.//{http://www.w3.org/2000/svg}tspan'):
                if tspan.text:
                    tspan.text = new_text
                    text_found = True

        if not text_found:
            return False

        # Convert back to string
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        modified_svg = ET.tostring(root, encoding='unicode')

        # Update layer using the correct Krita API
        layer.setShapesFromXml(modified_svg)
        return True

    except Exception as e:
        write_log(f"Error updating vector text: {e}")
        import traceback
        write_log(traceback.format_exc())
        return False
