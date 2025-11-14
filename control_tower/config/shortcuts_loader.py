"""
Keyboard Shortcuts Configuration Loader
Loads shortcuts from JSON
"""

import json
import os
from config.app_paths import get_shortcuts_config_path


# Load configuration from JSON file
_config_path = get_shortcuts_config_path()
try:
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
except FileNotFoundError:
    # Config doesn't exist yet, use defaults
    _config = {
        "story_editor_toolbar": {
            "new_text": "Ctrl+N",
            "refresh": "Ctrl+R",
            "update_krita": "Ctrl+S",
            "pin_window": "Ctrl+P"
        }
    }


def get_config():
    """Get the full configuration dictionary"""
    return _config


def reload_config():
    """Reload configuration from file"""
    global _config
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)


# Story Editor Toolbar Shortcuts
NEW_TEXT_SHORTCUT = _config["story_editor_toolbar"]["new_text"]
REFRESH_SHORTCUT = _config["story_editor_toolbar"]["refresh"]
UPDATE_KRITA_SHORTCUT = _config["story_editor_toolbar"]["update_krita"]
PIN_WINDOW_SHORTCUT = _config["story_editor_toolbar"]["pin_window"]
