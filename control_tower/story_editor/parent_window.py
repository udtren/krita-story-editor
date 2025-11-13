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
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
import os
from config.story_editor_loader import (
    get_window_stylesheet,
    get_toolbar_stylesheet,
    STORY_EDITOR_WINDOW_WIDTH,
    STORY_EDITOR_WINDOW_HEIGHT,
)
from config.shortcuts_loader import (
    NEW_TEXT_SHORTCUT,
    REFRESH_SHORTCUT,
    UPDATE_KRITA_SHORTCUT,
    PIN_WINDOW_SHORTCUT,
)


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
