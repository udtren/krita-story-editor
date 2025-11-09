"""
Story Editor Configuration
Styles and settings for the text editor components
"""

from PyQt5.QtGui import QFont

# Text Editor Font Configuration
TEXT_EDITOR_FONT_FAMILY = "Segoe UI"
TEXT_EDITOR_FONT_SIZE = 11
TEXT_EDITOR_MIN_HEIGHT = 80
TEXT_EDITOR_MAX_HEIGHT = 300

# TSpan Editor Colors
TSPAN_BORDER_COLOR = "#555"
TSPAN_BACKGROUND_COLOR = "#2b2b2b"
TSPAN_TEXT_COLOR = "#ffffff"
TSPAN_FOCUS_BORDER_COLOR = "#4A9EFF"
TSPAN_SELECTION_COLOR = "#4A9EFF"
TSPAN_SELECTION_TEXT_COLOR = "#000000"

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
            border: 2px solid {TSPAN_BORDER_COLOR};
            border-radius: 4px;
            padding: 8px;
            selection-background-color: {TSPAN_SELECTION_COLOR};
            selection-color: {TSPAN_SELECTION_TEXT_COLOR};
        }}
        
        QTextEdit:focus {{
            border: 2px solid {TSPAN_FOCUS_BORDER_COLOR};
        }}
        
        QTextEdit:hover {{
            border: 2px solid #666;
        }}
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
