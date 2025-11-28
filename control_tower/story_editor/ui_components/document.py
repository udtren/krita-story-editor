"""
Document UI Components Module

Contains functions for creating document sections, activate buttons, and thumbnail sections.

Data Flow:
----------
1. create_document_section() receives doc_data from all_docs_svg_data
2. Extracts: document_name, document_path, svg_data, opened, thumbnail
3. Creates:
   - Thumbnail section (via create_thumbnail_section)
   - Activate button (via create_activate_button)
   - Document state (via _initialize_document_state)
   - Text editors for all layers (via populate_layer_editors)

Input Data Structure (doc_data):
---------------------------------
{
    'document_name': 'Test001.kra',
    'document_path': 'C:\\...\\Test001.kra',
    'svg_data': [
        {
            'layer_name': 'layer2.shapelayer',
            'layer_id': 'layer2.shapelayer',
            'svg': '<svg>...</svg>'  # Contains text elements
        }
    ],
    'opened': False,  # Whether document is open in Krita
    'thumbnail': 'data:image/png;base64,...'  # Base64 PNG image
}

Output:
-------
- UI widgets added to provided layouts
- Document state initialized in editor_window.all_docs_text_state
- References stored in editor_window.doc_buttons and doc_thumbnails
"""

from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
)
from PyQt5.QtCore import Qt

from story_editor.ui_components.thumbnail import (
    create_thumbnail_label,
    create_document_status_label,
    setup_thumbnail_context_menu,
)
from story_editor.ui_components.text_editor import populate_layer_editors
from config.story_editor_loader import (
    get_activate_button_stylesheet,
    get_activate_button_disabled_stylesheet,
    get_thumbnail_layout_settings,
)

# Constants
THUMBNAIL_LABEL_WIDTH, THUMBNAIL_LAYOUT_GRID_COLUMNS = get_thumbnail_layout_settings()
ACTIVATE_BUTTON_WIDTH = 40
ACTIVATE_BUTTON_MIN_HEIGHT = 200
THUMBNAIL_SPACING = 0
DOC_CONTAINER_MARGINS = (5, 5, 5, 5)
DOCUMENT_CONTAINER_BORDER_COLOR = "#333333"
DOCUMENT_CONTAINER_BORDER_WIDTH = 2


def create_activate_button(
    doc_name: str, doc_path: str, opened: bool, editor_window
) -> QPushButton:
    """Create activate button for a document.

    Args:
        doc_name: Name of the document
        doc_path: Full path to the document
        opened: Whether the document is opened
        editor_window: The StoryEditorWindow instance (for connecting signals)

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
            lambda _checked, name=doc_name, btn=activate_btn: editor_window.activate_document(
                name, btn
            )
        )
        activate_btn.setStyleSheet(get_activate_button_stylesheet())
        activate_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    # Store button reference
    if not hasattr(editor_window, "doc_buttons"):
        editor_window.doc_buttons = {}
    editor_window.doc_buttons[doc_name] = activate_btn

    return activate_btn


def create_thumbnail_section(
    index: int,
    doc_name: str,
    doc_path: str,
    thumbnail: Optional[str],
    opened: bool,
    thumbnail_layout: QGridLayout,
    editor_window,
) -> None:
    """Create thumbnail section with status label.

    Args:
        index: Document index for grid positioning
        doc_name: Name of the document
        doc_path: Full path to the document
        thumbnail: Base64 encoded thumbnail data (optional)
        opened: Whether the document is opened
        thumbnail_layout: Grid layout to add thumbnail to
        editor_window: The StoryEditorWindow instance
    """
    # Create layout for thumbnail and status
    thumbnail_status_layout = QHBoxLayout()
    thumbnail_status_layout.setSpacing(THUMBNAIL_SPACING)
    thumbnail_status_layout.setContentsMargins(0, 0, 0, 0)

    # Create thumbnail label
    thumbnail_label = create_thumbnail_label(doc_name, doc_path, thumbnail)

    # Setup context menu
    setup_thumbnail_context_menu(thumbnail_label, doc_name, doc_path, editor_window)

    # Create status label
    document_status_label = create_document_status_label(opened)

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

    # Store thumbnail reference (button ref is stored in create_activate_button)
    if not hasattr(editor_window, "doc_thumbnails"):
        editor_window.doc_thumbnails = {}
    editor_window.doc_thumbnails[doc_name] = thumbnail_label

    # Store button ref placeholder (will be set when button is created)
    if not hasattr(editor_window, "doc_buttons"):
        editor_window.doc_buttons = {}


def create_document_section(
    index: int,
    doc_data: Dict[str, Any],
    thumbnail_layout: QGridLayout,
    all_docs_layout: QVBoxLayout,
    editor_window,
) -> None:
    """Create UI section for a single document.

    Args:
        index: Document index for grid positioning
        doc_data: Document data dictionary
        thumbnail_layout: Grid layout for thumbnails
        all_docs_layout: Vertical layout for document content
        editor_window: The StoryEditorWindow instance
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
    create_thumbnail_section(
        index, doc_name, doc_path, thumbnail, opened, thumbnail_layout, editor_window
    )

    # Initialize document state
    _initialize_document_state(doc_name, doc_path, opened, editor_window)

    # Create activate button
    activate_btn = create_activate_button(doc_name, doc_path, opened, editor_window)
    doc_header_layout = QHBoxLayout()
    doc_header_layout.addWidget(activate_btn)
    doc_horizontal_layout.addLayout(doc_header_layout, stretch=0)

    # Get and configure thumbnail for clickability if opened
    if (
        opened
        and hasattr(editor_window, "doc_thumbnails")
        and doc_name in editor_window.doc_thumbnails
    ):
        thumbnail_label = editor_window.doc_thumbnails[doc_name]
        thumbnail_label.setCursor(Qt.PointingHandCursor)
        thumbnail_label.mousePressEvent = (
            lambda _, name=doc_name: editor_window.thumbnail_clicked(name)
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
    editor_window.doc_layouts[doc_name] = doc_level_layers_layout

    # Populate layer editors
    populate_layer_editors(
        doc_name,
        doc_path,
        svg_data,
        doc_level_layers_layout,
        editor_window.all_docs_text_state,
    )

    # Add document container to horizontal layout
    doc_horizontal_layout.addWidget(doc_container, stretch=1)


def _initialize_document_state(
    doc_name: str, doc_path: str, opened: bool, editor_window
) -> None:
    """Initialize state tracking for a document.

    Args:
        doc_name: Name of the document
        doc_path: Full path to the document
        opened: Whether the document is opened
        editor_window: The StoryEditorWindow instance
    """
    editor_window.all_docs_text_state[doc_name] = {
        "document_name": doc_name,
        "document_path": doc_path,
        "has_text_changes": False,
        "new_text_widgets": [],
        "layer_groups": {},
        "opened": opened,
        "text_edit_widgets": [],
    }
