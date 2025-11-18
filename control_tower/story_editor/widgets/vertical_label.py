from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt


class VerticalLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet("line-height: 20%;")

    def setText(self, text):
        # Insert newline between each character
        vertical_text = "\n".join(text)
        super().setText(vertical_text)
        self.setAlignment(Qt.AlignCenter)
