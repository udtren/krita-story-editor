"""
UI Components Module for Story Editor

This package contains modular UI components for the Story Editor window,
organized by functionality for better maintainability and readability.

Modules:
    - scroll_areas: Scroll area creation (thumbnail and content areas)
    - thumbnail: Thumbnail label creation and configuration
    - document: Document section builders
    - text_editor: Text editor widget creation
"""

from story_editor.ui_components.scroll_areas import (
    create_thumbnail_scroll_area,
    create_content_scroll_area,
)
from story_editor.ui_components.thumbnail import (
    create_thumbnail_label,
    create_document_status_label,
    setup_thumbnail_context_menu,
)
from story_editor.ui_components.document import (
    create_activate_button,
    create_document_section,
    create_thumbnail_section,
)
from story_editor.ui_components.text_editor import (
    create_text_editor_widget,
    populate_layer_editors,
)

__all__ = [
    # Scroll areas
    "create_thumbnail_scroll_area",
    "create_content_scroll_area",
    # Thumbnails
    "create_thumbnail_label",
    "create_document_status_label",
    "setup_thumbnail_context_menu",
    # Documents
    "create_activate_button",
    "create_document_section",
    "create_thumbnail_section",
    # Text editors
    "create_text_editor_widget",
    "populate_layer_editors",
]
