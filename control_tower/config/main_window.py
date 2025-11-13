from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt


# Window Configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Story Editor Control Tower"

# Font Configuration
FONT_FAMILY = "Segoe UI"  # Use system default on Windows
FONT_SIZE = 12
BUTTON_FONT_SIZE = 11
LOG_FONT_SIZE = 10

# Button Configuration
BUTTON_HEIGHT = 40
BUTTON_MIN_WIDTH = 150


def get_default_font():
    """Get the default application font"""
    font = QFont(FONT_FAMILY, FONT_SIZE)
    return font


def get_button_font():
    """Get the font for buttons"""
    font = QFont(FONT_FAMILY, BUTTON_FONT_SIZE)
    font.setBold(True)
    return font


def get_log_font():
    """Get the font for log output"""
    font = QFont("Consolas", LOG_FONT_SIZE)  # Monospace font for logs
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
    
    # Define dark colors
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(dark_palette)

