from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
import xml.etree.ElementTree as ET
import re


class TextEditorWindow:
    """Handles the text editor window functionality"""

    def __init__(self, parent, socket_handler):
        """
        Initialize the text editor window handler

        Args:
            parent: The parent widget (main window)
            socket_handler: Object with send_request and log methods
        """
        self.parent = parent
        self.socket_handler = socket_handler
        self.svg_data = None
        self.text_editor_window = None
        self.text_edit_widgets = []  # Store references to text edit widgets with metadata

    def show_text_editor(self):
        """Show text editor window with SVG data from Krita document"""
        self.socket_handler.log("\n--- Opening Text Editor ---")

        # Clear any existing data
        self.svg_data = None

        # Request the SVG data (not text data)
        # The window will be created when set_svg_data() is called with the response
        self.socket_handler.send_request('get_all_svg_data')

    def set_svg_data(self, svg_data):
        """Store the received SVG data and create the editor window"""
        self.svg_data = svg_data
        # Automatically create the window when data is received
        self.create_text_editor_window()

    def extract_text_elements_from_svg(self, svg_content):
        """Extract all <text> elements from SVG content"""
        text_elements = []

        # Use regex to find all <text> elements
        pattern = r'<text[^>]*>.*?</text>'
        matches = re.findall(pattern, svg_content, re.DOTALL)

        for match in matches:
            # Extract just the text content for editing
            text_content = self.extract_text_content(match)
            text_elements.append({
                'raw_svg': match,
                'text_content': text_content
            })

        return text_elements

    def extract_text_content(self, text_element_svg):
        """Extract plain text content from a <text> SVG element"""
        try:
            # Parse the text element
            elem = ET.fromstring(text_element_svg)
            # Get all text content (including from tspan elements)
            text_content = ''.join(elem.itertext())
            return text_content
        except:
            # Fallback: use regex to strip tags
            text = re.sub(r'<[^>]+>', '', text_element_svg)
            return text.strip()

    def create_text_editor_window(self):
        """Create the text editor window with the received SVG data"""
        if not self.svg_data:
            self.socket_handler.log("⚠️ No SVG data available. Make sure the request succeeded.")
            return

        # Close existing window if it exists
        if self.text_editor_window:
            self.text_editor_window.close()

        # Clear previous widget references
        self.text_edit_widgets = []

        # Create new window
        self.text_editor_window = QWidget()
        self.text_editor_window.setWindowTitle("Text Editor (SVG-based)")
        self.text_editor_window.resize(800, 500)

        # Main layout
        main_layout = QVBoxLayout(self.text_editor_window)

        # Top bar with close and update buttons
        top_bar = QHBoxLayout()

        # Update button
        update_btn = QPushButton("Update Krita")
        update_btn.clicked.connect(self.update_all_texts)
        top_bar.addWidget(update_btn)

        top_bar.addStretch()

        # Close button
        close_btn = QPushButton("X")
        close_btn.setMaximumWidth(30)
        close_btn.setMaximumHeight(30)
        close_btn.clicked.connect(self.text_editor_window.close)
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)

        # VBoxLayout for all layers
        layers_layout = QVBoxLayout()

        # For each layer
        for layer_data in self.svg_data:
            layer_name = layer_data.get('layer_name', 'unknown')
            layer_id = layer_data.get('layer_id', 'unknown')
            svg_content = layer_data.get('svg', '')

            # Extract text elements from SVG
            text_elements = self.extract_text_elements_from_svg(svg_content)

            if not text_elements:
                continue

            # Layer label
            layer_label = QLabel(f"Layer: {layer_name}")
            layer_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
            layers_layout.addWidget(layer_label)

            # Add QTextEdit for each text element
            for elem_idx, text_elem in enumerate(text_elements):
                # Label for this text element
                elem_label = QLabel(f"  Text Element {elem_idx + 1}:")
                layers_layout.addWidget(elem_label)

                # QTextEdit for editing
                text_edit = QTextEdit()
                text_edit.setPlainText(text_elem['text_content'])
                text_edit.setMinimumHeight(80)
                layers_layout.addWidget(text_edit)

                # Store reference with metadata
                self.text_edit_widgets.append({
                    'widget': text_edit,
                    'layer_name': layer_name,
                    'layer_id': layer_id,
                    'shape_index': elem_idx,
                    'original_svg': text_elem['raw_svg'],
                    'original_text': text_elem['text_content']
                })

        main_layout.addLayout(layers_layout)
        main_layout.addStretch()

        # Show the window
        self.text_editor_window.show()
        total_texts = len(self.text_edit_widgets)
        self.socket_handler.log(f"✅ Text editor opened with {total_texts} text element(s) from {len(self.svg_data)} layer(s)")

    def update_all_texts(self):
        """Send update requests for all modified texts"""
        self.socket_handler.log("\n--- Updating texts in Krita ---")

        updates = []
        for item in self.text_edit_widgets:
            current_text = item['widget'].toPlainText()

            # Only update if text has changed
            if current_text != item['original_text']:
                updates.append({
                    'layer_name': item['layer_name'],
                    'layer_id': item['layer_id'],
                    'shape_index': item['shape_index'],
                    'new_text': current_text
                })

        if not updates:
            self.socket_handler.log("⚠️ No changes detected")
            return

        self.socket_handler.log(f"📝 Sending {len(updates)} text update(s)...")

        # Send update request
        self.socket_handler.send_request('update_layer_text', updates=updates)
