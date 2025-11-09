from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PyQt5.QtCore import QTimer


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
        self.text_data = None
        self.text_editor_window = None
        self.text_edit_widgets = []  # Store references to text edit widgets with metadata

    def show_text_editor(self):
        """Show text editor window with text from Krita document"""
        self.socket_handler.log("\n--- Opening Text Editor ---")

        # First, request the text data
        self.socket_handler.send_request('get_layer_text')

        # Wait a bit for response, then create the window
        QTimer.singleShot(500, self.create_text_editor_window)

    def set_text_data(self, text_data):
        """Store the received text data"""
        self.text_data = text_data

    def create_text_editor_window(self):
        """Create the text editor window with the received text data"""
        if not self.text_data:
            self.socket_handler.log("⚠️ No text data available. Make sure the request succeeded.")
            return

        # Close existing window if it exists
        if self.text_editor_window:
            self.text_editor_window.close()

        # Clear previous widget references
        self.text_edit_widgets = []

        # Create new window
        self.text_editor_window = QWidget()
        self.text_editor_window.setWindowTitle("Text Editor")
        self.text_editor_window.resize(600, 400)

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

        # VBoxLayout_1 for all documents
        documents_layout = QVBoxLayout()

        # For each text layer (treating each as a document for this test)
        for layer_idx, layer in enumerate(self.text_data):
            # VBoxLayout_2 for each document
            doc_layout = QVBoxLayout()

            # Add label for layer info
            layer_path = layer.get('path', 'unknown')
            layer_label = QLabel(f"Layer: {layer.get('layer_folder', 'unknown')} ({layer_path})")
            doc_layout.addWidget(layer_label)

            # Get text elements
            text_elements = layer.get('text_elements', [])

            # Add QTextEdit for each text element
            for elem_idx, text_elem in enumerate(text_elements):
                text_edit = QTextEdit()

                # Extract the text content and HTML
                if isinstance(text_elem, dict):
                    text_content = text_elem.get('text', '')
                    original_html = text_elem.get('html', '')
                else:
                    text_content = str(text_elem)
                    original_html = ''

                text_edit.setPlainText(text_content)
                text_edit.setMinimumHeight(100)
                doc_layout.addWidget(text_edit)

                # Store reference with metadata
                self.text_edit_widgets.append({
                    'widget': text_edit,
                    'layer_path': layer_path,
                    'layer_folder': layer.get('layer_folder', 'unknown'),
                    'element_index': elem_idx,
                    'original_text': text_content,
                    'original_html': original_html
                })

            documents_layout.addLayout(doc_layout)

        main_layout.addLayout(documents_layout)

        # Show the window
        self.text_editor_window.show()
        self.socket_handler.log(f"✅ Text editor opened with {len(self.text_data)} text layer(s)")

    def update_all_texts(self):
        """Send update requests for all modified texts"""
        self.socket_handler.log("\n--- Updating texts in Krita ---")

        updates = []
        for item in self.text_edit_widgets:
            current_text = item['widget'].toPlainText()

            # Only update if text has changed
            if current_text != item['original_text']:
                updates.append({
                    'layer_path': item['layer_path'],
                    'layer_folder': item['layer_folder'],
                    'element_index': item['element_index'],
                    'new_text': current_text,
                    'original_html': item['original_html']
                })

        if not updates:
            self.socket_handler.log("⚠️ No changes detected")
            return

        self.socket_handler.log(f"📝 Sending {len(updates)} text update(s)...")

        # Send update request
        self.socket_handler.send_request('update_layer_text', updates=updates)
