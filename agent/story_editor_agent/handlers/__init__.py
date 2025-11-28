"""
Handlers for different action types in the Story Editor Agent.
Each handler is responsible for processing a specific type of request.
"""
from .docs_svg_handler import handle_docs_svg_update
from .get_data_handler import handle_get_all_docs_svg_data
from .save_handler import handle_save_all_opened_docs
from .document_lifecycle import (
    handle_activate_document,
    handle_open_document,
    handle_close_document,
)
from .document_operations import (
    handle_add_from_template,
    handle_duplicate_document,
    handle_delete_document,
)

# Action handler registry
ACTION_HANDLERS = {
    "docs_svg_update": handle_docs_svg_update,
    "get_all_docs_svg_data": handle_get_all_docs_svg_data,
    "save_all_opened_docs": handle_save_all_opened_docs,
    "activate_document": handle_activate_document,
    "open_document": handle_open_document,
    "close_document": handle_close_document,
    "add_from_template": handle_add_from_template,
    "duplicate_document": handle_duplicate_document,
    "delete_document": handle_delete_document,
}

__all__ = [
    "ACTION_HANDLERS",
    "handle_docs_svg_update",
    "handle_get_all_docs_svg_data",
    "handle_save_all_opened_docs",
    "handle_activate_document",
    "handle_open_document",
    "handle_close_document",
    "handle_add_from_template",
    "handle_duplicate_document",
    "handle_delete_document",
]
