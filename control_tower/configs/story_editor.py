"""
Story Editor Configuration
Styles and settings for the text editor components
"""

from PyQt5.QtGui import QFont

# Story Editor Window Configuration
STORY_EDITOR_WINDOW_WIDTH = 1200
STORY_EDITOR_WINDOW_HEIGHT = 1800

# Text Editor Font Configuration
TEXT_EDITOR_FONT_FAMILY = "Segoe UI"
TEXT_EDITOR_FONT_SIZE = 11
TEXT_EDITOR_MIN_HEIGHT = 80
TEXT_EDITOR_MAX_HEIGHT = 300

# TSpan Editor Colors
TSPAN_FONT_SIZE = 24
TSPAN_BORDER_COLOR = "#595959"
TSPAN_BACKGROUND_COLOR = "#333333"
TSPAN_TEXT_COLOR = "#9C9C9C"
TSPAN_FOCUS_BORDER_COLOR = "#8c8c8c"
TSPAN_SELECTION_COLOR = "#4A9EFF"
TSPAN_SELECTION_TEXT_COLOR = "#C5C5C5"

# Style Label Colors
STYLE_LABEL_COLOR = "#888"
STYLE_LABEL_FONT_SIZE = 10

# Text Element Header Colors
TEXT_ELEMENT_HEADER_COLOR = "#4A9EFF"
TEXT_ELEMENT_HEADER_FONT_SIZE = 12

# Layer Header Colors
LAYER_HEADER_COLOR = "#FFD700"
LAYER_HEADER_FONT_SIZE = 14

# Group Box Styling
GROUP_BOX_BORDER_COLOR = "#555"
GROUP_BOX_BORDER_RADIUS = 5
GROUP_BOX_MARGIN_TOP = 10
GROUP_BOX_PADDING = 10

# Separator Color
SEPARATOR_COLOR = "#555"

# Window Background Color
WINDOW_BACKGROUND_COLOR = "#81623f"

# Toolbar Colors
TOOLBAR_BACKGROUND_COLOR = "#8e764e"

# Activate Button Colors
ACTIVATE_BTN_DISABLED_COLOR = "#A0A0A0"
ACTIVATE_BTN_DISABLED_BG = "#242424"
ACTIVATE_BTN_BG = "#69462d"
ACTIVATE_BTN_COLOR = "#393939"
ACTIVATE_BTN_CHECKED_BG = "#a5a5a5"
ACTIVATE_BTN_CHECKED_COLOR = "#393939"

# Template Combo Box Color
TEMPLATE_COMBO_COLOR = "black"

# Find/Replace Button Colors
FIND_REPLACE_BTN_COLOR = "#221c13"
FIND_REPLACE_BTN_FONT_SIZE = "18px"


def get_text_editor_font():
    """Get the font for text editors"""
    font = QFont(TEXT_EDITOR_FONT_FAMILY, TEXT_EDITOR_FONT_SIZE)
    return font


def get_tspan_editor_stylesheet():
    """Get the stylesheet for TSpan text editors"""
    return f"""
        QTextEdit {{
            background-color: {TSPAN_BACKGROUND_COLOR};
            color: {TSPAN_TEXT_COLOR};
            font-size: {TSPAN_FONT_SIZE}px;
            border: 2px solid {TSPAN_BORDER_COLOR};
            border-radius: 2px;
            padding: 2px;
            selection-background-color: {TSPAN_SELECTION_COLOR};
            selection-color: {TSPAN_SELECTION_TEXT_COLOR};
        }}
        
        QTextEdit:focus {{
            border: 2px solid {TSPAN_FOCUS_BORDER_COLOR};
        }}
        
        # QTextEdit:hover {{
        #     border: 2px solid #666;
        # }}
    """


def get_style_label_stylesheet():
    """Get the stylesheet for style info labels"""
    return f"""
        QLabel {{
            color: {STYLE_LABEL_COLOR};
            font-size: {STYLE_LABEL_FONT_SIZE}px;
            font-style: italic;
            padding: 2px;
        }}
    """


