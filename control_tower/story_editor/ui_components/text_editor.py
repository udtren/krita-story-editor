"""
Text Editor UI Components Module

Contains functions for creating text editor widgets and populating layer editors.

Data Flow:
----------
1. populate_layer_editors() receives svg_data list from document
2. For each layer, parses SVG to extract text elements
3. Creates QTextEdit widget for each text element
4. Stores widgets in all_docs_text_state for tracking changes

Input Data (svg_data item):
----------------------------
{
    'layer_name': 'layer2.shapelayer',
    'layer_id': 'layer2.shapelayer',
    'svg': '''<svg width="344.76pt" height="193.56pt" viewBox="0 0 344.76 193.56">
        <text id="shape807b_0" krita:textVersion="3" transform="translate(44.52, 44.380625)"
              fill="#ffffff" stroke="#000000" style="font-size: 8;">
            MY_TEXT
        </text>
    </svg>'''
}

Processing:
-----------
1. SVG string → parse_krita_svg() → extracts text_content and element_id
2. text_content → QTextEdit widget for user editing
3. Widget stored in all_docs_text_state['doc_name']['layer_groups'][layer_id]['changes']
4. Also stored in text_edit_widgets list for find/replace functionality

Output Structure (all_docs_text_state[doc_name]['layer_groups'][layer_id]):
----------------------------------------------------------------------------
{
    'layer_name': 'layer2.shapelayer',
    'layer_id': 'layer2.shapelayer',
    'layer_shapes': [...],  # Parsed SVG shape data
    'svg_content': '<svg>...</svg>',  # Original SVG
    'changes': [
        {
            'new_text': QTextEdit,  # Widget containing edited text
            'shape_id': 'shape807b_0'  # ID from SVG
        }
    ]
}
"""

from typing import Dict, Any, List
from PyQt5.QtWidgets import QTextEdit, QHBoxLayout, QVBoxLayout

from story_editor.utils.svg_parser import parse_krita_svg
from config.story_editor_loader import (
    get_text_editor_font,
    get_tspan_editor_stylesheet,
    TEXT_EDITOR_MIN_HEIGHT,
    TEXT_EDITOR_MAX_HEIGHT,
)

# Constants
TEXT_EDITOR_HEIGHT_PADDING = 10


def create_text_editor_widget(
    doc_name: str, layer_name: str, layer_id: str, layer_shape: Dict[str, Any]
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
            max(int(doc_height) + TEXT_EDITOR_HEIGHT_PADDING, TEXT_EDITOR_MIN_HEIGHT),
            TEXT_EDITOR_MAX_HEIGHT,
        )
    )

    return text_edit


def populate_layer_editors(
    doc_name: str,
    doc_path: str,
    svg_data: List[Dict[str, Any]],
    doc_level_layers_layout: QVBoxLayout,
    all_docs_text_state: Dict[str, Any],
) -> None:
    """Populate text editors for all layers in a document.

    Args:
        doc_name: Name of the document
        doc_path: Full path to the document
        svg_data: List of layer data dictionaries
        doc_level_layers_layout: Layout to add editors to
        all_docs_text_state: Document state dictionary to update
    """
    for layer_data in svg_data:
        layer_name = layer_data.get("layer_name", "unknown")
        layer_id = layer_data.get("layer_id", "unknown")
        svg_content = layer_data.get("svg", "")

        parsed_svg_data = parse_krita_svg(doc_name, doc_path, layer_id, svg_content)

        if not parsed_svg_data["layer_shapes"]:
            continue

        all_docs_text_state[doc_name]["layer_groups"][layer_id] = {
            "layer_name": layer_name,
            "layer_id": layer_id,
            "layer_shapes": parsed_svg_data["layer_shapes"],
            "svg_content": svg_content,
            "changes": [],
        }

        # Add QTextEdit for each text element
        for layer_shape in parsed_svg_data["layer_shapes"]:
            svg_section_level_layout = QHBoxLayout()

            # Create text editor
            text_edit = create_text_editor_widget(
                doc_name, layer_name, layer_id, layer_shape
            )

            svg_section_level_layout.addWidget(text_edit)

            all_docs_text_state[doc_name]["layer_groups"][layer_id]["changes"].append(
                {
                    "new_text": text_edit,
                    "shape_id": layer_shape["element_id"],
                }
            )

            # Add to text_edit_widgets list for find/replace functionality
            all_docs_text_state[doc_name]["text_edit_widgets"].append(
                {
                    "widget": text_edit,
                    "document_name": doc_name,
                    "layer_name": layer_name,
                    "layer_id": layer_id,
                    "shape_id": layer_shape["element_id"],
                }
            )

            doc_level_layers_layout.addLayout(svg_section_level_layout)
