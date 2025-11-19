"""
Template Configuration Loader
Loads template configuration from JSON
"""

import json
import os
from config.app_paths import get_template_config_path


# Load configuration from JSON file
_config_path = get_template_config_path()
try:
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
except FileNotFoundError:
    # Config doesn't exist yet, use defaults
    _config = {"default_template_name": ""}


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
    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("default_template_name", "")
    except FileNotFoundError:
        return ""


def get_default_svg_template_name():
    """Return the default SVG template name for new SVG text widgets"""
    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("default_svg_template_name", "")
    except FileNotFoundError:
        return ""
