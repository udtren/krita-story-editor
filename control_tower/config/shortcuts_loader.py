"""
Keyboard Shortcuts Configuration Loader
Loads shortcuts from JSON
"""

import json
import os


# Load configuration from JSON file
_config_path = os.path.join(os.path.dirname(__file__), "shortcuts.json")
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


# Story Editor Toolbar Shortcuts
NEW_TEXT_SHORTCUT = _config["story_editor_toolbar"]["new_text"]
REFRESH_SHORTCUT = _config["story_editor_toolbar"]["refresh"]
UPDATE_KRITA_SHORTCUT = _config["story_editor_toolbar"]["update_krita"]
PIN_WINDOW_SHORTCUT = _config["story_editor_toolbar"]["pin_window"]
