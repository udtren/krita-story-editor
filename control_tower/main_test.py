from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QLabel, QInputDialog, QFileDialog
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtCore import QTimer
from configs.main_window import (
    setup_dark_palette,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    BUTTON_HEIGHT,
    BUTTON_MIN_WIDTH,
    get_button_font,
    get_log_font
)
from utils.kra_reader import extract_text_from_kra
from story_editor import TextEditorWindow
import json
import sys


class ControlTower(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Initialize text editor window handler
        self.text_editor_handler = TextEditorWindow(self, self)

        # Set up socket
        self.socket = QLocalSocket(self)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_data_received)
        self.socket.errorOccurred.connect(self.on_error)

        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Connection status
        self.status_label = QLabel("Status: Not Connected")
        layout.addWidget(self.status_label)

        # Connect button
        self.connect_btn = QPushButton("Connect to Krita Docker")
        self.connect_btn.clicked.connect(self.connect_to_docker)
        self.connect_btn.setFont(get_button_font())
        self.connect_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.connect_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        layout.addWidget(self.connect_btn)

        # Test button
        self.test_btn = QPushButton("Test: Get Document Name")
        self.test_btn.clicked.connect(self.test_get_document_name)
        self.test_btn.setFont(get_button_font())
        self.test_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.test_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        self.test_btn.setEnabled(False)
        layout.addWidget(self.test_btn)

        # Get all documents button
        self.get_docs_btn = QPushButton("Get All Documents Info")
        self.get_docs_btn.clicked.connect(self.test_get_all_documents)
        self.get_docs_btn.setFont(get_button_font())
        self.get_docs_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.get_docs_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        self.get_docs_btn.setEnabled(False)
        layout.addWidget(self.get_docs_btn)

        # Get text layers button
        self.get_text_btn = QPushButton("Get Text Layers")
        self.get_text_btn.clicked.connect(self.test_get_text_layers)
        self.get_text_btn.setFont(get_button_font())
        self.get_text_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.get_text_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        self.get_text_btn.setEnabled(False)
        layout.addWidget(self.get_text_btn)

        # Get layer text button
        self.get_layer_text_btn = QPushButton("Get Layer Text")
        self.get_layer_text_btn.clicked.connect(self.test_get_layer_text)
        self.get_layer_text_btn.setFont(get_button_font())
        self.get_layer_text_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.get_layer_text_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        self.get_layer_text_btn.setEnabled(False)
        layout.addWidget(self.get_layer_text_btn)

        # Show text editor button
        self.show_text_editor_btn = QPushButton("Show Text Editor")
        self.show_text_editor_btn.clicked.connect(
            self.text_editor_handler.show_text_editor)
        self.show_text_editor_btn.setFont(get_button_font())
        self.show_text_editor_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.show_text_editor_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        self.show_text_editor_btn.setEnabled(False)
        layout.addWidget(self.show_text_editor_btn)

        # Read KRA offline button
        self.read_kra_btn = QPushButton("Read .kra File (Offline)")
        self.read_kra_btn.clicked.connect(self.test_read_kra_offline)
        self.read_kra_btn.setFont(get_button_font())
        self.read_kra_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.read_kra_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        layout.addWidget(self.read_kra_btn)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(get_log_font())
        layout.addWidget(self.log_output)

        self.log("Application started. Click 'Connect to Krita Docker' to begin.")

    def log(self, message):
        """Add a message to the log output"""
        self.log_output.append(f"[LOG] {message}")

    def connect_to_docker(self):
        """Connect to the Krita docker's local server"""
        self.log("Attempting to connect to 'krita_story_editor_bridge'...")
        self.socket.connectToServer("krita_story_editor_bridge")

        # Give it a moment to connect
        QTimer.singleShot(1000, self.check_connection)

    def check_connection(self):
        """Check if connection was successful"""
        if self.socket.state() != QLocalSocket.LocalSocketState.ConnectedState:
            self.log("⚠️ Connection failed! Make sure:")
            self.log("  1. Krita is running")
            self.log("  2. The Story Editor Agent docker is loaded")
            self.log("  3. The docker is visible in Krita's workspace")

    def on_connected(self):
        """Called when successfully connected"""
        self.log("✅ Connected to Krita docker!")
        self.status_label.setText("Status: Connected")
        self.status_label.setStyleSheet("color: green;")
        self.connect_btn.setEnabled(False)
        self.test_btn.setEnabled(True)
        self.get_docs_btn.setEnabled(True)
        self.get_text_btn.setEnabled(True)
        self.get_layer_text_btn.setEnabled(True)
        self.show_text_editor_btn.setEnabled(True)

    def on_disconnected(self):
        """Called when disconnected"""
        self.log("❌ Disconnected from Krita docker")
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("color: red;")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(False)
        self.get_docs_btn.setEnabled(False)
        self.get_text_btn.setEnabled(False)
        self.get_layer_text_btn.setEnabled(False)
        self.show_text_editor_btn.setEnabled(False)

    def on_error(self, error):
        """Called when socket error occurs"""
        error_msg = self.socket.errorString()
        self.log(f"❌ Socket Error: {error_msg}")

    def send_request(self, action, **params):
        """Send a request to the Krita docker"""
        request = {'action': action, **params}
        json_data = json.dumps(request)
        self.log(f"📤 Sending: {json_data}")
        self.socket.write(json_data.encode('utf-8'))
        self.socket.flush()

    def on_data_received(self):
        """Handle data received from the Krita docker"""
        data = self.socket.readAll().data().decode('utf-8')
        self.log(f"📥 Received: {data}")

        try:
            response = json.loads(data)
            self.log(f"✅ Parsed response: {response}")

            # Store text data if it's a get_layer_text response
            if 'text_layers' in response and response.get('success'):
                self.text_editor_handler.set_text_data(response['text_layers'])
        except json.JSONDecodeError as e:
            self.log(f"⚠️ Failed to parse JSON: {e}")

    def test_get_document_name(self):
        """Test the get_document_name action"""
        self.log("\n--- Testing get_document_name ---")
        self.send_request('get_document_name')

    def test_get_all_documents(self):
        """Test the get_all_documents action"""
        self.log("\n--- Testing get_all_documents ---")
        self.send_request('get_all_documents')

    def test_get_text_layers(self):
        """Test the get_text_layers action"""
        self.log("\n--- Testing get_text_layers ---")
        self.send_request('get_text_layers')

    def test_get_layer_text(self):
        """Test the get_layer_text action"""
        self.log("\n--- Testing get_layer_text ---")
        self.log("Retrieving text from all vector layers...")
        self.send_request('get_layer_text')

    def test_read_kra_offline(self):
        """Read text from a .kra file without connecting to Krita"""
        self.log("\n--- Testing offline .kra reading ---")

        # Open file dialog to select .kra file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select .kra File",
            "",
            "Krita Files (*.kra);;All Files (*)"
        )

        if not file_path:
            self.log("❌ No file selected")
            return

        self.log(f"Reading file: {file_path}")

        try:
            text_layers = extract_text_from_kra(file_path)

            if text_layers:
                self.log(f"✅ Found {len(text_layers)} layer(s) with text")
                self.log(
                    f"📥 Result: {json.dumps(text_layers, indent=2, ensure_ascii=False)}")
            else:
                self.log("⚠️ No text layers found in file")

        except Exception as e:
            self.log(f"❌ Error reading .kra file: {e}")


def main():
    app = QApplication(sys.argv)

    # Set dark color scheme
    setup_dark_palette(app)

    window = ControlTower()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
