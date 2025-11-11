from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QComboBox, QToolBar, QAction)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QByteArray, QTimer, QSize
from PyQt5.QtGui import QIcon
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
    TEXT_EDITOR_MAX_HEIGHT,
    STORY_EDITOR_WINDOW_WIDTH,
    STORY_EDITOR_WINDOW_HEIGHT
)
from story_editor.utils.text_updater import create_svg_data_for_doc
from story_editor.utils.svg_parser import parse_krita_svg, extract_elements_from_svg


class StoryEditorWindow:
    """Handles the text editor window functionality"""

    def __init__(self, parent, socket_handler):
        """
        Initialize the text editor window handler

        Args:
            parent: The parent widget (main window)
            socket_handler: Object with send_request and log methods

        get_all_svg_data response data structure:
        [
            {
                'document_name': 'Example.kra',
                'document_path': '/path/to/Example.kra',
                'svg_data': [{
                        'layer_name': 'Layer 1',
                        'layer_id': '...',
                        'svg': '<svg>...</svg>'}
                        , ...]
            },
            ...
        ]
        """
        self.parent = parent
        self.socket_handler = socket_handler
        self.all_docs_svg_data = None
        self.text_editor_window = None
        self.text_edit_widgets = []  # Store references to text edit widgets with metadata
        self.doc_layouts = {}  # Store document layouts {doc_name: layout}
        self.active_doc_name = None  # Track which document is active for new text

    def create_text_editor_window(self):
        """Create the text editor window with the received SVG data"""
        if not self.all_docs_svg_data:
            self.socket_handler.log(
                "⚠️ No SVG data available. Make sure the request succeeded.")
            return

        # Store current window position and size if window exists
        window_geometry = None
        if self.text_editor_window:
            window_geometry = self.text_editor_window.geometry()
            self.text_editor_window.close()

        # Clear previous widget references
            '''all_docs_text_state data structure:
        all_docs_text_state[document_name] = {
                        'document_name': 'Example.kra',
                        'document_path': '/path/to/Example.kra',
                        'has_text_changes':False,
                        'text_edit_widgets':[]
                        }
        '''
        self.all_docs_text_state = {}
        self.text_edit_widgets = []
        self.doc_layouts = {}
        self.active_doc_name = None

        # Create new window
        self.text_editor_window = QWidget()
        self.text_editor_window.setWindowTitle("Story Editor")

        # Restore previous geometry or use default size
        if window_geometry:
            self.text_editor_window.setGeometry(window_geometry)
        else:
            self.text_editor_window.resize(
                STORY_EDITOR_WINDOW_WIDTH, STORY_EDITOR_WINDOW_HEIGHT)

        # Main layout
        main_layout = QVBoxLayout(self.text_editor_window)

        #################################
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #E0E0E0;
                border: none;
                padding: 4px;
            }
        """)
        main_layout.addWidget(toolbar)

        # Get absolute path to icon
        icon_path_bath = os.path.join(
            os.path.dirname(__file__), "icons")

        new_text_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'plus.png')}"), "Add New Text", self.text_editor_window)
        new_text_btn.setStatusTip("Add a new text widget")
        new_text_btn.triggered.connect(self.add_new_text_widget)
        new_text_btn.setCheckable(True)
        toolbar.addAction(new_text_btn)

        refresh_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'refresh.png')}"), "Refresh from Krita", self.text_editor_window)
        refresh_btn.setStatusTip("Reload text data from Krita document")
        refresh_btn.triggered.connect(self.refresh_data)
        refresh_btn.setCheckable(True)
        toolbar.addAction(refresh_btn)

        update_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'check.png')}"), "Update Krita", self.text_editor_window)
        update_btn.setStatusTip("Update Krita")
        update_btn.triggered.connect(self.send_merged_svg_request)
        update_btn.setCheckable(True)
        toolbar.addAction(update_btn)

        #################################

        # VBoxLayout for all layers
        for doc_data in self.all_docs_svg_data:
            doc_name = doc_data.get('document_name', 'unknown')
            doc_path = doc_data.get('document_path', 'unknown')
            self.svg_data = doc_data.get('svg_data', [])
            opened = doc_data.get('opened', True)

            self.all_docs_text_state[doc_name] = {
                'document_name': doc_name,
                'document_path': doc_path,
                'has_text_changes': False,
                'text_edit_widgets': [],
                'opened': opened
            }

            # Document header with clickable button to activate
            doc_header_layout = QHBoxLayout()

            # Activate button for this document
            activate_btn = QPushButton(f"📄 {doc_name}")
            activate_btn.setCheckable(True)
            activate_btn.setToolTip(
                f"Click to activate this document for adding new text\nPath: {doc_path}")
            activate_btn.clicked.connect(
                lambda checked, name=doc_name, btn=activate_btn: self.activate_document(name, btn))
            activate_btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #4A9EFF;
                    color: white;
                }
            """)
            doc_header_layout.addWidget(activate_btn)
            doc_header_layout.addStretch()
            main_layout.addLayout(doc_header_layout)

            # Store button reference for later activation
            if not hasattr(self, 'doc_buttons'):
                self.doc_buttons = {}
            self.doc_buttons[doc_name] = activate_btn

            # each document has its own QVBoxLayout
            doc_level_layers_layout = QVBoxLayout()

            # Store the layout for this document
            self.doc_layouts[doc_name] = doc_level_layers_layout

            # Set first document as active by default
            if self.active_doc_name is None:
                self.active_doc_name = doc_name
                activate_btn.setChecked(True)

            # For each layer
            for layer_data in self.svg_data:
                layer_name = layer_data.get('layer_name', 'unknown')
                layer_id = layer_data.get('layer_id', 'unknown')
                svg_content = layer_data.get('svg', '')

                parsed_svg_data = parse_krita_svg(
                    doc_name, doc_path, layer_id, svg_content)

                if not parsed_svg_data['layer_shapes']:
                    continue

                # Add QTextEdit for each text element
                for elem_idx, layer_shape in enumerate(parsed_svg_data['layer_shapes']):
                    svg_section_level_layout = QHBoxLayout()
                    # QTextEdit for editing
                    text_edit = QTextEdit()
                    text_edit.setPlainText(layer_shape['text_content'])
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
                    self.all_docs_text_state[doc_name]['text_edit_widgets'].append({
                        'widget': text_edit,
                        'document_name': doc_name,
                        'document_path': doc_path,
                        'layer_name': layer_name,
                        'layer_id': layer_id,
                        'shape_id': layer_shape['element_id'],
                        'original_text': layer_shape['text_content'],

                    })

                    #################################################
                    # Add metadata label
                    #################################################
                    metadata_label = QLabel(
                        f"Layer: {layer_name} | Layer Id: {layer_id} | Shape ID: {layer_shape['element_id']}")
                    metadata_label.setStyleSheet(
                        "color: gray; font-size: 10pt;")
                    metadata_label.setMaximumWidth(100)
                    metadata_label.setWordWrap(True)
                    svg_section_level_layout.addWidget(metadata_label)

                    #################################################

                    doc_level_layers_layout.addLayout(
                        svg_section_level_layout)

            # Add each document layout to main layout (AFTER all layers processed)
            main_layout.addLayout(doc_level_layers_layout)

        main_layout.addStretch()

        # Show the window
        self.text_editor_window.show()

    def activate_document(self, doc_name, clicked_btn):
        """Activate a document for adding new text"""
        # Uncheck all other buttons
        if hasattr(self, 'doc_buttons'):
            for name, btn in self.doc_buttons.items():
                if name != doc_name:
                    btn.setChecked(False)

        # Set active document
        self.active_doc_name = doc_name
        # self.socket_handler.log(f"📄 Activated document: {doc_name}")

    def add_new_text_widget(self):
        """Add a new empty text editor widget for creating new text"""
        # Check if a document is active
        if not self.active_doc_name or self.active_doc_name not in self.doc_layouts:
            self.socket_handler.log(
                "⚠️ No active document. Please click on a document name to activate it first.")
            return

        # Get the active document's layout
        active_layout = self.doc_layouts[self.active_doc_name]

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

        # Add to the ACTIVE document's layout
        active_layout.addLayout(svg_section_level_layout)

        # Store reference with metadata marking it as new
        self.all_docs_text_state[self.active_doc_name]['text_edit_widgets'].append({
            'widget': text_edit,
            'is_new': True,  # Flag to identify new text
            'document_name': self.active_doc_name,  # Store which document this belongs to
            'template_combo': choose_template_combo,  # Store reference to combo box
            'original_text': ''
        })

        self.socket_handler.log(
            f"✅ Added new text widget to '{self.active_doc_name}' document.")

    def refresh_data(self):
        """Refresh the editor window with latest data from Krita"""
        self.socket_handler.log("🔄 Refreshing data from Krita")
        # Simply request new data, which will rebuild the window
        self.show_text_editor()

    def send_merged_svg_request(self):
        """Send update requests for all modified texts and add new texts"""

        merged_requests = []

        for doc_name, doc_state in self.all_docs_text_state.items():
            self.socket_handler.log(
                f"⏳ Creating update data for document: {doc_name}")

            result = create_svg_data_for_doc(
                doc_name=doc_name,
                text_edit_widgets=doc_state['text_edit_widgets'],
                socket_handler=self.socket_handler,
                opened=doc_state.get('opened')
            )
            if result.get('success'):
                merged_requests.append(result.get('requests'))
                self.socket_handler.log(
                    f"✅ Update data for document: {doc_name} added to the merged requests")

        if len(merged_requests) > 0:
            self.socket_handler.log(
                f"--- {len(merged_requests)} documents to update ---")
            self.socket_handler.send_request(
                'docs_svg_update', merged_requests=merged_requests, krita_files_folder=self.parent.krita_files_folder if hasattr(self.parent, 'krita_files_folder') else None)
        else:
            self.socket_handler.log("⚠️ No updates or new texts to send.")

    def show_text_editor(self):
        """Show text editor window with SVG data from Krita document"""
        # self.socket_handler.log("--- Opening Story Editor ---")

        # Clear any existing data
        self.all_docs_svg_data = None

        # Set the waiting flag on the parent (main window)
        if hasattr(self.parent, '_waiting_for_svg'):
            self.parent._waiting_for_svg = 'text_editor'

        # Get krita folder path if available
        krita_folder_path = None
        if hasattr(self.parent, 'krita_files_folder'):
            krita_folder_path = self.parent.krita_files_folder

        # Request the SVG data
        # The window will be created when set_svg_data() is called with the response
        if krita_folder_path:
            self.socket_handler.send_request(
                'get_all_docs_svg_data', folder_path=krita_folder_path)
        else:
            self.socket_handler.send_request('get_all_docs_svg_data')

    def set_svg_data(self, all_docs_svg_data):
        """Store the received SVG data and create the editor window"""
        self.all_docs_svg_data = all_docs_svg_data
        # Automatically create the window when data is received
        self.create_text_editor_window()
