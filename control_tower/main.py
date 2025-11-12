from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QTextEdit,
    QLabel,
    QInputDialog,
    QFileDialog,
    QToolBar,
    QAction,
)
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
from configs.main_window import (
    setup_dark_palette,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    BUTTON_HEIGHT,
    BUTTON_MIN_WIDTH,
    get_button_font,
    get_log_font,
)
from utils.kra_reader import extract_text_from_kra
from utils.template_manager import show_template_manager
from story_editor import StoryEditorWindow
from configs.story_editor import (
    get_window_stylesheet,
    get_toolbar_stylesheet,
    STORY_EDITOR_WINDOW_WIDTH,
    STORY_EDITOR_WINDOW_HEIGHT,
)
from configs.shortcuts import (
    NEW_TEXT_SHORTCUT,
    REFRESH_SHORTCUT,
    UPDATE_KRITA_SHORTCUT,
    PIN_WINDOW_SHORTCUT,
)
import json
import sys
import os


class StoryEditorParentWindow(QWidget):
    """Persistent parent window that contains the toolbar and content area"""

    def __init__(self, story_editor_handler, parent=None):
        super().__init__(parent)
        self.story_editor_handler = story_editor_handler
        self.setWindowTitle("Story Editor")
        self.setStyleSheet(get_window_stylesheet())
        self.resize(STORY_EDITOR_WINDOW_WIDTH, STORY_EDITOR_WINDOW_HEIGHT)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setStyleSheet(get_toolbar_stylesheet())
        main_layout.addWidget(toolbar)

        # Get absolute path to icon
        icon_path_bath = os.path.join(
            os.path.dirname(__file__), "story_editor", "icons"
        )

        new_text_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'plus.png')}"),
            "Add New Text",
            self,
        )
        new_text_btn.setStatusTip("Add a new text widget to the active document")
        new_text_btn.setShortcut(NEW_TEXT_SHORTCUT)
        new_text_btn.triggered.connect(self.story_editor_handler.add_new_text_widget)
        toolbar.addAction(new_text_btn)

        refresh_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'refresh.png')}"),
            "Refresh from Krita document",
            self,
        )
        refresh_btn.setStatusTip("Reload text data from Krita document")
        refresh_btn.setShortcut(REFRESH_SHORTCUT)
        refresh_btn.triggered.connect(self.story_editor_handler.refresh_data)
        toolbar.addAction(refresh_btn)

        save_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'disk.png')}"),
            "Save All Opened Documents",
            self,
        )
        save_btn.setStatusTip("Save all opened Krita documents")
        save_btn.triggered.connect(self.story_editor_handler.save_all_opened_docs)
        toolbar.addAction(save_btn)

        update_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'check.png')}"),
            "Update Krita",
            self,
        )
        update_btn.setStatusTip("Update Krita document with modified and new texts")
        update_btn.setShortcut(UPDATE_KRITA_SHORTCUT)
        update_btn.triggered.connect(self.story_editor_handler.send_merged_svg_request)
        toolbar.addAction(update_btn)

        # Add separator
        toolbar.addSeparator()

        # Find/Replace button
        find_replace_btn = QAction(
            "Find/Replace",
            self,
        )
        find_replace_btn.setStatusTip("Find and replace text in all editors")
        find_replace_btn.triggered.connect(self.story_editor_handler.show_find_replace)
        toolbar.addAction(find_replace_btn)

        # Add spacer to push pin button to the right
        spacer = QWidget()
        spacer.setSizePolicy(
            QWidget().sizePolicy().Expanding, QWidget().sizePolicy().Preferred
        )
        toolbar.addWidget(spacer)

        # Pin button to keep window on top
        self.pin_btn = QAction(
            QIcon(f"{os.path.join(icon_path_bath, 'thumbtack_light.png')}"),
            "Pin Window on Top",
            self,
        )
        self.pin_btn.setCheckable(True)
        self.pin_btn.setStatusTip("Keep Story Editor window on top of all windows")
        self.pin_btn.setShortcut(PIN_WINDOW_SHORTCUT)
        self.pin_btn.triggered.connect(self.toggle_window_pin)
        toolbar.addAction(self.pin_btn)

        # Create a container for the content that will be updated on refresh
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.content_container)

    def toggle_window_pin(self, checked):
        """Toggle window always-on-top state"""
        # Get current window flags
        flags = self.windowFlags()

        # Get icon path
        icon_path_bath = os.path.join(
            os.path.dirname(__file__), "story_editor", "icons"
        )

        if checked:
            # Add WindowStaysOnTopHint flag
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            # Change icon to dark thumbtack
            self.pin_btn.setIcon(
                QIcon(os.path.join(icon_path_bath, "thumbtack_dark.png"))
            )
            self.story_editor_handler.socket_handler.log(
                "📌 Story Editor window pinned on top"
            )
        else:
            # Remove WindowStaysOnTopHint flag
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            # Change icon back to light thumbtack
            self.pin_btn.setIcon(
                QIcon(os.path.join(icon_path_bath, "thumbtack_light.png"))
            )
            self.story_editor_handler.socket_handler.log(
                "📌 Story Editor window unpinned"
            )

        # Need to show the window again after changing flags
        self.show()


class ControlTower(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

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

                case {"all_docs_svg_data": svg_data, "success": True}:
                    self.log(f"📥 All docs svg data received from agent")
                    # Route to the appropriate handler based on which one is waiting
                    if self._waiting_for_svg == "text_editor":
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


def main():
    app = QApplication(sys.argv)

    # Set dark color scheme
    setup_dark_palette(app)

    window = ControlTower()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
