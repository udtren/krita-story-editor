"""
Keyboard Shortcuts Configuration Loader
Loads shortcuts from JSON
"""

import json
import os


# Load configuration from JSON file
_config_path = os.path.join(os.path.dirname(__file__), "template.json")
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


def get_default_template_name():
    """Return the default template name for new text widgets"""
    with open(_config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("default_template_name", "")
