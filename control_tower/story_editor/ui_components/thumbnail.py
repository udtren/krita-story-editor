"""
Thumbnail UI Components Module

Contains functions for creating and configuring thumbnail-related widgets.

Data Flow:
----------
1. create_thumbnail_label() receives thumbnail data from doc_data
2. Decodes base64 PNG image
3. Scales to fit THUMBNAIL_LABEL_WIDTH
4. Creates QLabel with image or placeholder

Input Data (thumbnail field from doc_data):
--------------------------------------------
'thumbnail': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...'

Format: Data URI with base64-encoded PNG image
- Prefix: 'data:image/png;base64,'
- Encoded image data follows

Processing:
-----------
1. Remove data URI prefix if present
2. base64.b64decode() → raw image bytes
3. QPixmap.loadFromData() → create image
4. pixmap.scaledToWidth() → resize maintaining aspect ratio
5. QLabel.setPixmap() → display in UI

Status Label:
-------------
create_document_status_label() creates a vertical label showing:
- "opened" (green) if document is open in Krita
- "closed" (gray) if document is not open

This helps users know which documents they can edit/save.
"""

import base64
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QPixmap

from story_editor.widgets.vertical_label import VerticalLabel
from config.story_editor_loader import (
    get_thumbnail_status_label_stylesheet,
    get_thumbnail_status_label_disabled_stylesheet,
    get_thumbnail_layout_settings,
)

# Constants
THUMBNAIL_LABEL_WIDTH, _ = get_thumbnail_layout_settings()
DOCUMENT_STATUS_LABEL_WIDTH = 24
THUMBNAIL_BORDER_DEFAULT = "#555"
THUMBNAIL_BORDER_ACTIVE = "#aaa"
THUMBNAIL_BACKGROUND_COLOR = "#aa805a"
DOCUMENT_CONTAINER_BORDER_WIDTH = 2


def decode_base64_thumbnail(thumbnail_data: str) -> QPixmap:
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


def create_thumbnail_label(
    doc_name: str, doc_path: str, thumbnail: Optional[str]
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
            pixmap = decode_base64_thumbnail(thumbnail)

            # Scale pixmap to width while maintaining aspect ratio
            pixmap = pixmap.scaledToWidth(THUMBNAIL_LABEL_WIDTH, Qt.SmoothTransformation)
            thumbnail_label.setPixmap(pixmap)
            # Set label size to match the scaled pixmap
            thumbnail_label.setFixedSize(pixmap.size())

            # Set tooltip with document info
            thumbnail_label.setToolTip(f"Document: {doc_name}\nPath: {doc_path}")
        except Exception:
            # If loading fails, show placeholder text
            thumbnail_label.setText("No\nPreview")
            thumbnail_label.setAlignment(Qt.AlignCenter)
    else:
        # No thumbnail available
        thumbnail_label.setText("No\nPreview")
        thumbnail_label.setAlignment(Qt.AlignCenter)

    return thumbnail_label


def create_document_status_label(opened: bool) -> VerticalLabel:
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


def setup_thumbnail_context_menu(
    thumbnail_label: QLabel,
    doc_name: str,
    doc_path: str,
    editor_window,
) -> None:
    """Setup context menu for thumbnail label.

    Args:
        thumbnail_label: The thumbnail label widget
        doc_name: Name of the document
        doc_path: Full path to the document
        editor_window: The StoryEditorWindow instance (for accessing comic_config_info)
    """
    thumbnail_label.setContextMenuPolicy(Qt.CustomContextMenu)
    thumbnail_label.customContextMenuRequested.connect(
        lambda pos: editor_window.show_thumbnail_context_menu(
            pos, doc_name, thumbnail_label, doc_path, editor_window.comic_config_info
        )
    )
