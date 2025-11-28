from pathlib import Path
import os
import base64
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QScrollArea,
    QMenu,
    QSizePolicy,
    QGridLayout,
    QAction,
)
from PyQt5.QtCore import QByteArray, QTimer, Qt
from PyQt5.QtGui import QPixmap
from story_editor.utils.text_updater import create_svg_data_for_doc
from story_editor.utils.svg_parser import parse_krita_svg
from story_editor.widgets.vertical_label import VerticalLabel
from story_editor.widgets.find_replace import show_find_replace_dialog
from story_editor.widgets.story_board_window import StoryBoardWindow
from story_editor.utils.logs import write_log
from story_editor.widgets.new_text_edit import add_new_text_widget

from config.story_editor_loader import (
    get_text_editor_font,
    get_tspan_editor_stylesheet,
    get_activate_button_disabled_stylesheet,
    get_activate_button_stylesheet,
    get_thumbnail_status_label_stylesheet,
    get_thumbnail_status_label_disabled_stylesheet,
    get_thumbnail_right_click_menu_stylesheet,
    get_thumbnail_layout_settings,
    TEXT_EDITOR_MIN_HEIGHT,
    TEXT_EDITOR_MAX_HEIGHT,
)

THUMBNAIL_LABEL_WIDTH, THUMBNAIL_LAYOUT_GRID_COLUMNS = get_thumbnail_layout_settings()
DOCUMENT_STATUS_LABEL_WIDTH = 24
THUMBNAIL_SCROLL_AREA_WIDTH = (
    THUMBNAIL_LABEL_WIDTH + DOCUMENT_STATUS_LABEL_WIDTH + 15
) * THUMBNAIL_LAYOUT_GRID_COLUMNS

