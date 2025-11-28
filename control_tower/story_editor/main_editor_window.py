from pathlib import Path
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QMenu, QAction, QTextEdit, QPushButton
from PyQt5.QtCore import QTimer
from story_editor.utils.text_updater import create_svg_data_for_doc
from story_editor.widgets.find_replace import show_find_replace_dialog
from story_editor.widgets.story_board_window import StoryBoardWindow
from story_editor.widgets.new_text_edit import add_new_text_widget

# Import UI component factory functions from modular package
from story_editor.ui_components import scroll_areas as ui_scroll
from story_editor.ui_components import document as ui_doc

from config.story_editor_loader import (
    get_thumbnail_right_click_menu_stylesheet,
)

# UI Constants (minimal - most moved to ui_components modules)
MAIN_LAYOUT_MARGINS = (0, 0, 10, 20)


@dataclass
class LayerChange:
    """Represents a change to a text element in a layer."""

    new_text: QTextEdit
    shape_id: str


@dataclass
class LayerGroup:
    """Represents a layer group within a document."""

    layer_name: str
    layer_id: str
    layer_shapes: List[Dict[str, Any]]
    svg_content: str
    changes: List[LayerChange] = field(default_factory=list)


@dataclass
class TextEditWidget:
    """Represents a text editor widget with metadata."""

    widget: QTextEdit
    document_name: str
    layer_name: str
    layer_id: str
    shape_id: str


@dataclass
class DocumentState:
    """Represents the state of a document in the editor."""

    document_name: str
    document_path: str
    has_text_changes: bool = False
    new_text_widgets: List[Any] = field(default_factory=list)
    layer_groups: Dict[str, LayerGroup] = field(default_factory=dict)
    opened: bool = True
    text_edit_widgets: List[TextEditWidget] = field(default_factory=list)