def get_text_element_header_stylesheet():
    """Get the stylesheet for text element headers"""
    return f"""
        QLabel {{
            font-weight: bold;
            color: {TEXT_ELEMENT_HEADER_COLOR};
            font-size: {TEXT_ELEMENT_HEADER_FONT_SIZE}px;
            padding: 5px 0px;
        }}
    """


def get_layer_header_stylesheet():
    """Get the stylesheet for layer headers"""
    return f"""
        QLabel {{
            font-weight: bold;
            font-size: {LAYER_HEADER_FONT_SIZE}px;
            color: {LAYER_HEADER_COLOR};
            padding: 8px 0px;
        }}
    """


def get_group_box_stylesheet():
    """Get the stylesheet for text element group boxes"""
    return f"""
        QGroupBox {{
            border: 1px solid {GROUP_BOX_BORDER_COLOR};
            border-radius: {GROUP_BOX_BORDER_RADIUS}px;
            margin-top: {GROUP_BOX_MARGIN_TOP}px;
            padding: {GROUP_BOX_PADDING}px;
            background-color: #1e1e1e;
        }}
        
        QGroupBox:hover {{
            border: 1px solid #666;
        }}
    """


def get_separator_stylesheet():
    """Get the stylesheet for separators between tspans"""
    return f"""
        QLabel {{
            color: {SEPARATOR_COLOR};
            font-size: 10px;
        }}
    """


def get_editor_scroll_area_stylesheet():
    """Get the stylesheet for the main editor scroll area"""
    return """
        QScrollArea {
            border: 1px solid #555;
            background-color: #2b2b2b;
        }

        QScrollBar:vertical {
            border: none;
            background: #2b2b2b;
            width: 12px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #555;
            min-height: 20px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical:hover {
            background: #666;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """


def get_window_stylesheet():
    """Get the stylesheet for the main window"""
    return f"background-color: {WINDOW_BACKGROUND_COLOR};"


def get_toolbar_stylesheet():
    """Get the stylesheet for the toolbar"""
    return f"""
        QToolBar {{
            background-color: {TOOLBAR_BACKGROUND_COLOR};
            border: none;
            padding: 2px;
        }}
        QToolButton {{
            color: {FIND_REPLACE_BTN_COLOR};
            font-size: {FIND_REPLACE_BTN_FONT_SIZE};
            font-weight: bold;
            padding: 4px 8px;
            border: none;
            background-color: transparent;
        }}
        QToolButton:hover {{
            background-color: rgba(0, 0, 0, 0.1);
            border-radius: 3px;
        }}
        QToolButton:pressed {{
            background-color: rgba(0, 0, 0, 0.2);
        }}
    """


def get_activate_button_disabled_stylesheet():
    """Get the stylesheet for disabled activate buttons"""
    return f"""
        QPushButton {{
            font-style: italic;
            padding-top: 2px;
            padding-bottom: 0px;
            padding-left: 2px;
            padding-right: 2px;
            font-weight: bold;
            text-align: center;
            font-size: 10pt;
            color: {ACTIVATE_BTN_DISABLED_COLOR};
            background-color: {ACTIVATE_BTN_DISABLED_BG};
        }}
    """


def get_activate_button_stylesheet():
    """Get the stylesheet for active activate buttons"""
    return f"""
        QPushButton {{
            text-align: center;
            padding-top: 2px;
            padding-bottom: 0px;
            padding-left: 2px;
            padding-right: 2px;
            font-weight: bold;
            font-size: 10pt;
            background-color: {ACTIVATE_BTN_BG};
            color: {ACTIVATE_BTN_COLOR};
        }}
        QPushButton:checked {{
            background-color: {ACTIVATE_BTN_CHECKED_BG};
            color: {ACTIVATE_BTN_CHECKED_COLOR};
        }}
    """


def get_template_combo_stylesheet():
    """Get the stylesheet for template combo box"""
    return f"color: {TEMPLATE_COMBO_COLOR};"