# UI Constants
ACTIVATE_BUTTON_WIDTH = 40
ACTIVATE_BUTTON_MIN_HEIGHT = 200
THUMBNAIL_BORDER_DEFAULT = "#555"
THUMBNAIL_BORDER_ACTIVE = "#aaa"
THUMBNAIL_BACKGROUND_COLOR = "#aa805a"
DOCUMENT_CONTAINER_BORDER_COLOR = "#333333"
DOCUMENT_CONTAINER_BORDER_WIDTH = 2
TEXT_EDITOR_HEIGHT_PADDING = 10
SCROLL_RESTORE_DELAY_MS = 100
THUMBNAIL_SPACING = 0
THUMBNAIL_MARGINS = 0
CONTENT_LAYOUT_MARGINS = (0, 0, 15, 0)
MAIN_LAYOUT_MARGINS = (0, 0, 10, 20)
DOC_CONTAINER_MARGINS = (5, 5, 5, 5)


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

    def _create_thumbnail_scroll_area(self) -> Tuple[QScrollArea, QGridLayout]:
        """Create scroll area for document thumbnails.

        Returns:
            Tuple of (scroll_area, thumbnail_layout)
        """
        thumbnail_scroll_area = QScrollArea()
        thumbnail_scroll_area.setWidgetResizable(True)
        thumbnail_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        thumbnail_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        thumbnail_scroll_area.setFrameShape(QScrollArea.NoFrame)
        thumbnail_scroll_area.setMaximumWidth(THUMBNAIL_SCROLL_AREA_WIDTH)

        # Create container widget for thumbnails
        thumbnail_container = QWidget()
        thumbnail_layout = QGridLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(
            THUMBNAIL_MARGINS, THUMBNAIL_MARGINS, THUMBNAIL_MARGINS, THUMBNAIL_MARGINS
        )

        # Set the container as scroll area's widget
        thumbnail_scroll_area.setWidget(thumbnail_container)

        # Store reference for saving position later
        self.thumbnail_scroll_area_widget = thumbnail_scroll_area

        return thumbnail_scroll_area, thumbnail_layout

    def _create_content_scroll_area(self) -> Tuple[QScrollArea, QVBoxLayout]:
        """Create scroll area for all documents' content.

        Returns:
            Tuple of (scroll_area, all_docs_layout)
        """
        all_docs_scroll_area = QScrollArea()
        all_docs_scroll_area.setWidgetResizable(True)
        all_docs_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        all_docs_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        all_docs_scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Create container widget for all documents
        all_docs_container = QWidget()
        all_docs_layout = QVBoxLayout(all_docs_container)
        all_docs_layout.setContentsMargins(*CONTENT_LAYOUT_MARGINS)

        # Set the container as scroll area's widget
        all_docs_scroll_area.setWidget(all_docs_container)

        # Store reference for saving position later
        self.all_docs_scroll_area_widget = all_docs_scroll_area

        return all_docs_scroll_area, all_docs_layout

    def _decode_base64_thumbnail(self, thumbnail_data: str) -> QPixmap:
        """Decode base64 thumbnail data to QPixmap.

        Args:
            thumbnail_data: Base64 encoded image data (with or without data URI prefix)

        Returns:
            QPixmap object with the decoded image

        Raises:
            Exception: If decoding fails
        """
        # Remove the data URI prefix if present
        if thumbnail_data.startswith("data:image"):
            thumbnail_data = thumbnail_data.split(",", 1)[1]

        # Decode base64 to bytes
        image_bytes = base64.b64decode(thumbnail_data)

        # Create QPixmap from bytes
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(image_bytes))

        return pixmap

    def _create_thumbnail_label(
        self, doc_name: str, doc_path: str, thumbnail: Optional[str]
    ) -> QLabel:
        """Create and configure thumbnail label for a document.

        Args:
            doc_name: Name of the document
            doc_path: Full path to the document
            thumbnail: Base64 encoded thumbnail data (optional)

        Returns:
            Configured QLabel with thumbnail or placeholder
        """
        thumbnail_label = QLabel()
        thumbnail_label.setFixedWidth(THUMBNAIL_LABEL_WIDTH)
        thumbnail_label.setStyleSheet(
            f"border: {DOCUMENT_CONTAINER_BORDER_WIDTH}px solid {THUMBNAIL_BORDER_DEFAULT}; "
            f"background-color: {THUMBNAIL_BACKGROUND_COLOR}; color: #000000;"
        )
        thumbnail_label.setProperty("default_border", THUMBNAIL_BORDER_DEFAULT)
        thumbnail_label.setProperty("active_border", THUMBNAIL_BORDER_ACTIVE)

        # Load thumbnail from base64 data if available
        if thumbnail:
            try:
                pixmap = self._decode_base64_thumbnail(thumbnail)

                # Scale pixmap to width while maintaining aspect ratio
                pixmap = pixmap.scaledToWidth(
                    THUMBNAIL_LABEL_WIDTH, Qt.SmoothTransformation
                )
                thumbnail_label.setPixmap(pixmap)
                # Set label size to match the scaled pixmap
                thumbnail_label.setFixedSize(pixmap.size())

                # Set tooltip with document info
                thumbnail_label.setToolTip(f"Document: {doc_name}\nPath: {doc_path}")
            except Exception as e:
                # If loading fails, show placeholder text
                thumbnail_label.setText("No\nPreview")
                thumbnail_label.setAlignment(Qt.AlignCenter)
        else:
            # No thumbnail available
            thumbnail_label.setText("No\nPreview")
            thumbnail_label.setAlignment(Qt.AlignCenter)

        return thumbnail_label

    def _setup_thumbnail_context_menu(
        self, thumbnail_label: QLabel, doc_name: str, doc_path: str
    ) -> None:
        """Setup context menu for thumbnail label.

        Args:
            thumbnail_label: The thumbnail label widget
            doc_name: Name of the document
            doc_path: Full path to the document
        """
        thumbnail_label.setContextMenuPolicy(Qt.CustomContextMenu)
        thumbnail_label.customContextMenuRequested.connect(
            lambda pos: self.show_thumbnail_context_menu(
                pos, doc_name, thumbnail_label, doc_path, self.comic_config_info
            )
        )

    def _create_document_status_label(self, opened: bool) -> VerticalLabel:
        """Create vertical status label for a document.

        Args:
            opened: Whether the document is opened

        Returns:
            Configured VerticalLabel widget
        """
        status_text = "opened" if opened else "closed"
        document_status_label = VerticalLabel(status_text)
        document_status_label.setFixedWidth(DOCUMENT_STATUS_LABEL_WIDTH)
        document_status_label.setContentsMargins(0, 0, 0, 0)

        if opened:
            document_status_label.setStyleSheet(get_thumbnail_status_label_stylesheet())
        else:
            document_status_label.setStyleSheet(
                get_thumbnail_status_label_disabled_stylesheet()
            )

        return document_status_label

    def _create_activate_button(
        self, doc_name: str, doc_path: str, opened: bool
    ) -> QPushButton:
        """Create activate button for a document.

        Args:
            doc_name: Name of the document
            doc_path: Full path to the document
            opened: Whether the document is opened

        Returns:
            Configured QPushButton
        """
        # Add line breaks between each character for vertical text
        vertical_doc_name = "\n".join(f"{doc_name}".replace(".kra", ""))
        activate_btn = QPushButton(vertical_doc_name)
        activate_btn.setFixedWidth(ACTIVATE_BUTTON_WIDTH)
        activate_btn.setMinimumHeight(ACTIVATE_BUTTON_MIN_HEIGHT)

        if not opened:
            activate_btn.setStyleSheet(get_activate_button_disabled_stylesheet())
            activate_btn.setEnabled(False)
            activate_btn.setToolTip(f"Document: {doc_name} (offline)\nPath: {doc_path}")
        else:
            activate_btn.setCheckable(True)
            activate_btn.setToolTip(
                f"Document: {doc_name} (click to activate)\nPath: {doc_path}"
            )
            activate_btn.clicked.connect(
                lambda _checked, name=doc_name, btn=activate_btn: self.activate_document(
                    name, btn
                )
            )
            activate_btn.setStyleSheet(get_activate_button_stylesheet())
            activate_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Store button reference
        if not hasattr(self, "doc_buttons"):
            self.doc_buttons = {}
        self.doc_buttons[doc_name] = activate_btn

        return activate_btn

    def _initialize_document_state(
        self, doc_name: str, doc_path: str, opened: bool
    ) -> None:
        """Initialize state tracking for a document.

        Args:
            doc_name: Name of the document
            doc_path: Full path to the document
            opened: Whether the document is opened
        """
        self.all_docs_text_state[doc_name] = {
            "document_name": doc_name,
            "document_path": doc_path,
            "has_text_changes": False,
            "new_text_widgets": [],
            "layer_groups": {},
            "opened": opened,
            "text_edit_widgets": [],
        }

    def _create_text_editor_widget(
        self, doc_name: str, layer_name: str, layer_id: str, layer_shape: Dict[str, Any]
    ) -> QTextEdit:
        """Create a text editor widget for a text element.

        Args:
            doc_name: Name of the document
            layer_name: Name of the layer
            layer_id: ID of the layer
            layer_shape: Shape data containing text content and element ID

        Returns:
            Configured QTextEdit widget
        """
        text_edit = QTextEdit()
        text_edit.setPlainText(layer_shape["text_content"])
        text_edit.setToolTip(
            f"Doc: {doc_name} | Layer: {layer_name} | Layer Id: {layer_id} | "
            f"Shape ID: {layer_shape['element_id']}"
        )
        text_edit.setAcceptRichText(False)
        text_edit.setFont(get_text_editor_font())
        text_edit.setStyleSheet(get_tspan_editor_stylesheet())
        text_edit.setMaximumHeight(TEXT_EDITOR_MAX_HEIGHT)

        # Auto-adjust height based on content
        doc_height = text_edit.document().size().height()
        text_edit.setMinimumHeight(
            min(
                max(
                    int(doc_height) + TEXT_EDITOR_HEIGHT_PADDING, TEXT_EDITOR_MIN_HEIGHT
                ),
                TEXT_EDITOR_MAX_HEIGHT,
            )
        )

        return text_edit

    def _populate_layer_editors(
        self,
        doc_name: str,
        doc_path: str,
        svg_data: List[Dict[str, Any]],
        doc_level_layers_layout: QVBoxLayout,
    ) -> None:
        """Populate text editors for all layers in a document.

        Args:
            doc_name: Name of the document
            doc_path: Full path to the document
            svg_data: List of layer data dictionaries
            doc_level_layers_layout: Layout to add editors to
        """
        for layer_data in svg_data:
            layer_name = layer_data.get("layer_name", "unknown")
            layer_id = layer_data.get("layer_id", "unknown")
            svg_content = layer_data.get("svg", "")

            parsed_svg_data = parse_krita_svg(doc_name, doc_path, layer_id, svg_content)
            # write_log(f"parsed_svg_data: {parsed_svg_data}")

            if not parsed_svg_data["layer_shapes"]:
                continue

            self.all_docs_text_state[doc_name]["layer_groups"][layer_id] = {
                "layer_name": layer_name,
                "layer_id": layer_id,
                "layer_shapes": parsed_svg_data["layer_shapes"],
                "svg_content": svg_content,
                "changes": [],
            }

            # Add QTextEdit for each text element
            for elem_idx, layer_shape in enumerate(parsed_svg_data["layer_shapes"]):
                svg_section_level_layout = QHBoxLayout()

                # Create text editor
                text_edit = self._create_text_editor_widget(
                    doc_name, layer_name, layer_id, layer_shape
                )

                svg_section_level_layout.addWidget(text_edit)

                self.all_docs_text_state[doc_name]["layer_groups"][layer_id][
                    "changes"
                ].append(
                    {
                        "new_text": text_edit,
                        "shape_id": layer_shape["element_id"],
                    }
                )

                # Add to text_edit_widgets list for find/replace functionality
                self.all_docs_text_state[doc_name]["text_edit_widgets"].append(
                    {
                        "widget": text_edit,
                        "document_name": doc_name,
                        "layer_name": layer_name,
                        "layer_id": layer_id,
                        "shape_id": layer_shape["element_id"],
                    }
                )

                doc_level_layers_layout.addLayout(svg_section_level_layout)

    def _create_document_section(
        self,
        index: int,
        doc_data: Dict[str, Any],
        thumbnail_layout: QGridLayout,
        all_docs_layout: QVBoxLayout,
    ) -> None:
        """Create UI section for a single document.

        Args:
            index: Document index for grid positioning
            doc_data: Document data dictionary
            thumbnail_layout: Grid layout for thumbnails
            all_docs_layout: Vertical layout for document content
        """
        doc_name = doc_data.get("document_name", "unknown")
        doc_path = doc_data.get("document_path", "unknown")
        svg_data = doc_data.get("svg_data", [])
        opened = doc_data.get("opened", True)
        thumbnail = doc_data.get("thumbnail", None)

        # Create horizontal layout for this document (activate button + content)
        doc_horizontal_layout = QHBoxLayout()
        all_docs_layout.addLayout(doc_horizontal_layout)

        # Create thumbnail section
        self._create_thumbnail_section(
            index, doc_name, doc_path, thumbnail, opened, thumbnail_layout
        )

        # Initialize document state
        self._initialize_document_state(doc_name, doc_path, opened)

        # Create activate button
        activate_btn = self._create_activate_button(doc_name, doc_path, opened)
        doc_header_layout = QHBoxLayout()
        doc_header_layout.addWidget(activate_btn)
        doc_horizontal_layout.addLayout(doc_header_layout, stretch=0)

        # Get and configure thumbnail for clickability if opened
        if (
            opened
            and hasattr(self, "doc_thumbnails")
            and doc_name in self.doc_thumbnails
        ):
            thumbnail_label = self.doc_thumbnails[doc_name]
            thumbnail_label.setCursor(Qt.PointingHandCursor)
            thumbnail_label.mousePressEvent = (
                lambda _, name=doc_name: self.thumbnail_clicked(name)
            )

        # Create document container for layers
        doc_container = QWidget()
        doc_level_layers_layout = QVBoxLayout(doc_container)
        doc_level_layers_layout.setContentsMargins(*DOC_CONTAINER_MARGINS)
        doc_container.setStyleSheet(
            f"border: {DOCUMENT_CONTAINER_BORDER_WIDTH}px solid {DOCUMENT_CONTAINER_BORDER_COLOR}; "
            "background-color: transparent;"
        )

        # Store the layout for this document
        self.doc_layouts[doc_name] = doc_level_layers_layout

        # Populate layer editors
        self._populate_layer_editors(
            doc_name, doc_path, svg_data, doc_level_layers_layout
        )

        # Add document container to horizontal layout
        doc_horizontal_layout.addWidget(doc_container, stretch=1)

    def _create_thumbnail_section(
        self,
        index: int,
        doc_name: str,
        doc_path: str,
        thumbnail: Optional[str],
        opened: bool,
        thumbnail_layout: QGridLayout,
    ) -> None:
        """Create thumbnail section with status label.

        Args:
            index: Document index for grid positioning
            doc_name: Name of the document
            doc_path: Full path to the document
            thumbnail: Base64 encoded thumbnail data (optional)
            opened: Whether the document is opened
            thumbnail_layout: Grid layout to add thumbnail to
        """
        # Create layout for thumbnail and status
        thumbnail_status_layout = QHBoxLayout()
        thumbnail_status_layout.setSpacing(THUMBNAIL_SPACING)
        thumbnail_status_layout.setContentsMargins(0, 0, 0, 0)

        # Create thumbnail label
        thumbnail_label = self._create_thumbnail_label(doc_name, doc_path, thumbnail)

        # Setup context menu
        self._setup_thumbnail_context_menu(thumbnail_label, doc_name, doc_path)

        # Create status label
        document_status_label = self._create_document_status_label(opened)

        # Add widgets to layout
        thumbnail_status_layout.addWidget(thumbnail_label)
        thumbnail_status_layout.addWidget(document_status_label)
        thumbnail_status_layout.addStretch()

        # Calculate grid position
        row = index // THUMBNAIL_LAYOUT_GRID_COLUMNS
        col = index % THUMBNAIL_LAYOUT_GRID_COLUMNS

        # Create container and add to grid
        thumbnail_status_container = QWidget()
        thumbnail_status_container.setLayout(thumbnail_status_layout)
        thumbnail_layout.addWidget(thumbnail_status_container, row, col)

        # Store thumbnail reference (button ref is stored in _create_activate_button)
        if not hasattr(self, "doc_thumbnails"):
            self.doc_thumbnails = {}
        self.doc_thumbnails[doc_name] = thumbnail_label

        # Store button ref placeholder (will be set when button is created)
        if not hasattr(self, "doc_buttons"):
            self.doc_buttons = {}

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
        self.socket_handler.log("📋 Story Board window opened")

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