class StoryEditorWindow:
    """Handles the text editor window functionality.

    Data Flow Overview:
    -------------------
    1. User opens Story Editor → show_text_editor() is called
    2. Socket request sent to Krita plugin → "get_all_docs_svg_data"
    3. Krita returns all_docs_svg_data → set_svg_data() receives it
    4. Window created → create_text_editor_window() builds UI
    5. User edits text → changes stored in all_docs_text_state
    6. User saves → send_merged_svg_request() sends updates back to Krita

    Key Data Structures:
    --------------------
    all_docs_svg_data: List[Dict] - Raw data from Krita (read-only)
        Structure:
        [{
            'document_name': str,          # e.g., 'Test001.kra'
            'document_path': str,          # Full path to .kra file
            'svg_data': List[Dict],        # SVG data for each text layer
            'opened': bool,                # Whether document is open in Krita
            'thumbnail': str               # Base64 encoded PNG thumbnail
        }]

        Each svg_data item contains:
        {
            'layer_name': str,             # e.g., 'layer2.shapelayer'
            'layer_id': str,               # Unique layer identifier
            'svg': str                     # SVG XML with text elements
        }

    all_docs_text_state: Dict[str, Dict] - Editable state (modified by user)
        Structure:
        {
            'document_name': {
                'document_name': str,
                'document_path': str,
                'has_text_changes': bool,
                'new_text_widgets': List,     # New text elements added
                'layer_groups': Dict,         # Existing text layers with edits
                'opened': bool,
                'text_edit_widgets': List     # QTextEdit widgets for find/replace
            }
        }
    """

    def __init__(self, parent, socket_handler):
        """
        Initialize the text editor window handler

        Args:
            parent: The parent widget (main window)
            socket_handler: Object with send_request and log methods
        """
        self.parent = parent
        self.socket_handler = socket_handler
        self.all_docs_svg_data = None
        self.parent_window = None  # Will be set by ControlTower

        self.doc_layouts = {}  # Store document layouts {doc_name: layout}
        self.active_doc_name = None  # Track which document is active for new text
        self.thumbnail_scroll_position = 0  # Track thumbnail scroll position
        self.content_scroll_position = 0  # Track content scroll position

        self.comic_config_info = None  # To store comic config info
        self.template_files = []  # To store template files list
        self.story_board_window = None  # Store reference to story board window

    def set_parent_window(self, parent_window) -> None:
        """Set the persistent parent window"""
        self.parent_window = parent_window
        # Set close event handler on parent window
        self.parent_window.closeEvent = lambda event: self._on_window_close(event)

    # ===================================================================
    # Helper Methods for UI Creation
    # ===================================================================

    def _save_current_scroll_positions(self) -> None:
        """Save current scroll positions before clearing content."""
        if hasattr(self, "thumbnail_scroll_area_widget"):
            self.thumbnail_scroll_position = (
                self.thumbnail_scroll_area_widget.verticalScrollBar().value()
            )
        if hasattr(self, "all_docs_scroll_area_widget"):
            self.content_scroll_position = (
                self.all_docs_scroll_area_widget.verticalScrollBar().value()
            )

    def _clear_previous_content(self) -> None:
        """Clear previous content in parent window's container."""
        if self.parent_window:
            while self.parent_window.content_layout.count():
                child = self.parent_window.content_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def _initialize_editor_state(self) -> None:
        """Initialize/reset editor state variables."""
        self.all_docs_text_state = {}
        self.new_text_widgets = []
        self.doc_layouts = {}
        self.active_doc_name = None

    def _create_thumbnail_scroll_area(self):
        """Create scroll area for document thumbnails - delegates to ui_components."""
        return ui_scroll.create_thumbnail_scroll_area(self)

    def _create_content_scroll_area(self):
        """Create scroll area for all documents' content - delegates to ui_components."""
        return ui_scroll.create_content_scroll_area(self)

    def _create_document_section(
        self, index: int, doc_data: Dict[str, Any], thumbnail_layout, all_docs_layout
    ) -> None:
        """Create UI section for a single document - delegates to ui_components."""
        ui_doc.create_document_section(
            index, doc_data, thumbnail_layout, all_docs_layout, self
        )

    def create_text_editor_window(self) -> None:
        """Create the content for the Story Editor"""
        if not self.all_docs_svg_data:
            self.socket_handler.log(
                "⚠️ No SVG data available. Make sure the request succeeded."
            )
            return

        # Prepare for new window creation
        self._save_current_scroll_positions()
        self._clear_previous_content()
        self._initialize_editor_state()

        # Create main layout
        thumbnail_and_text_layout = QHBoxLayout()

        # Create thumbnail and content scroll areas
        thumbnail_scroll_area, thumbnail_layout = self._create_thumbnail_scroll_area()
        all_docs_scroll_area, all_docs_layout = self._create_content_scroll_area()

        thumbnail_and_text_layout.addWidget(thumbnail_scroll_area)
        thumbnail_and_text_layout.addWidget(all_docs_scroll_area)
        thumbnail_and_text_layout.setContentsMargins(*MAIN_LAYOUT_MARGINS)

        # Process all documents
        for index, doc_data in enumerate(self.all_docs_svg_data):
            self._create_document_section(
                index, doc_data, thumbnail_layout, all_docs_layout
            )

        # Add stretch at the end of thumbnail layout (inside the container for proper scrolling)
        thumbnail_layout.setRowStretch(thumbnail_layout.rowCount(), 1)

        # Add stretch at the end of all_docs_layout (inside the container for proper scrolling)
        all_docs_layout.addStretch()

        # Add content to parent window's container
        if self.parent_window:
            self.parent_window.content_layout.addLayout(thumbnail_and_text_layout)

            # Show the parent window
            self.parent_window.show()

            # Restore scroll positions after window is shown (use QTimer to ensure scrollbars are ready)
            QTimer.singleShot(100, self._restore_scroll_positions)

    def add_new_text_widget(self) -> None:
        """Add a new empty text editor widget for creating new text"""
        add_new_text_widget(
            self.active_doc_name,
            self.doc_layouts,
            self.all_docs_text_state,
            self.socket_handler,
        )

    def _restore_scroll_positions(self) -> None:
        """Restore saved scroll positions for both scroll areas"""
        if (
            hasattr(self, "thumbnail_scroll_area_widget")
            and self.thumbnail_scroll_position > 0
        ):
            self.thumbnail_scroll_area_widget.verticalScrollBar().setValue(
                self.thumbnail_scroll_position
            )

        if (
            hasattr(self, "all_docs_scroll_area_widget")
            and self.content_scroll_position > 0
        ):
            self.all_docs_scroll_area_widget.verticalScrollBar().setValue(
                self.content_scroll_position
            )

    def send_merged_svg_request(self) -> None:
        """Send update requests for all modified texts and add new texts"""

        merged_requests = []

        self.socket_handler.log(f"⏳ Processing update data for documents...")

        for doc_name, doc_state in self.all_docs_text_state.items():

            # write_log(f"Processing document: {doc_name}")

            doc_path = doc_state["document_path"]
            # layer_groups Contains all changes for the existing layers
            layer_groups = doc_state["layer_groups"]
            # new_text_widgets Contains all new text widgets added by the user
            new_text_widgets = doc_state["new_text_widgets"]

            result = create_svg_data_for_doc(
                doc_name=doc_name,
                doc_path=doc_path,
                layer_groups=layer_groups,
                new_text_widgets=new_text_widgets,
                socket_handler=self.socket_handler,
                opened=doc_state.get("opened"),
            )

            """
            final_result = {
                "doc_name": doc_name,
                "doc_path": doc_path,
                "existing_texts_updated": [],
                "new_texts_added": [],
                "has_changes": False,
                "opened": opened,
            }
            final_result["new_texts_added"].append({"svg_data": svg_data})
            final_result["existing_texts_updated"].append(
                    {
                        "layer_name": layer_name,
                        "layer_id": layer_id,
                        "svg_data": valid_svg_data,
                    }
                )
            """
            if result.get("has_changes"):
                merged_requests.append(result)
                self.socket_handler.log(
                    f"✅ Update data for document: {doc_name} added to the merged requests"
                )

        if len(merged_requests) > 0:
            # write_log(f"merged_requests before send to agent: {merged_requests}")
            self.socket_handler.log(
                f"--- {len(merged_requests)} documents to update ---"
            )
            self.socket_handler.send_request(
                "docs_svg_update",
                merged_requests=merged_requests,
                krita_files_folder=(
                    self.parent.krita_files_folder
                    if hasattr(self.parent, "krita_files_folder")
                    else None
                ),
            )
        else:
            self.socket_handler.log("⚠️ No updates or new texts to send.")

    def show_text_editor(self) -> None:
        """Show text editor window with SVG data from Krita document"""
        # Clear any existing data
        self.all_docs_svg_data = None

        # Set the waiting flag on the parent (main window)
        if hasattr(self.parent, "_waiting_for_svg"):
            self.parent._waiting_for_svg = "text_editor"

        # Get krita folder path if available
        krita_folder_path = None
        if hasattr(self.parent, "krita_files_folder"):
            krita_folder_path = self.parent.krita_files_folder

        # Request the SVG data
        # The window will be created when set_svg_data() is called with the response
        if krita_folder_path:
            self.socket_handler.send_request(
                "get_all_docs_svg_data", folder_path=krita_folder_path
            )
        else:
            self.socket_handler.send_request("get_all_docs_svg_data")

    def set_svg_data(self, all_docs_svg_data: List[Dict[str, Any]]) -> None:
        """Store the received SVG data and create the editor window"""
        self.all_docs_svg_data = all_docs_svg_data
        # Automatically create the window when data is received
        self.create_text_editor_window()
        # Disable the open button when window is shown
        self._update_open_button_state(False)

    def set_comic_config_info(self, comic_config_info: Dict[str, Any]) -> None:
        """Store the comic config info for future use"""
        self.comic_config_info = comic_config_info

    def _on_window_close(self, event: Any) -> None:
        """Handle window close event to re-enable the open button"""
        # Re-enable the open button
        self._update_open_button_state(True)
        # Accept the close event
        event.accept()

    def _update_open_button_state(self, enabled: bool) -> None:
        """Update the state of the 'Open Story Editor' button in the main window"""
        if hasattr(self.parent, "show_story_editor_btn"):
            self.parent.show_story_editor_btn.setEnabled(enabled)
            if enabled:
                self.parent.show_story_editor_btn.setText("Open Story Editor")
                self.parent.show_story_editor_btn.setStyleSheet(
                    "background-color: #414a8e; color: #1a1625; padding: 5px;"
                )
            else:
                self.parent.show_story_editor_btn.setText("Story Editor is Open")
                self.parent.show_story_editor_btn.setStyleSheet(
                    "background-color: #666666; color: #999999; padding: 5px;"
                )

    def thumbnail_clicked(self, doc_name: str) -> None:
        """Handle thumbnail click - activate the document"""
        self.activate_document(doc_name)

    def activate_document(
        self, doc_name: str, clicked_btn: Optional[QPushButton] = None
    ) -> None:
        """Activate a document for adding new text"""
        # Uncheck all other buttons and reset thumbnail borders
        if hasattr(self, "doc_buttons"):
            for name, btn in self.doc_buttons.items():
                if name != doc_name:
                    btn.setChecked(False)
                    # Reset thumbnail border
                    if hasattr(self, "doc_thumbnails") and name in self.doc_thumbnails:
                        thumbnail = self.doc_thumbnails[name]
                        default_border = thumbnail.property("default_border")
                        thumbnail.setStyleSheet(f"border: 2px solid {default_border};")

        # Check the clicked button and update its thumbnail
        if hasattr(self, "doc_buttons") and doc_name in self.doc_buttons:
            self.doc_buttons[doc_name].setChecked(True)

        if hasattr(self, "doc_thumbnails") and doc_name in self.doc_thumbnails:
            thumbnail = self.doc_thumbnails[doc_name]
            active_border = thumbnail.property("active_border")
            thumbnail.setStyleSheet(
                f"border: 3px solid {active_border}; border-color: blue;"
            )

        # Set active document
        self.active_doc_name = doc_name
        # self.socket_handler.log(f"📄 Activated document: {doc_name}")

    def refresh_data(self) -> None:
        """Refresh the editor window with latest data from Krita"""
        self.socket_handler.log("🔄 Refreshing data from Krita")
        # Simply request new data, which will rebuild the window
        self.show_text_editor()

    def save_all_opened_docs(self) -> None:
        """Save all opened Krita documents"""
        self.socket_handler.log("💾 Saving all opened documents")
        self.socket_handler.send_request("save_all_opened_docs")

    def show_find_replace(self) -> None:
        """Show the find/replace dialog"""
        if not hasattr(self, "all_docs_text_state") or not self.all_docs_text_state:
            self.socket_handler.log("⚠️ No text editors available")
            return

        show_find_replace_dialog(self.parent_window, self.all_docs_text_state)

    def show_story_board(self) -> None:
        """Show the story board window with all thumbnails"""
        if not self.all_docs_svg_data:
            self.socket_handler.log("⚠️ No document data available")
            return

        # Close existing story board window if open
        if self.story_board_window is not None:
            self.story_board_window.close()

        # Create new story board window as independent popup (no parent to make it separate)
        self.story_board_window = StoryBoardWindow(self.all_docs_svg_data, parent=None)
        self.story_board_window.show()

    # ===================================================================
    # Context Menu Handlers
    # ===================================================================

    def show_thumbnail_context_menu(
        self,
        pos: Any,
        doc_name: str,
        thumbnail_label: QLabel,
        doc_path: str,
        comic_config_info: Optional[Dict[str, Any]],
    ) -> None:
        """Show context menu for thumbnail"""
        menu = QMenu(self.parent_window)
        menu.setStyleSheet(get_thumbnail_right_click_menu_stylesheet())

        # Add "Activate" action
        activate_action = menu.addAction("Activate")
        activate_action.triggered.connect(
            lambda: self.send_activate_document_request(doc_name)
        )

        # Add "Open" action
        open_action = menu.addAction(f"Open")
        open_action.triggered.connect(lambda: self.send_open_document_request(doc_path))

        # Add "Close" action
        close_action = menu.addAction("Close")
        close_action.triggered.connect(
            lambda: self.send_close_document_request(doc_name)
        )

        # Only documents belonging to the comic folder can be modified
        if comic_config_info:
            config_filepath = comic_config_info.get("config_filepath", "")
            doc_path_obj = Path(doc_path)
            config_parent = Path(config_filepath).parent
            if (
                config_parent in doc_path_obj.parents
                or doc_path_obj.parent == config_parent
            ):
                # print(f"Document {doc_name} is in config folder or its subfolder")

                # Add separator
                menu.addSeparator()

                # Add "Add From Template" action with submenu
                template_files = comic_config_info.get("template_files", [])
                if template_files:
                    add_new_action = menu.addAction("Add From Template")
                    select_template_menu = QMenu(self.parent_window)
                    select_template_menu.setStyleSheet(
                        get_thumbnail_right_click_menu_stylesheet()
                    )

                    for template in template_files:
                        template_name = os.path.basename(template)
                        template_action = QAction(template_name, self.parent_window)
                        template_action.triggered.connect(
                            lambda checked, t=template: self.send_add_new_document_from_template_request(
                                doc_path, t, config_filepath
                            )
                        )
                        select_template_menu.addAction(template_action)

                    add_new_action.setMenu(select_template_menu)

                # Add "Duplicate" action
                duplicate_action = menu.addAction("Duplicate")
                duplicate_action.triggered.connect(
                    lambda: self.send_duplicate_document_request(
                        doc_name, doc_path, config_filepath
                    )
                )

                # Add "Delete" action
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(
                    lambda: self.send_delete_document_request(
                        doc_name, doc_path, config_filepath
                    )
                )

        # Show menu at global position
        menu.exec_(thumbnail_label.mapToGlobal(pos))

    def send_open_document_request(self, doc_path: str) -> None:
        """Send open_document request to the agent"""
        self.socket_handler.log(f"📂 Requesting to open document: {doc_path}")
        self.socket_handler.send_request("open_document", doc_path=doc_path)

    def send_close_document_request(self, doc_name: str) -> None:
        """Send close_document request to the agent"""
        self.socket_handler.log(f"❌ Requesting to close document: {doc_name}")
        self.socket_handler.send_request("close_document", doc_name=doc_name)

    def send_activate_document_request(self, doc_name: str) -> None:
        """Send activate_document request to the agent"""
        self.socket_handler.log(f"➡️ Requesting to activate document: {doc_name}")
        self.socket_handler.send_request("activate_document", doc_name=doc_name)

    def send_add_new_document_from_template_request(
        self,
        target_doc_path: str,
        template_path: Optional[str] = None,
        config_filepath: Optional[str] = None,
    ) -> None:
        """Send add_new_document_from_template request to the agent"""
        self.socket_handler.log(f"📄➕ Requesting to add new document from template")
        self.socket_handler.send_request(
            "add_from_template",
            doc_path=target_doc_path,
            template_path=template_path,
            config_filepath=config_filepath,
        )

    def send_duplicate_document_request(
        self,
        target_doc_name: str,
        target_doc_path: str,
        config_filepath: Optional[str] = None,
    ) -> None:
        """Send duplicate_document request to the agent"""
        self.socket_handler.log(
            f"📄➕ Requesting to duplicate document: {target_doc_name}"
        )
        self.socket_handler.send_request(
            "duplicate_document",
            doc_name=target_doc_name,
            doc_path=target_doc_path,
            config_filepath=config_filepath,
        )

    def send_delete_document_request(
        self,
        target_doc_name: str,
        target_doc_path: str,
        config_filepath: Optional[str] = None,
    ) -> None:
        """Send delete_document request to the agent"""
        self.socket_handler.log(f"🗑️ Requesting to delete document: {target_doc_name}")
        self.socket_handler.send_request(
            "delete_document",
            doc_name=target_doc_name,
            doc_path=target_doc_path,
            config_filepath=config_filepath,
        )

    # ===================================================================
