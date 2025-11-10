from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QComboBox
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QByteArray
import xml.etree.ElementTree as ET
import re
import uuid
import os
import glob
from configs.story_editor import (
    get_text_editor_font,
    get_tspan_editor_stylesheet,
    get_layer_header_stylesheet,
    TEXT_EDITOR_MIN_HEIGHT,
    TEXT_EDITOR_MAX_HEIGHT
)
from story_editor.utils.text_updater import update_all_texts


class StoryEditorWindow:
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
            self.socket_handler.log(
                "⚠️ No SVG data available. Make sure the request succeeded.")
            return

        # Close existing window if it exists
        if self.text_editor_window:
            self.text_editor_window.close()

        # Clear previous widget references
        self.text_edit_widgets = []

        # Create new window
        self.text_editor_window = QWidget()
        self.text_editor_window.setWindowTitle("Story Editor")
        self.text_editor_window.resize(800, 1200)

        # Main layout
        main_layout = QVBoxLayout(self.text_editor_window)

        # Top bar with close and update buttons
        top_bar = QHBoxLayout()

        # New Text button
        new_text_btn = QPushButton("New Text")
        new_text_btn.clicked.connect(self.add_new_text_widget)
        top_bar.addWidget(new_text_btn)

        # Update button
        update_btn = QPushButton("Update Krita")
        update_btn.clicked.connect(self.update_all_texts)
        top_bar.addWidget(update_btn)

        top_bar.addStretch()

        main_layout.addLayout(top_bar)

        # VBoxLayout for all layers
        self.doc_level_layers_layout = QVBoxLayout()

        # For each layer
        for layer_data in self.svg_data:
            document_name = layer_data.get('document_name', 'unknown')
            document_path = layer_data.get('document_path', 'unknown')
            layer_name = layer_data.get('layer_name', 'unknown')
            layer_id = layer_data.get('layer_id', 'unknown')
            svg_content = layer_data.get('svg', '')

            # Extract text elements from SVG
            text_elements = self.extract_text_elements_from_svg(svg_content)

            if not text_elements:
                continue

            # Add QTextEdit for each text element
            for elem_idx, text_elem in enumerate(text_elements):
                svg_section_level_layout = QHBoxLayout()
                # QTextEdit for editing
                text_edit = QTextEdit()
                text_edit.setPlainText(text_elem['text_content'])
                text_edit.setAcceptRichText(False)
                text_edit.setFont(get_text_editor_font())
                text_edit.setStyleSheet(get_tspan_editor_stylesheet())
                text_edit.setMaximumHeight(TEXT_EDITOR_MAX_HEIGHT)

                # Auto-adjust height based on content
                doc_height = text_edit.document().size().height()
                text_edit.setMinimumHeight(
                    min(max(int(doc_height) + 10, TEXT_EDITOR_MIN_HEIGHT), TEXT_EDITOR_MAX_HEIGHT))

                svg_section_level_layout.addWidget(text_edit)

                # Store reference with metadata
                self.text_edit_widgets.append({
                    'widget': text_edit,
                    'document_name': document_name,
                    'document_path': document_path,
                    'layer_name': layer_name,
                    'layer_id': layer_id,
                    'shape_index': elem_idx,
                    'original_svg': text_elem['raw_svg'],
                    'original_text': text_elem['text_content']
                })

                self.doc_level_layers_layout.addLayout(
                    svg_section_level_layout)

        main_layout.addLayout(self.doc_level_layers_layout)
        main_layout.addStretch()

        # Show the window
        self.text_editor_window.show()
        total_texts = len(self.text_edit_widgets)
        self.socket_handler.log(
            f"✅ Text editor opened with {total_texts} text element(s) from {len(self.svg_data)} layer(s)")

    def add_new_text_widget(self):
        """Add a new empty text editor widget for creating new text"""
        # Default template path
        default_template = 'svg_templates/default_1.xml'
        placeholder_text = '''Enter new text here.


If you want multiple paragraphs within different text elements, separate them with double line breaks.'''

        # Create new layout for this text element
        svg_section_level_layout = QHBoxLayout()

        # Create the text editor
        text_edit = QTextEdit()
        text_edit.setPlainText("")
        text_edit.setPlaceholderText(placeholder_text)
        text_edit.setAcceptRichText(False)
        text_edit.setFont(get_text_editor_font())
        text_edit.setStyleSheet(get_tspan_editor_stylesheet())
        text_edit.setMaximumHeight(TEXT_EDITOR_MAX_HEIGHT)
        text_edit.setMinimumHeight(TEXT_EDITOR_MIN_HEIGHT)

        svg_section_level_layout.addWidget(text_edit)

        # Create template selector combo box
        choose_template_combo = QComboBox()
        choose_template_combo.setMinimumWidth(200)
        choose_template_combo.setMaximumWidth(400)

        # Find all XML files in svg_templates directory
        template_dir = 'svg_templates'
        template_files = []

        if os.path.exists(template_dir):
            # Get all .xml files
            xml_files = glob.glob(os.path.join(template_dir, '*.xml'))
            for xml_file in sorted(xml_files):
                # Get just the filename without path
                filename = os.path.basename(xml_file)
                template_files.append((filename, xml_file))
                choose_template_combo.addItem(filename, xml_file)

        if not template_files:
            self.socket_handler.log(
                f"⚠️ No template files found in {template_dir}")
            # Add default as fallback
            choose_template_combo.addItem("default_1.xml", default_template)

        # Set default selection
        default_index = choose_template_combo.findText("default_1.xml")
        if default_index >= 0:
            choose_template_combo.setCurrentIndex(default_index)

        svg_section_level_layout.addWidget(choose_template_combo)

        # Add to layout
        self.doc_level_layers_layout.addLayout(svg_section_level_layout)

        # Store reference with metadata marking it as new
        self.text_edit_widgets.append({
            'widget': text_edit,
            'is_new': True,  # Flag to identify new text
            'template_combo': choose_template_combo,  # Store reference to combo box
            'original_text': ''
        })

        self.socket_handler.log(
            f"✅ Added new text widget with {choose_template_combo.count()} template(s)")

    def update_all_texts(self):
        """Send update requests for all modified texts and add new texts"""
        update_all_texts(self.text_edit_widgets, self.socket_handler)
