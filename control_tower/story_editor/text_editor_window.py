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

        # Create new window
        self.text_editor_window = QWidget()
        self.text_editor_window.setWindowTitle("Text Editor")
        self.text_editor_window.resize(600, 400)

        # Main layout with close button at top
        main_layout = QVBoxLayout(self.text_editor_window)

        # Top bar with close button
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        close_btn = QPushButton("X")
        close_btn.setMaximumWidth(30)
        close_btn.setMaximumHeight(30)
        close_btn.clicked.connect(self.text_editor_window.close)
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)

        # VBoxLayout_1 for all documents
        documents_layout = QVBoxLayout()

        # For each text layer (treating each as a document for this test)
        for layer in self.text_data:
            # VBoxLayout_2 for each document
            doc_layout = QVBoxLayout()

            # Add label for layer info
            layer_label = QLabel(f"Layer: {layer.get('layer_folder', 'unknown')}")
            doc_layout.addWidget(layer_label)

            # Get text elements
            text_elements = layer.get('text_elements', [])

            # Add QTextEdit for each text element
            for text_elem in text_elements:
                text_edit = QTextEdit()

                # Extract the text content
                if isinstance(text_elem, dict):
                    text_content = text_elem.get('text', '')
                else:
                    text_content = str(text_elem)

                text_edit.setPlainText(text_content)
                text_edit.setMinimumHeight(100)
                doc_layout.addWidget(text_edit)

            documents_layout.addLayout(doc_layout)

        main_layout.addLayout(documents_layout)

        # Show the window
        self.text_editor_window.show()
        self.socket_handler.log(f"✅ Text editor opened with {len(self.text_data)} text layer(s)")
