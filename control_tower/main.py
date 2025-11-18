from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTextEdit,
    QLabel,
    QFileDialog,
)
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon

from config.template_manager import show_template_manager
from config.config_dialog import ConfigDialog
from story_editor import StoryEditorWindow, StoryEditorParentWindow
import json
import sys
import os
from config.main_window_loader import (
    setup_dark_palette,
    get_button_font,
    get_log_font,
)


class ControlTower(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor Control Tower")
        self.setFixedSize(800, 600)

        # Set window icon (for taskbar and title bar)
        icon_path = os.path.join(os.path.dirname(__file__), "images", "book_128.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Initialize text editor window handler
        self.text_editor_handler = StoryEditorWindow(self, self)

        # Create persistent parent window for Story Editor
        self.story_editor_parent_window = None

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

        # Get path to background image
        bg_image_path = os.path.join(
            os.path.dirname(__file__), "images", "coffee_pixel.png"
        )
        # Convert to forward slashes for Qt stylesheet
        bg_image_path = bg_image_path.replace("\\", "/")

        # Apply background only to the central widget, not children
        central_widget.setStyleSheet(
            f"""
            QWidget#centralWidget {{
                border-image: url({bg_image_path}) 0 0 0 0 stretch stretch;
            }}
        """
        )
        central_widget.setObjectName("centralWidget")
        layout = QVBoxLayout(central_widget)

        # Title Layout
        title_layout = QHBoxLayout()
        title_label = QLabel("Krita Story Editor")
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        )

        # Load custom font from file
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "Minecraft.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            title_font = QFont(font_family, 24)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #ecbd30;")
        else:
            # Fallback if font loading fails
            title_label.setFont(get_button_font())
            title_label.setStyleSheet("color: #ecbd30;")

        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(get_log_font())
        self.log_output.setStyleSheet(
            """
            QTextEdit {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(30, 30, 30, 255),
                    stop: 1 rgba(30, 30, 30, 0)
                );
                border: none;
                border-radius: 8px;
            }
        """
        )
        layout.addWidget(self.log_output)

        # Connection status (aligned to the right)
        status_layout = QHBoxLayout()
        status_layout.addStretch()  # Push label to the right
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            status_label_font = QFont(font_family, 10)
            self.status_label.setFont(status_label_font)
        else:
            # Fallback if font loading fails
            self.status_label.setFont(get_button_font())

        self.status_label.setFixedSize(250, 40)
        self.status_label.setStyleSheet(
            """
            background-color: black; 
            color: #c8c8c8; 
            padding: 3px;
            qproperty-alignment: 'AlignCenter';
            border-radius: 8px;
            """
        )
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)

        # Connect button (aligned to the right)
        connect_layout = QHBoxLayout()
        connect_layout.addStretch()  # Push button to the right
        self.connect_btn = QPushButton("Connect to Agent")
        self.connect_btn.clicked.connect(self.connect_to_docker)
        self.connect_btn.setFont(get_button_font())
        self.connect_btn.setStyleSheet(
            """
            color: #4b281c; 
            background-color: #9e6658;
            padding: 5px;
            border-radius: 8px;
            """
        )

        self.connect_btn.setFixedSize(250, 40)
        connect_layout.addWidget(self.connect_btn)
        layout.addLayout(connect_layout)

        # Krita Folder Path Input (aligned to the right)
        folder_layout = QHBoxLayout()
        folder_layout.addStretch()  # Push button to the right
        self.krita_files_path_btn = QPushButton("Set Krita Folder Path")
        self.krita_files_path_btn.clicked.connect(self.set_krita_files_folder_path)
        self.krita_files_path_btn.setFont(get_button_font())
        self.krita_files_path_btn.setStyleSheet(
            """
            color: #4b281c; 
            background-color: #9e6658;
            padding: 5px;
            border-radius: 8px;
            """
        )

        self.krita_files_path_btn.setFixedSize(250, 40)
        folder_layout.addWidget(self.krita_files_path_btn)
        layout.addLayout(folder_layout)

        # Template Management button (aligned to the right)
        edit_templates_layout = QHBoxLayout()
        edit_templates_layout.addStretch()  # Push button to the right
        self.edit_templates_btn = QPushButton("Edit Templates")
        self.edit_templates_btn.clicked.connect(self.open_template_manager)
        self.edit_templates_btn.setFont(get_button_font())
        self.edit_templates_btn.setStyleSheet(
            """
            color: #4b281c;
            background-color: #9e6658;
            padding: 5px;
            border-radius: 8px;
            """
        )

        self.edit_templates_btn.setFixedSize(250, 40)
        edit_templates_layout.addWidget(self.edit_templates_btn)
        layout.addLayout(edit_templates_layout)

        # Settings button (aligned to the right)
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()  # Push button to the right
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        self.settings_btn.setFont(get_button_font())
        self.settings_btn.setStyleSheet(
            """
            color: #4b281c;
            background-color: #9e6658;
            padding: 5px;
            border-radius: 8px;
            """
        )

        self.settings_btn.setFixedSize(250, 40)
        settings_layout.addWidget(self.settings_btn)
        layout.addLayout(settings_layout)

        # Add spacing between buttons #c8c8c8
        layout.addSpacing(20)  # 20 pixels of space

        # Open Story Editor (aligned to the right)
        editor_layout = QHBoxLayout()
        editor_layout.addStretch()  # Push button to the right
        self.show_story_editor_btn = QPushButton("Open Story Editor")
        self.show_story_editor_btn.clicked.connect(self.open_text_editor)
        self.show_story_editor_btn.setStyleSheet(
            """
            background-color: #414a8e; 
            color: #1a1625; 
            padding: 5px; 
            border-radius: 8px;
            """
        )
        self.show_story_editor_btn.setFont(get_button_font())

        self.show_story_editor_btn.setFixedSize(250, 40)
        self.show_story_editor_btn.setEnabled(False)
        editor_layout.addWidget(self.show_story_editor_btn)
        layout.addLayout(editor_layout)

        self.log("Application started. Click 'Connect to Story Editor Agent' to begin.")

    def closeEvent(self, event):
        """Handle main window close event - close all child windows"""
        # Close the Story Editor Parent Window if it exists
        if self.story_editor_parent_window:
            self.story_editor_parent_window.close()

        # Accept the close event to allow the main window to close
        event.accept()

    def log(self, message):
        """Add a message to the log output"""
        self.log_output.append(f" {message}")

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
        self.status_label.setStyleSheet(
            "background-color: black; color: #4cc340; padding: 5px;"
        )
        self.connect_btn.setEnabled(False)
        self.connect_btn.setStyleSheet("color: gray;")

        self.show_story_editor_btn.setEnabled(True)

    def on_disconnected(self):
        """Called when disconnected"""
        self.log("❌ Disconnected from Krita docker")
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet(
            "background-color: black; color: #c8c8c8; padding: 5px;"
        )

        self.connect_btn.setEnabled(True)
        self.connect_btn.setStyleSheet("color: #4b281c; padding: 5px;")

        self.show_story_editor_btn.setEnabled(False)

    def on_error(self, error):
        """Called when socket error occurs"""
        error_msg = self.socket.errorString()
        self.log(f"❌ Socket Error: {error_msg}")

    def send_request(self, action, **params):
        """Send a request to the Krita docker"""
        request = {"action": action, **params}
        json_data = json.dumps(request)
        self.log(f"📤 Sending Request to the Agent: {request['action']}")
        self.socket.write(json_data.encode("utf-8"))
        self.socket.flush()

    def on_data_received(self):
        """Handle data received from the Krita docker"""
        data = self.socket.readAll().data().decode("utf-8")

        try:
            response = json.loads(data)

            # Determine response type and handle accordingly
            match response:
                case {"docs_svg_update_result": result, "success": True}:
                    self.log(f"✔️ Text Update Request Finishied: {result}")
                    self.text_editor_handler.refresh_data()

                case {
                    "all_docs_svg_data": svg_data,
                    "comic_config_info": comic_config_info,
                    "success": True,
                }:
                    self.log(
                        f"📥 All docs svg data and comic config info received from agent"
                    )
                    self.text_editor_handler.set_svg_data(svg_data)
                    self.text_editor_handler.set_comic_config_info(comic_config_info)
                    self._waiting_for_svg = None

                case {"all_docs_svg_data": svg_data, "success": True}:
                    self.log(f"📥 All docs svg data received from agent")
                    self.text_editor_handler.set_svg_data(svg_data)
                    self._waiting_for_svg = None

                case {
                    "response_type": "save_all_opened_docs",
                    "success": True,
                }:
                    result = response.get("result", "Unknown")
                    self.log(f"💾 {result}")

                case {
                    "response_type": "activate_document",
                    "success": True,
                }:
                    result = response.get("result", "Unknown")
                    self.log(f"💾 {result}")

                case {"response_type": "open_document", "success": True}:
                    result = response.get("result", "Unknown")
                    self.log(f"📂 {result}")
                    self.text_editor_handler.refresh_data()

                case {"response_type": "close_document", "success": True}:
                    result = response.get("result", "Unknown")
                    self.log(f"🗑️ {result}")
                    self.text_editor_handler.refresh_data()

                case {"progress": progress}:
                    self.log(f"📋 Agent Progress: {progress}")

                case _:
                    self.log(f"Other Response: {response}")

        except json.JSONDecodeError as e:
            self.log(f"⚠️ Failed to parse JSON: {e}")

    def open_text_editor(self):
        """Open the text editor window"""
        # Create parent window only once
        if not self.story_editor_parent_window:
            self.story_editor_parent_window = StoryEditorParentWindow(
                self.text_editor_handler
            )
            # Pass parent window to the handler
            self.text_editor_handler.set_parent_window(self.story_editor_parent_window)

        self._waiting_for_svg = "text_editor"
        self.text_editor_handler.show_text_editor()

    def open_template_manager(self):
        """Open the template manager window"""
        self.log("📝 Opening Template Manager...")
        self.template_manager_window = show_template_manager(self)

    def open_settings(self):
        """Open the settings dialog"""
        self.log("⚙️ Opening Settings...")
        settings_dialog = ConfigDialog(self)
        if settings_dialog.exec_():
            self.log("✅ Settings saved successfully")
        else:
            self.log("❌ Settings changes cancelled")

    def set_krita_files_folder_path(self):
        """Set the folder path where Krita files are located"""
        self.log("\n--- Setting Krita Files Folder Path ---")

        # Open folder dialog to select directory
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Krita Files Folder", "", QFileDialog.Option.ShowDirsOnly
        )

        if not folder_path:
            self.log("❌ No folder selected")
            return

        self.log(f"✅ Krita files folder set to: {folder_path}")

        # Store the path (you can save this to a config file or use it for batch operations)
        self.krita_files_folder = folder_path
        self.krita_files_path_btn.setText(f"{folder_path}")
        self.krita_files_path_btn.setStyleSheet(
            """
            font-size: 12px;  
            color: #4b281c; 
            background-color: #9e6658;
            font-weight: bold;"""
        )

        # Refresh the Story Editor window if it exists
        if (
            self.story_editor_parent_window
            and self.story_editor_parent_window.isVisible()
        ):
            self.text_editor_handler.refresh_data()


