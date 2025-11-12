"""
Template Manager
Provides a GUI for managing SVG text templates
"""

import os
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QTextEdit,
    QLabel,
    QInputDialog,
    QMessageBox,
    QFileDialog,
)
from PyQt5.QtCore import Qt


class TemplateManagerWindow(QWidget):
    """Window for managing SVG text templates"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set window flags to make it a proper popup window
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        self.template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "utils", "user_templates"
        )
        self.current_template = None
        self.init_ui()
        self.load_template_list()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Template Manager")
        self.resize(800, 600)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #414a8e;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
            }
            QPushButton {
                background-color: #9e6658;
                color: #4b281c;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b87769;
            }
            QPushButton:pressed {
                background-color: #8d5548;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            QLabel {
                color: #ecbd30;
                font-weight: bold;
            }
        """
        )

        main_layout = QHBoxLayout()

        # Left side - Template list
        left_layout = QVBoxLayout()
        left_label = QLabel("Template Files")
        left_layout.addWidget(left_label)

        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        left_layout.addWidget(self.template_list)

        # Buttons for template list operations
        list_buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add New")
        self.add_btn.clicked.connect(self.add_template)
        list_buttons_layout.addWidget(self.add_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self.rename_template)
        self.rename_btn.setEnabled(False)
        list_buttons_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_template)
        self.delete_btn.setEnabled(False)
        list_buttons_layout.addWidget(self.delete_btn)

        left_layout.addLayout(list_buttons_layout)

        # Right side - Template editor
        right_layout = QVBoxLayout()
        right_label = QLabel("Template Content")
        right_layout.addWidget(right_label)

        self.template_editor = QTextEdit()
        self.template_editor.setPlaceholderText(
            "Select a template from the list to edit, or create a new one.\n\n"
            "Template must contain:\n"
            "- SHAPE_ID: Will be replaced with unique shape ID\n"
            "- TEXT_TO_REPLACE: Will be replaced with actual text content"
        )
        right_layout.addWidget(self.template_editor)

        # Editor buttons
        editor_buttons_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_template)
        self.save_btn.setEnabled(False)
        editor_buttons_layout.addWidget(self.save_btn)

        self.revert_btn = QPushButton("Revert Changes")
        self.revert_btn.clicked.connect(self.revert_changes)
        self.revert_btn.setEnabled(False)
        editor_buttons_layout.addWidget(self.revert_btn)

        right_layout.addLayout(editor_buttons_layout)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addLayout(right_layout, stretch=2)

        self.setLayout(main_layout)

        # Connect text changed signal
        self.template_editor.textChanged.connect(self.on_text_changed)

    def load_template_list(self):
        """Load all template files from the user_templates directory"""
        self.template_list.clear()

        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            return

        # Get all .xml files
        xml_files = [f for f in os.listdir(self.template_dir) if f.endswith(".xml")]
        xml_files.sort()

        for filename in xml_files:
            self.template_list.addItem(filename)

    def on_template_selected(self, current, previous):
        """Handle template selection from the list"""
        if current is None:
            self.template_editor.clear()
            self.current_template = None
            self.save_btn.setEnabled(False)
            self.revert_btn.setEnabled(False)
            self.rename_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        filename = current.text()
        file_path = os.path.join(self.template_dir, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.template_editor.blockSignals(True)
            self.template_editor.setPlainText(content)
            self.template_editor.blockSignals(False)

            self.current_template = filename
            self.rename_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Failed to load template:\n{str(e)}"
            )

    def on_text_changed(self):
        """Handle text editor changes"""
        if self.current_template:
            self.save_btn.setEnabled(True)
            self.revert_btn.setEnabled(True)

    def add_template(self):
        """Create a new template file"""
        filename, ok = QInputDialog.getText(
            self,
            "New Template",
            "Enter template filename (without .xml):",
        )

        if not ok or not filename:
            return

        # Ensure .xml extension
        if not filename.endswith(".xml"):
            filename = filename + ".xml"

        file_path = os.path.join(self.template_dir, filename)

        # Check if file already exists
        if os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Exists",
                f"Template '{filename}' already exists.",
            )
            return

        # Create default template content
        default_content = (
            '<text id="SHAPE_ID" krita:useRichText="true" text-rendering="auto" '
            'krita:textVersion="3" transform="translate(32, 122)" '
            'fill="#000000" stroke-opacity="0" stroke="#000000" stroke-width="0" '
            'stroke-linecap="square" stroke-linejoin="bevel" kerning="none" '
            'letter-spacing="0" word-spacing="0" '
            'style="text-align: start;text-align-last: auto;font-family: Arial;font-size: 18;">'
            '<tspan x="0">TEXT_TO_REPLACE</tspan></text>'
        )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(default_content)

            self.load_template_list()

            # Select the newly created template
            items = self.template_list.findItems(filename, Qt.MatchExactly)
            if items:
                self.template_list.setCurrentItem(items[0])

            QMessageBox.information(
                self,
                "Success",
                f"Template '{filename}' created successfully.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create template:\n{str(e)}"
            )

    def rename_template(self):
        """Rename the selected template"""
        if not self.current_template:
            return

        old_name = self.current_template
        base_name = os.path.splitext(old_name)[0]

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Template",
            "Enter new template name (without .xml):",
            text=base_name,
        )

        if not ok or not new_name:
            return

        # Ensure .xml extension
        if not new_name.endswith(".xml"):
            new_name = new_name + ".xml"

        if new_name == old_name:
            return

        old_path = os.path.join(self.template_dir, old_name)
        new_path = os.path.join(self.template_dir, new_name)

        # Check if new name already exists
        if os.path.exists(new_path):
            QMessageBox.warning(
                self,
                "File Exists",
                f"Template '{new_name}' already exists.",
            )
            return

        try:
            os.rename(old_path, new_path)
            self.current_template = new_name
            self.load_template_list()

            # Select the renamed template
            items = self.template_list.findItems(new_name, Qt.MatchExactly)
            if items:
                self.template_list.setCurrentItem(items[0])

            QMessageBox.information(
                self,
                "Success",
                f"Template renamed to '{new_name}'.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to rename template:\n{str(e)}"
            )

    def delete_template(self):
        """Delete the selected template"""
        if not self.current_template:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.current_template}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        file_path = os.path.join(self.template_dir, self.current_template)

        try:
            os.remove(file_path)
            self.current_template = None
            self.template_editor.clear()
            self.load_template_list()

            QMessageBox.information(
                self,
                "Success",
                "Template deleted successfully.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to delete template:\n{str(e)}"
            )

    def save_template(self):
        """Save changes to the current template"""
        if not self.current_template:
            return

        content = self.template_editor.toPlainText()

        # Validate that template contains required placeholders
        if "SHAPE_ID" not in content:
            QMessageBox.warning(
                self,
                "Invalid Template",
                "Template must contain 'SHAPE_ID' placeholder.",
            )
            return

        if "TEXT_TO_REPLACE" not in content:
            QMessageBox.warning(
                self,
                "Invalid Template",
                "Template must contain 'TEXT_TO_REPLACE' placeholder.",
            )
            return

        file_path = os.path.join(self.template_dir, self.current_template)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.save_btn.setEnabled(False)
            self.revert_btn.setEnabled(False)

            QMessageBox.information(
                self,
                "Success",
                f"Template '{self.current_template}' saved successfully.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save template:\n{str(e)}"
            )

    def revert_changes(self):
        """Revert changes and reload the current template"""
        if not self.current_template:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Revert",
            "Discard all unsaved changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Reload the template
            items = self.template_list.findItems(
                self.current_template, Qt.MatchExactly
            )
            if items:
                self.on_template_selected(items[0], None)
            self.save_btn.setEnabled(False)
            self.revert_btn.setEnabled(False)


def show_template_manager(parent=None):
    """Show the template manager window"""
    window = TemplateManagerWindow(parent)
    window.show()
    return window
