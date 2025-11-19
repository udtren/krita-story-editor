"""
New Text Widget Management
Handles adding new text widgets to the Story Editor
"""

from PyQt5.QtWidgets import QTextEdit, QComboBox, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
import os
import glob
from config.story_editor_loader import (
    get_text_editor_font,
    get_tspan_editor_stylesheet,
    get_template_combo_stylesheet,
    TEXT_EDITOR_MIN_HEIGHT,
    TEXT_EDITOR_MAX_HEIGHT,
)
from config.template_loader import (
    get_default_template_name,
    get_default_svg_template_name,
)
from config.app_paths import get_user_templates_path, get_svg_templates_path


def add_new_text_widget(
    active_doc_name,
    doc_layouts,
    all_docs_text_state,
    socket_handler,
):
    """
    Add a new empty text editor widget for creating new text

    Args:
        active_doc_name: Name of the currently active document
        doc_layouts: Dictionary of document layouts {doc_name: layout}
        all_docs_text_state: Dictionary containing all document states
        socket_handler: Object with send_request and log methods

    Returns:
        True if widget was added successfully, False otherwise
    """
    # Check if a document is active
    if not active_doc_name or active_doc_name not in doc_layouts:
        socket_handler.log(
            "No active document. Please click on a document name to activate it first."
        )
        return False

    # Get the active document's layout
    active_layout = doc_layouts[active_doc_name]
    placeholder_text = """If you want multiple paragraphs within different text elements, separate them with triple line breaks."""

    # Create new layout for this text element
    svg_section_level_layout = QHBoxLayout()

    # Create the text editor
    text_edit = QTextEdit()
    text_edit.setPlainText("")
    text_edit.setPlaceholderText(placeholder_text)
    text_edit.setFont(get_text_editor_font())
    text_edit.setStyleSheet(get_tspan_editor_stylesheet())
    text_edit.setMaximumHeight(TEXT_EDITOR_MAX_HEIGHT)
    text_edit.setMinimumHeight(TEXT_EDITOR_MIN_HEIGHT)

    svg_section_level_layout.addWidget(text_edit)

    template_section_layout = QVBoxLayout()

    # Create template selector combo box
    svg_template_label = QLabel("SVG Template:")
    svg_template_label.setStyleSheet(
        "color: #000000; border: none; background: transparent;"
    )
    choose_svg_template_combo = QComboBox()
    choose_svg_template_combo.setMinimumWidth(200)
    choose_svg_template_combo.setMaximumWidth(400)
    choose_svg_template_combo.setStyleSheet(get_template_combo_stylesheet())

    template_label = QLabel("Text Template:")
    template_label.setStyleSheet(
        "color: #000000; border: none;background: transparent;"
    )
    choose_template_combo = QComboBox()
    choose_template_combo.setMinimumWidth(200)
    choose_template_combo.setMaximumWidth(400)
    choose_template_combo.setStyleSheet(get_template_combo_stylesheet())

    template_section_layout.addWidget(svg_template_label)
    template_section_layout.addWidget(choose_svg_template_combo)
    template_section_layout.addWidget(template_label)
    template_section_layout.addWidget(choose_template_combo)
    template_section_layout.addStretch()

    # ===================================================
    # Find all XML files in svg_templates directory
    # ===================================================
    svg_template_dir = get_svg_templates_path()
    svg_template_files = []

    if os.path.exists(svg_template_dir):
        # Get all .xml files
        xml_files = glob.glob(os.path.join(svg_template_dir, "*.xml"))
        for xml_file in sorted(xml_files):
            # Get just the filename without path
            filename = os.path.basename(xml_file)
            svg_template_files.append((filename, xml_file))
            choose_svg_template_combo.addItem(filename, xml_file)
    if not svg_template_files:
        socket_handler.log(f"No template files found in {svg_template_dir}")

    # Set default selection
    default_svg_template_name = get_default_svg_template_name()
    default_index = choose_svg_template_combo.findText(default_svg_template_name)
    if default_index >= 0:
        choose_svg_template_combo.setCurrentIndex(default_index)

    # ===================================================
    # Find all XML files in user_templates directory
    # ===================================================

    template_dir = get_user_templates_path()
    template_files = []

    if os.path.exists(template_dir):
        # Get all .xml files
        xml_files = glob.glob(os.path.join(template_dir, "*.xml"))
        for xml_file in sorted(xml_files):
            # Get just the filename without path
            filename = os.path.basename(xml_file)
            template_files.append((filename, xml_file))
            choose_template_combo.addItem(filename, xml_file)

    if not template_files:
        socket_handler.log(f"No template files found in {template_dir}")

    # Set default selection
    default_template_name = get_default_template_name()
    default_index = choose_template_combo.findText(default_template_name)
    if default_index >= 0:
        choose_template_combo.setCurrentIndex(default_index)

    # ===================================================

    svg_section_level_layout.addLayout(template_section_layout)

    # Add to the ACTIVE document's layout
    active_layout.addLayout(svg_section_level_layout)
    active_layout.setAlignment(svg_section_level_layout, Qt.AlignTop)

    # Store reference with metadata marking it as new
    all_docs_text_state[active_doc_name]["new_text_widgets"].append(
        {
            "widget": text_edit,
            "is_new": True,  # Flag to identify new text
            "document_name": active_doc_name,  # Store which document this belongs to
            "template_combo": choose_template_combo,  # Store reference to combo box
            "svg_template_combo": choose_svg_template_combo,
            "original_text": "",
        }
    )

    socket_handler.log(f"Added new text widget to '{active_doc_name}' document.")
    return True
