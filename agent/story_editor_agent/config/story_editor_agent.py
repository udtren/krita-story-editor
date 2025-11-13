"""
Story Editor Agent Configuration
Styles and settings for the Krita docker and dialogs
"""

# Dialog Configuration
DIALOG_WIDTH = 700
DIALOG_HEIGHT = 500

# Color Scheme - Dark theme with blue-white text
DIALOG_BACKGROUND_COLOR = "#1e1e1e"
DIALOG_TEXT_COLOR = "#e0f0ff"  # Blue-white
DIALOG_BORDER_COLOR = "#3a3a3a"
DIALOG_LABEL_COLOR = "#a0d0ff"  # Lighter blue-white for labels

# Font Configuration
DIALOG_FONT_FAMILY = "Courier New"
DIALOG_FONT_SIZE = 10


def get_output_dialog_stylesheet():
    """Get the stylesheet for the SVG output dialog text area"""
    return f"""
        QTextEdit {{
            font-family: '{DIALOG_FONT_FAMILY}', monospace;
            font-size: {DIALOG_FONT_SIZE}pt;
            background-color: {DIALOG_BACKGROUND_COLOR};
            color: {DIALOG_TEXT_COLOR};
            border: 2px solid {DIALOG_BORDER_COLOR};
            border-radius: 4px;
            padding: 10px;
            selection-background-color: #264f78;
            selection-color: #ffffff;
        }}
    """


def get_dialog_label_stylesheet():
    """Get the stylesheet for dialog labels"""
    return f"""
        QLabel {{
            color: {DIALOG_LABEL_COLOR};
            font-size: 11pt;
            font-weight: bold;
            padding: 5px 0px;
        }}
    """


def get_dialog_stylesheet():
    """Get the overall dialog stylesheet"""
    return f"""
        QDialog {{
            background-color: #2b2b2b;
        }}
        
        QDialogButtonBox {{
            background-color: transparent;
        }}
        
        QPushButton {{
            background-color: {DIALOG_BORDER_COLOR};
            color: {DIALOG_TEXT_COLOR};
            border: 1px solid #555;
            border-radius: 3px;
            padding: 6px 16px;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: #4a4a4a;
            border: 1px solid #666;
        }}
        
        QPushButton:pressed {{
            background-color: #2a2a2a;
        }}
    """
