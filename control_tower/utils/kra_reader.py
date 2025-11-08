"""
Utility to read text from .kra files without Krita running
"""
import zipfile
import xml.etree.ElementTree as ET


def extract_text_from_kra(kra_path):
    """
    Extract all text from vector layers in a .kra file
    
    Args:
        kra_path: Path to the .kra file
        
    Returns:
        List of dictionaries with text layer information
    """
    text_layers = []
    
    try:
        # Open the .kra file as a zip
        with zipfile.ZipFile(kra_path, 'r') as kra_zip:
            all_files = kra_zip.namelist()
            
            # Search for content.svg files
            for file_path in all_files:
                if 'content.svg' in file_path and 'shapelayer' in file_path:
                    # Extract layer folder name from path
                    parts = file_path.split('/')
                    layer_folder = parts[-2] if len(parts) >= 2 else 'unknown'
                    
                    # Read and extract text
                    svg_content = kra_zip.read(file_path).decode('utf-8')
                    text_elements = _extract_text_from_svg(svg_content)
                    
                    if text_elements:
                        text_layers.append({
                            'path': file_path,
                            'layer_folder': layer_folder,
                            'text_elements': text_elements
                        })
            
            return text_layers
            
    except Exception as e:
        raise Exception(f"Error reading .kra file: {e}")


def _extract_text_from_svg(svg_content):
    """Extract text elements from SVG content string"""
    try:
        # Parse SVG
        root = ET.fromstring(svg_content)
        
        # Collect text elements with their HTML
        text_elements = []
        
        # Search for text elements
        for elem in root.iter():
            tag_lower = elem.tag.lower()
            if 'text' in tag_lower and elem.tag.endswith('text'):
                # Get the text content
                elem_text = ''.join(elem.itertext()).strip()
                
                if elem_text:
                    # Convert element to HTML string (outer HTML)
                    outer_html = ET.tostring(elem, encoding='unicode', method='xml')
                    
                    text_elements.append({
                        'text': elem_text,
                        'html': outer_html
                    })
        
        return text_elements
        
    except Exception as e:
        raise Exception(f"Error parsing SVG: {e}")
