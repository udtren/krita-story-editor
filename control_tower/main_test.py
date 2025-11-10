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
from story_editor import StoryEditorWindow
import json
import sys


class ControlTower(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Initialize text editor window handler
        self.text_editor_handler = StoryEditorWindow(self, self)

        # Track which editor is waiting for SVG data
        self._waiting_for_svg = None  # 'text_editor'

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
        self.connect_btn = QPushButton("Connect to Story Editor Agent")
        self.connect_btn.clicked.connect(self.connect_to_docker)
        self.connect_btn.setFont(get_button_font())
        self.connect_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.connect_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        layout.addWidget(self.connect_btn)

        # Open Story Editor
        self.show_story_editor_btn = QPushButton("Open/Refresh Story Editor")
        self.show_story_editor_btn.clicked.connect(self.open_text_editor)
        self.show_story_editor_btn.setFont(get_button_font())
        self.show_story_editor_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.show_story_editor_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        self.show_story_editor_btn.setEnabled(False)
        layout.addWidget(self.show_story_editor_btn)

        # Test button
        self.test_btn = QPushButton("TEST")
        self.test_btn.clicked.connect(self.test_get_all_docs_svg_data)
        self.test_btn.setFont(get_button_font())
        self.test_btn.setMinimumHeight(BUTTON_HEIGHT)
        self.test_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        layout.addWidget(self.test_btn)

        # Read KRA offline button
        # self.read_kra_btn = QPushButton("Read .kra File (Offline)")
        # self.read_kra_btn.clicked.connect(self.test_read_kra_offline)
        # self.read_kra_btn.setFont(get_button_font())
        # self.read_kra_btn.setMinimumHeight(BUTTON_HEIGHT)
        # self.read_kra_btn.setMinimumWidth(BUTTON_MIN_WIDTH)
        # layout.addWidget(self.read_kra_btn)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(get_log_font())
        layout.addWidget(self.log_output)

        self.log(
            "Application started. Click 'Connect to Story Editor Agent' to begin.")

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

        self.show_story_editor_btn.setEnabled(True)

    def on_disconnected(self):
        """Called when disconnected"""
        self.log("❌ Disconnected from Krita docker")
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("color: red;")
        self.connect_btn.setEnabled(True)

        self.show_story_editor_btn.setEnabled(False)

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
        # self.log(f"📥 Received: {data}")

        try:
            response = json.loads(data)

            # Only log non-SVG responses (SVG data is too large)
            if 'text_update_request_result' in response and response.get('success'):
                self.log(
                    f"✅ Text Update Request Finishied: {response['text_update_request_result']}")
                self.text_editor_handler.refresh_data()

            if 'all_docs_svg_data' in response and response.get('success'):
                self.log(
                    f"✅ Received SVG data for all open documents")

                # Route to the appropriate handler based on which one is waiting
                if self._waiting_for_svg == 'text_editor':
                    self.text_editor_handler.set_svg_data(
                        response['all_docs_svg_data'])
                self._waiting_for_svg = None

            if 'svg_data' not in response and 'all_docs_svg_data' not in response:
                self.log(f"✅ Parsed response: {response}")

        except json.JSONDecodeError as e:
            self.log(f"⚠️ Failed to parse JSON: {e}")

    def open_text_editor(self):
        """Open the text editor window"""
        self._waiting_for_svg = 'text_editor'
        self.text_editor_handler.show_text_editor()

    def test_get_svg_data(self):
        """Test the get_svg_data action"""
        self.log("\n--- Testing get_svg_data ---")
        self.log("Retrieving SVG data from all vector layers...")
        self.send_request('get_all_svg_data')

    def test_get_all_docs_svg_data(self):
        """Test the get_all_docs_svg_data action"""
        self.log("\n--- Testing get_all_docs_svg_data ---")
        self.log(
            "Retrieving SVG data from all vector layers in all open documents...")
        self.send_request('get_all_docs_svg_data')

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
