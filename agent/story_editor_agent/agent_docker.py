from krita import *
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtCore import QByteArray
import json
import xml.etree.ElementTree as ET
from .utils.logs import write_log
import zipfile
import os
import tempfile

class StoryEditorAgentDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor Agent")

        # Set up local server for communication
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.handle_connection)
        self.server.listen("krita_story_editor_bridge")
        
        self.clients = []
    
    def handle_connection(self):
        client = self.server.nextPendingConnection()
        client.readyRead.connect(lambda: self.handle_message(client))
        self.clients.append(client)
    
    def handle_message(self, client):
        data = client.readAll().data().decode('utf-8')
        request = json.loads(data)
        
        # Process request and interact with Krita
        if request['action'] == 'get_document_name':
            doc = Krita.instance().activeDocument()
            response = {'name': doc.name() if doc else None}
            client.write(json.dumps(response).encode('utf-8'))
        
        elif request['action'] == 'get_all_documents':
            documents = Krita.instance().documents()
            doc_info = []
            for doc in documents:
                info = {
                    'name': doc.name(),
                    'fileName': doc.fileName(),
                    'width': doc.width(),
                    'height': doc.height(),
                    'resolution': doc.resolution(),
                    'colorDepth': doc.colorDepth(),
                    'colorModel': doc.colorModel()
                }
                doc_info.append(info)
            response = {'documents': doc_info, 'count': len(doc_info)}
            client.write(json.dumps(response).encode('utf-8'))
        
        elif request['action'] == 'get_text_layers':
            doc = Krita.instance().activeDocument()
            if not doc:
                response = {'error': 'No active document', 'layers': []}
            else:
                text_layers = []
                self._find_text_layers(doc.rootNode(), text_layers)
                response = {'layers': text_layers, 'count': len(text_layers)}
            client.write(json.dumps(response).encode('utf-8'))
        
        elif request['action'] == 'get_layer_text':
            doc = Krita.instance().activeDocument()
            layer_name = request.get('layer_name')
            
            if not doc:
                response = {'success': False, 'error': 'No active document'}
            else:
                try:
                    # Get all text from vector layers
                    text_data = self._get_all_vector_text()
                    response = {'success': True, 'text_layers': text_data}
                except Exception as e:
                    response = {'success': False, 'error': str(e)}
            client.write(json.dumps(response).encode('utf-8'))

    def _find_text_layers(self, node, text_layers, path=""):
        """Recursively find all vector/text layers"""
        current_path = f"{path}/{node.name()}" if path else node.name()
        
        if node.type() == 'vectorlayer':
            text_layers.append({
                'name': node.name(),
                'path': current_path,
                'visible': node.visible(),
                'type': node.type()
            })
        
        # Recurse into child nodes
        for child in node.childNodes():
            self._find_text_layers(child, text_layers, current_path)
    
    def _get_all_vector_text(self):
        """Extract text content from all vector layers by reading from .kra zip file"""
        try:
            doc = Krita.instance().activeDocument()
            kra_path = doc.fileName()
            
            if not kra_path:
                write_log("[ERROR] Document not saved - cannot access .kra file")
                return []
            
            write_log(f"[DEBUG] KRA file path: {kra_path}")
            
            text_layers = []
            
            # Open the .kra file as a zip
            with zipfile.ZipFile(kra_path, 'r') as kra_zip:
                # List all files to find the layer's content.svg
                all_files = kra_zip.namelist()
                write_log(f"[DEBUG] Total files in .kra: {len(all_files)}")
                
                # Search for content.svg files
                for file_path in all_files:
                    if 'content.svg' in file_path and 'shapelayer' in file_path:
                        write_log(f"[DEBUG] Found potential SVG: {file_path}")
                        
                        # Extract layer folder name from path
                        # e.g., "krita_test/layers/layer4.shapelayer/content.svg"
                        parts = file_path.split('/')
                        layer_folder = parts[-2] if len(parts) >= 2 else 'unknown'
                        
                        # Read and extract text
                        svg_content = kra_zip.read(file_path).decode('utf-8')
                        text = self._extract_text_from_svg(svg_content)
                        
                        if text:
                            # Always use text_elements array format
                            if isinstance(text, list):
                                text_layers.append({
                                    'path': file_path,
                                    'layer_folder': layer_folder,
                                    'text_elements': text
                                })
                                write_log(f"[DEBUG] Found {len(text)} text elements in {file_path}")
                            else:
                                # Single element - still use array format
                                text_layers.append({
                                    'path': file_path,
                                    'layer_folder': layer_folder,
                                    'text_elements': [text]
                                })
                                write_log(f"[DEBUG] Found 1 text element in {file_path}")
                        else:
                            write_log(f"[DEBUG] No text in {file_path}")
                
                write_log(f"[DEBUG] Total text layers found: {len(text_layers)}")
                return text_layers
                
        except Exception as e:
            write_log(f"Error extracting vector text: {e}")
            import traceback
            write_log(traceback.format_exc())
            return []
    
    def _extract_text_from_svg(self, svg_content):
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
    
    def _update_vector_text(self, layer, new_text):
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

class StoryEditorAgentFactory(DockWidgetFactoryBase):

    def __init__(self):
        super().__init__("StoryEditorAgentDocker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        return StoryEditorAgentDocker()