class SingleInstanceChecker:
    """Ensures only one instance of the application runs at a time"""

    def __init__(self, app_id="krita_story_editor_control_tower"):
        self.app_id = app_id
        self.server = QLocalServer()
        self.socket = QLocalSocket()

    def is_already_running(self):
        """Check if another instance is already running"""
        # Try to connect to an existing server
        self.socket.connectToServer(self.app_id)

        # If connection succeeds, another instance is running
        if self.socket.waitForConnected(500):
            return True

        # No existing instance, so create a server for this instance
        # Remove any stale server first
        QLocalServer.removeServer(self.app_id)

        # Start listening
        if not self.server.listen(self.app_id):
            return True  # Failed to start server, assume another instance exists

        return False

    def cleanup(self):
        """Clean up the server"""
        if self.server.isListening():
            self.server.close()


def main():
    app = QApplication(sys.argv)

    # Set application-wide icon (important for Windows taskbar)
    icon_path = os.path.join(os.path.dirname(__file__), "images", "book_128.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Check for existing instance
    instance_checker = SingleInstanceChecker()
    if instance_checker.is_already_running():
        print("Another instance of Story Editor Control Tower is already running.")
        sys.exit(0)

    # Set dark color scheme
    setup_dark_palette(app)

    window = ControlTower()
    window.show()

    # Clean up the instance checker on exit
    app.aboutToQuit.connect(instance_checker.cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
