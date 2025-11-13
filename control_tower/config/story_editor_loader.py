"""
Story Editor Configuration Loader
Loads configuration from JSON and provides helper functions
"""

import json
import os
from PyQt5.QtGui import QFont


# Load configuration from JSON file
_config_path = os.path.join(os.path.dirname(__file__), "story_editor.json")
with open(_config_path, "r", encoding="utf-8") as f:
    _config = json.load(f)


def get_config():
    """Get the full configuration dictionary"""
    return _config


def reload_config():
    """Reload configuration from file"""
    global _config
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)


def get_text_editor_font():
    """Get the font for text editors"""
    font = QFont(
        _config["text_editor"]["font_family"], _config["text_editor"]["font_size"]
    )
    return font


def get_tspan_editor_stylesheet():
    """Get the stylesheet for TSpan text editors"""
    tspan = _config["tspan"]
    tooltip = _config["tooltip"]

    return f"""
        QTextEdit {{
            background-color: {tspan['background_color']};
            color: {tspan['text_color']};
            font-size: {tspan['font_size']}px;
            border: 2px solid {tspan['border_color']};
            border-radius: 8px;
            padding: 2px;
            selection-background-color: {tspan['selection_color']};
            selection-color: {tspan['selection_text_color']};
        }}

        QTextEdit:focus {{
            border: 2px solid {tspan['focus_border_color']};
        }}

        QToolTip {{
            background-color: {tooltip['background_color']};
            color: {tooltip['text_color']};
            border: 1px solid {tooltip['border_color']};
            padding: 5px;
            border-radius: 3px;
            font-size: 14px;
        }}
    """


def get_style_label_stylesheet():
    """Get the stylesheet for style info labels"""
    style = _config["style_label"]

    return f"""
        QLabel {{
            color: {style['color']};
            font-size: {style['font_size']}px;
            font-style: italic;
            padding: 2px;
        }}
    """


def get_text_element_header_stylesheet():
    """Get the stylesheet for text element headers"""
    header = _config["text_element_header"]

    return f"""
        QLabel {{
            font-weight: bold;
            color: {header['color']};
            font-size: {header['font_size']}px;
            padding: 5px 0px;
        }}
    """


def get_layer_header_stylesheet():
    """Get the stylesheet for layer headers"""
    header = _config["layer_header"]

    return f"""
        QLabel {{
            font-weight: bold;
            font-size: {header['font_size']}px;
            color: {header['color']};
            padding: 8px 0px;
        }}
    """


def get_group_box_stylesheet():
    """Get the stylesheet for text element group boxes"""
    group = _config["group_box"]

    return f"""
        QGroupBox {{
            border: 1px solid {group['border_color']};
            border-radius: {group['border_radius']}px;
            margin-top: {group['margin_top']}px;
            padding: {group['padding']}px;
            background-color: {group['background_color']};
        }}
        
        QGroupBox:hover {{
            border: 1px solid {group['hover_border_color']};
        }}
    """


def get_separator_stylesheet():
    """Get the stylesheet for separators between tspans"""
    sep = _config["separator"]

    return f"""
        QLabel {{
            color: {sep['color']};
            font-size: {sep['font_size']}px;
        }}
    """


def get_editor_scroll_area_stylesheet():
    """Get the stylesheet for the main editor scroll area"""
    scroll = _config["scroll_area"]

    return f"""
        QScrollArea {{
            border: 1px solid {scroll['border_color']};
            background-color: {scroll['background_color']};
        }}

        QScrollBar:vertical {{
            border: none;
            background: {scroll['scrollbar_background']};
            width: {scroll['scrollbar_width']}px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {scroll['scrollbar_handle']};
            min-height: {scroll['scrollbar_handle_min_height']}px;
            border-radius: {scroll['scrollbar_handle_border_radius']}px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {scroll['scrollbar_handle_hover']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
    """


def get_window_stylesheet():
    """Get the stylesheet for the main window"""
    return f"background-color: {_config['main_window']['background_color']};"


def get_toolbar_stylesheet():
    """Get the stylesheet for the toolbar"""
    toolbar = _config["toolbar"]
    btn = _config["find_replace_button"]

    return f"""
        QToolBar {{
            background-color: {toolbar['background_color']};
            border: none;
            padding: 2px;
        }}
        QToolButton {{
            color: {btn['color']};
            font-size: {btn['font_size']};
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
    btn = _config["activate_button"]

    return f"""
        QPushButton {{
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 2px;
            padding-right: 2px;
            font-weight: bold;
            text-align: center;
            font-size: 10pt;
            border-radius: 8px;
            color: {btn['disabled_color']};
            background-color: {btn['disabled_bg']};
        }}
    """


def get_activate_button_stylesheet():
    """Get the stylesheet for active activate buttons"""
    btn = _config["activate_button"]

    return f"""
        QPushButton {{
            text-align: center;
            padding-top: 2px;
            padding-bottom: 2px;
            padding-left: 2px;
            padding-right: 2px;
            font-weight: bold;
            font-size: 10pt;
            border-radius: 8px;
            background-color: {btn['bg']};
            color: {btn['color']};
        }}
        QPushButton:checked {{
            background-color: {btn['checked_bg']};
            color: {btn['checked_color']};
        }}
    """


def get_template_combo_stylesheet():
    """Get the stylesheet for template combo box"""
    combo = _config["template_combo"]

    return f"""
    color: {combo['color']};
    background-color: {combo['background_color']};
    """


# Export configuration values as module-level constants for backward compatibility
STORY_EDITOR_WINDOW_WIDTH = _config["window"]["width"]
STORY_EDITOR_WINDOW_HEIGHT = _config["window"]["height"]
TEXT_EDITOR_FONT_SIZE = _config["text_editor"]["font_size"]
TEXT_EDITOR_MIN_HEIGHT = _config["text_editor"]["min_height"]
TEXT_EDITOR_MAX_HEIGHT = _config["text_editor"]["max_height"]
