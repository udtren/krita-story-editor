"""
Find and Replace Dialog for Story Editor
Provides find and replace functionality for all text editors in the window
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QRegularExpression
from PyQt5.QtGui import QTextCursor


class FindReplaceDialog(QDialog):
    """Dialog for finding and replacing text across all text editors"""

    def __init__(self, parent, text_edit_widgets):
        """
        Initialize the find/replace dialog

        Args:
            parent: The parent widget
            text_edit_widgets: List of dictionaries containing text edit widget info
                              Each dict has 'widget', 'document_name', 'layer_name', etc.
        """
        super().__init__(parent)
        self.text_edit_widgets = text_edit_widgets
        self.current_matches = []
        self.current_match_index = -1
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Find and Replace")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Find section
        find_layout = QHBoxLayout()
        find_label = QLabel("Find:")
        find_label.setFixedWidth(100)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Enter text to find...")
        self.find_input.textChanged.connect(self.on_find_text_changed)
        find_layout.addWidget(find_label)
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)

        # Replace section
        replace_layout = QHBoxLayout()
        replace_label = QLabel("Replace:")
        replace_label.setFixedWidth(100)
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Enter replacement text...")
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)

        # Options
        options_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        self.whole_word_cb = QCheckBox("Whole Words Only")
        self.use_regex_cb = QCheckBox("Use Regular Expression")
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        options_layout.addWidget(self.use_regex_cb)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "color: #323232; font-style: italic; background-color: #7d7d7d;"
        )
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.find_next_btn = QPushButton("Find Next")
        self.find_next_btn.clicked.connect(self.find_next)
        button_layout.addWidget(self.find_next_btn)

        self.find_prev_btn = QPushButton("Find Previous")
        self.find_prev_btn.clicked.connect(self.find_previous)
        button_layout.addWidget(self.find_prev_btn)

        self.replace_btn = QPushButton("Replace")
        self.replace_btn.clicked.connect(self.replace_current)
        button_layout.addWidget(self.replace_btn)

        self.replace_all_btn = QPushButton("Replace All")
        self.replace_all_btn.clicked.connect(self.replace_all)
        button_layout.addWidget(self.replace_all_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Close button
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        # Set stylesheet
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #b9ae93;
                font-size: 18px;
                padding: 5px 5px;
            }
            QLineEdit {
                background-color: #333333;
                color: #c5c5c5;
                font-size: 24px;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #4A9EFF;
            }
            QPushButton {
                background-color: #444;
                color: #b9ae93;
                font-size: 18px;
                border: 1px solid #555;
                padding: 5px 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
            QCheckBox {
                color: #b9ae93;
                font-size: 18px;
                padding: 5px 5px;
            }
        """
        )

    def on_find_text_changed(self, text):
        """Called when find text changes - reset search"""
        self.current_matches = []
        self.current_match_index = -1
        if text:
            self.find_all_matches()

    def find_all_matches(self):
        """Find all matches across all text editors"""
        self.current_matches = []
        find_text = self.find_input.text()

        if not find_text:
            self.status_label.setText("")
            return

        for widget_info in self.text_edit_widgets:
            widget = widget_info.get("widget")
            if not widget:
                continue

            text = widget.toPlainText()

            if self.use_regex_cb.isChecked():
                # Use regular expression
                flags = (
                    0
                    if self.case_sensitive_cb.isChecked()
                    else QRegularExpression.CaseInsensitiveOption
                )
                regex = QRegularExpression(find_text)
                if flags:
                    regex.setPatternOptions(flags)

                match_iter = regex.globalMatch(text)
                while match_iter.hasNext():
                    match = match_iter.next()
                    self.current_matches.append(
                        {
                            "widget": widget,
                            "widget_info": widget_info,
                            "start": match.capturedStart(),
                            "length": match.capturedLength(),
                        }
                    )
            else:
                # Simple text search
                search_text = (
                    find_text
                    if self.case_sensitive_cb.isChecked()
                    else find_text.lower()
                )
                compare_text = (
                    text if self.case_sensitive_cb.isChecked() else text.lower()
                )

                start = 0
                while True:
                    pos = compare_text.find(search_text, start)
                    if pos == -1:
                        break

                    # Check whole word option
                    if self.whole_word_cb.isChecked():
                        # Check if it's a whole word
                        before_ok = pos == 0 or not text[pos - 1].isalnum()
                        after_ok = (pos + len(find_text)) >= len(text) or not text[
                            pos + len(find_text)
                        ].isalnum()
                        if not (before_ok and after_ok):
                            start = pos + 1
                            continue

                    self.current_matches.append(
                        {
                            "widget": widget,
                            "widget_info": widget_info,
                            "start": pos,
                            "length": len(find_text),
                        }
                    )
                    start = pos + 1

        # Update status
        count = len(self.current_matches)
        if count == 0:
            self.status_label.setText("No matches found")
        else:
            self.status_label.setText(
                f"Found {count} match{'es' if count != 1 else ''}"
            )

    def find_next(self):
        """Find and highlight the next match"""
        if not self.current_matches:
            self.find_all_matches()

        if not self.current_matches:
            self.status_label.setText("No matches found")
            return

        self.current_match_index = (self.current_match_index + 1) % len(
            self.current_matches
        )
        self.highlight_current_match()

    def find_previous(self):
        """Find and highlight the previous match"""
        if not self.current_matches:
            self.find_all_matches()

        if not self.current_matches:
            self.status_label.setText("No matches found")
            return

        self.current_match_index = (self.current_match_index - 1) % len(
            self.current_matches
        )
        self.highlight_current_match()

    def highlight_current_match(self):
        """Highlight the current match in the text editor"""
        if self.current_match_index < 0 or self.current_match_index >= len(
            self.current_matches
        ):
            return

        match = self.current_matches[self.current_match_index]
        widget = match["widget"]
        widget_info = match["widget_info"]

        # Update status
        self.status_label.setText(
            f"Match {self.current_match_index + 1} of {len(self.current_matches)} "
            f"(Document: {widget_info.get('document_name', 'unknown')})"
        )

        # Set cursor to the match position
        cursor = widget.textCursor()
        cursor.setPosition(match["start"])
        cursor.setPosition(match["start"] + match["length"], QTextCursor.KeepAnchor)
        widget.setTextCursor(cursor)

        # Ensure the widget is visible and has focus
        widget.setFocus()
        widget.ensureCursorVisible()

    def replace_current(self):
        """Replace the current match"""
        if self.current_match_index < 0 or self.current_match_index >= len(
            self.current_matches
        ):
            self.status_label.setText("No match selected")
            return

        match = self.current_matches[self.current_match_index]
        widget = match["widget"]
        replace_text = self.replace_input.text()

        # Replace the text
        cursor = widget.textCursor()
        cursor.setPosition(match["start"])
        cursor.setPosition(match["start"] + match["length"], QTextCursor.KeepAnchor)
        cursor.insertText(replace_text)

        # Refresh matches as positions have changed
        self.current_matches = []
        self.current_match_index = -1
        self.find_all_matches()

        # Move to next match if available
        if self.current_matches:
            self.find_next()
        else:
            self.status_label.setText("Replaced. No more matches.")

    def replace_all(self):
        """Replace all matches"""
        if not self.current_matches:
            self.find_all_matches()

        if not self.current_matches:
            self.status_label.setText("No matches to replace")
            return

        count = len(self.current_matches)
        replace_text = self.replace_input.text()

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Replace All",
            f"Replace all {count} occurrence{'s' if count != 1 else ''}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Replace all matches (work backwards to avoid position shifting issues)
        for match in reversed(self.current_matches):
            widget = match["widget"]
            cursor = widget.textCursor()
            cursor.setPosition(match["start"])
            cursor.setPosition(match["start"] + match["length"], QTextCursor.KeepAnchor)
            cursor.insertText(replace_text)

        self.status_label.setText(
            f"Replaced {count} occurrence{'s' if count != 1 else ''}"
        )

        # Refresh matches
        self.current_matches = []
        self.current_match_index = -1
        self.find_all_matches()


def show_find_replace_dialog(parent, all_docs_text_state):
    """
    Show the find/replace dialog

    Args:
        parent: The parent widget
        all_docs_text_state: Dictionary containing all document text state
                            Format: {doc_name: {'text_edit_widgets': [...]}}
    """
    # Collect all text edit widgets from all documents
    all_text_widgets = []
    for doc_name, doc_state in all_docs_text_state.items():
        all_text_widgets.extend(doc_state.get("text_edit_widgets", []))

    # Create and show the dialog
    dialog = FindReplaceDialog(parent, all_text_widgets)
    dialog.exec_()
