"""
Main Window Configuration Loader
Loads configuration from JSON and provides helper functions
"""

import json
import os
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
from config.app_paths import get_main_window_config_path


# Load configuration from JSON file
_config_path = get_main_window_config_path()
try:
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
except FileNotFoundError:
    # Config doesn't exist yet, use minimal defaults
    _config = {
        "font": {
            "family": "Arial",
            "size": 10,
            "button_size": 12,
            "log_family": "Consolas",
            "log_size": 9,
        },
        "button": {"height": 40, "min_width": 100},
        "dark_palette": {
            "window": "#2b2b2b",
            "window_text": "#e0e0e0",
            "base": "#1e1e1e",
            "alternate_base": "#2b2b2b",
            "tooltip_base": "#ffffff",
            "tooltip_text": "#ffffff",
            "text": "#e0e0e0",
            "button": "#353535",
            "button_text": "#e0e0e0",
            "bright_text": "#ff0000",
            "link": "#42a5f5",
            "highlight": "#42a5f5",
            "highlighted_text": "#000000",
        },
    }


def get_config():
    """Get the full configuration dictionary"""
    return _config


def reload_config():
    """Reload configuration from file"""
    global _config
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)


def get_default_font():
    """Get the default application font"""
    font = QFont(_config["font"]["family"], _config["font"]["size"])
    return font


def get_button_font():
    """Get the font for buttons"""
    font = QFont(_config["font"]["family"], _config["font"]["button_size"])
    font.setBold(True)
    return font


def get_log_font():
    """Get the font for log output"""
    font = QFont(_config["font"]["log_family"], _config["font"]["log_size"])
    return font


def setup_dark_palette(app):
    """
    Configure dark color scheme for the application

    Args:
        app: QApplication instance
    """
    app.setStyle("Fusion")

    # Set default application font
    app.setFont(get_default_font())

    dark_palette = QPalette()
    palette_config = _config["dark_palette"]

    # Define dark colors from config
    dark_palette.setColor(QPalette.Window, QColor(palette_config["window"]))
    dark_palette.setColor(QPalette.WindowText, QColor(palette_config["window_text"]))
    dark_palette.setColor(QPalette.Base, QColor(palette_config["base"]))
    dark_palette.setColor(
        QPalette.AlternateBase, QColor(palette_config["alternate_base"])
    )
    dark_palette.setColor(QPalette.ToolTipBase, QColor(palette_config["tooltip_base"]))
    dark_palette.setColor(QPalette.ToolTipText, QColor(palette_config["tooltip_text"]))
    dark_palette.setColor(QPalette.Text, QColor(palette_config["text"]))
    dark_palette.setColor(QPalette.Button, QColor(palette_config["button"]))
    dark_palette.setColor(QPalette.ButtonText, QColor(palette_config["button_text"]))
    dark_palette.setColor(QPalette.BrightText, QColor(palette_config["bright_text"]))
    dark_palette.setColor(QPalette.Link, QColor(palette_config["link"]))
    dark_palette.setColor(QPalette.Highlight, QColor(palette_config["highlight"]))
    dark_palette.setColor(
        QPalette.HighlightedText, QColor(palette_config["highlighted_text"])
    )

    app.setPalette(dark_palette)
