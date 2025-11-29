"""
Scroll Area Creation Module

Contains functions for creating scroll areas for thumbnails and document content.
"""

from typing import Tuple
from PyQt5.QtWidgets import QWidget, QScrollArea, QGridLayout, QVBoxLayout
from PyQt5.QtCore import Qt

# Import constants from parent module
from config.story_editor_loader import get_thumbnail_layout_settings

THUMBNAIL_LABEL_WIDTH, THUMBNAIL_LAYOUT_GRID_COLUMNS = get_thumbnail_layout_settings()
DOCUMENT_STATUS_LABEL_WIDTH = 24
THUMBNAIL_SCROLL_AREA_WIDTH = (
    THUMBNAIL_LABEL_WIDTH + DOCUMENT_STATUS_LABEL_WIDTH + 15
) * THUMBNAIL_LAYOUT_GRID_COLUMNS

THUMBNAIL_MARGINS = 0
CONTENT_LAYOUT_MARGINS = (0, 0, 15, 0)


def create_thumbnail_scroll_area(editor_window) -> Tuple[QScrollArea, QGridLayout]:
    """Create scroll area for document thumbnails.

    Args:
        editor_window: The StoryEditorWindow instance (for storing reference)

    Returns:
        Tuple of (scroll_area, thumbnail_layout)
    """
    thumbnail_scroll_area = QScrollArea()
    thumbnail_scroll_area.setWidgetResizable(True)
    thumbnail_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    thumbnail_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    thumbnail_scroll_area.setFrameShape(QScrollArea.NoFrame)
    thumbnail_scroll_area.setMaximumWidth(THUMBNAIL_SCROLL_AREA_WIDTH)
    thumbnail_scroll_area.verticalScrollBar().setStyleSheet(
        """
        QScrollBar:vertical {
            border: 1px solid black;
            width: 15px;
        }
        QScrollBar::handle:vertical {
            border: 1px solid black;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
    )

    # Create container widget for thumbnails
    thumbnail_container = QWidget()
    thumbnail_layout = QGridLayout(thumbnail_container)
    thumbnail_layout.setContentsMargins(
        THUMBNAIL_MARGINS, THUMBNAIL_MARGINS, THUMBNAIL_MARGINS, THUMBNAIL_MARGINS
    )

    # Set the container as scroll area's widget
    thumbnail_scroll_area.setWidget(thumbnail_container)

    # Store reference for saving position later
    editor_window.thumbnail_scroll_area_widget = thumbnail_scroll_area

    return thumbnail_scroll_area, thumbnail_layout


def create_content_scroll_area(editor_window) -> Tuple[QScrollArea, QVBoxLayout]:
    """Create scroll area for all documents' content.

    Args:
        editor_window: The StoryEditorWindow instance (for storing reference)

    Returns:
        Tuple of (scroll_area, all_docs_layout)
    """
    all_docs_scroll_area = QScrollArea()
    all_docs_scroll_area.setWidgetResizable(True)
    all_docs_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    all_docs_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    all_docs_scroll_area.setFrameShape(QScrollArea.NoFrame)
    all_docs_scroll_area.verticalScrollBar().setStyleSheet(
        """
        QScrollBar:vertical {
            border: 1px solid black;
            width: 15px;
        }
        QScrollBar::handle:vertical {
            border: 1px solid black;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
    )

    # Create container widget for all documents
    all_docs_container = QWidget()
    all_docs_layout = QVBoxLayout(all_docs_container)
    all_docs_layout.setContentsMargins(*CONTENT_LAYOUT_MARGINS)

    # Set the container as scroll area's widget
    all_docs_scroll_area.setWidget(all_docs_container)

    # Store reference for saving position later
    editor_window.all_docs_scroll_area_widget = all_docs_scroll_area

    return all_docs_scroll_area, all_docs_layout
