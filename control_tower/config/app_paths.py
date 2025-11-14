"""
Application Paths Manager
Handles file paths for both development and PyInstaller executable environments
"""

import os
import sys


def get_app_root():
    """
    Get the application root directory
    - When running as .exe: the directory where the .exe is located
    - When running as .py: the project root (parent of control_tower)
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        # Go up two levels: config -> control_tower -> project_root
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_resource_path(relative_path):
    """
    Get absolute path to bundled resource (images, fonts, etc.)
    This is for READ-ONLY resources inside the executable
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


def get_user_data_path():
    """
    Get the user_data directory path
    This folder sits OUTSIDE the executable and persists between runs

    Location: {app_root}/user_data/
    """
    return os.path.join(get_app_root(), "user_data")


def get_user_templates_path():
    """
    Get the persistent directory for user-created templates
    Location: {app_root}/user_data/templates/
    """
    templates_dir = os.path.join(get_user_data_path(), "templates")

    # Create directory if it doesn't exist
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    return templates_dir


def get_config_dir():
    """
    Get the config directory path
    Location: {app_root}/user_data/config/
    """
    config_dir = os.path.join(get_user_data_path(), "config")

    # Create directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    return config_dir


def get_config_path():
    """
    Get the path for the template config file (template.json)
    Location: {app_root}/user_data/config/template.json
    """
    return os.path.join(get_config_dir(), "template.json")


def get_main_window_config_path():
    """
    Get the path for the main window config file
    Location: {app_root}/user_data/config/main_window.json
    """
    return os.path.join(get_config_dir(), "main_window.json")


def get_shortcuts_config_path():
    """
    Get the path for the shortcuts config file
    Location: {app_root}/user_data/config/shortcuts.json
    """
    return os.path.join(get_config_dir(), "shortcuts.json")


def get_story_editor_config_path():
    """
    Get the path for the story editor config file
    Location: {app_root}/user_data/config/story_editor.json
    """
    return os.path.join(get_config_dir(), "story_editor.json")


def get_template_config_path():
    """
    Get the path for the template config file (alias for get_config_path)
    Location: {app_root}/user_data/config/template.json
    """
    return get_config_path()


def copy_default_configs():
    """
    Copy default config files and templates from bundled resources to user_data
    - Copies config files if they don't exist
    - Copies template files if templates folder is empty
    """
    import shutil

    config_dir = get_config_dir()
    templates_dir = get_user_templates_path()

    # Copy config files
    config_files = [
        "template.json",
        "main_window.json",
        "shortcuts.json",
        "story_editor.json"
    ]

    try:
        # Get bundled config directory
        bundled_config = get_resource_path("config")

        for config_file in config_files:
            dest_path = os.path.join(config_dir, config_file)

            # Only copy if destination doesn't exist
            if not os.path.exists(dest_path):
                src_path = os.path.join(bundled_config, config_file)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"Copied default config: {config_file}")
    except Exception:
        # If copying fails, that's okay - configs may already exist
        pass  # Silent fail - configs may already exist

    # Copy default templates if templates folder is empty
    try:
        # Check if templates directory is empty
        if not os.listdir(templates_dir):
            # Get bundled templates directory
            bundled_templates = get_resource_path(os.path.join("config", "user_templates"))

            if os.path.exists(bundled_templates):
                # Copy all .xml files from bundled templates
                for filename in os.listdir(bundled_templates):
                    if filename.endswith(".xml"):
                        src_path = os.path.join(bundled_templates, filename)
                        dest_path = os.path.join(templates_dir, filename)
                        shutil.copy2(src_path, dest_path)
                        print(f"Copied default template: {filename}")
    except Exception:
        # If copying fails, that's okay - user can create their own templates
        pass  # Silent fail


# Initialize and copy default configs on first import
copy_default_configs()
