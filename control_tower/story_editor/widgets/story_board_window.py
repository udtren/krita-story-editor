import base64
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QGridLayout,
    QSizePolicy,
)
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QPixmap
from config.story_editor_loader import get_story_board_settings

STORY_BOARD_COLUMN_COUNT, STORY_BOARD_THUMBNAIL_WIDTH = get_story_board_settings()
STORY_BOARD_WINDOW_WIDTH = (
    STORY_BOARD_THUMBNAIL_WIDTH * STORY_BOARD_COLUMN_COUNT
    + STORY_BOARD_COLUMN_COUNT * 15
)


class StoryBoardWindow(QWidget):
    """Window to display all document thumbnails in a grid layout"""

    def __init__(self, all_docs_svg_data, parent=None):
        super().__init__(parent)
        self.all_docs_svg_data = all_docs_svg_data
        self.setWindowTitle("Story Board")
        self.setFixedWidth(STORY_BOARD_WINDOW_WIDTH)
        self.setStyleSheet("background-color: #2b2b2b; color: #cccccc;")

        self.init_ui()

    def init_ui(self):
        """Initialize the UI with thumbnails in a grid layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create scroll area for thumbnails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Create container widget for thumbnails
        container = QWidget()
        grid_layout = QGridLayout(container)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setSpacing(5)
        grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align items to top-left

        # Set the container as scroll area's widget
        scroll_area.setWidget(container)

        # Add thumbnails to grid
        columns = STORY_BOARD_COLUMN_COUNT
        for index, doc_data in enumerate(self.all_docs_svg_data):
            doc_name = doc_data.get("document_name", "unknown")
            doc_path = doc_data.get("document_path", "unknown")
            thumbnail = doc_data.get("thumbnail", None)
            opened = doc_data.get("opened", True)

            # Create a container for thumbnail and label
            thumb_container = QWidget()
            thumb_layout = QVBoxLayout(thumb_container)
            thumb_layout.setContentsMargins(0, 0, 0, 0)
            thumb_layout.setSpacing(5)

            # Create thumbnail label
            thumbnail_label = QLabel()
            thumbnail_label.setAlignment(Qt.AlignCenter)

            # Set border style based on opened status
            border_color = "#888" if opened else "#444"
            background_color = "#3a3a3a" if opened else "#2a2a2a"
            thumbnail_label.setStyleSheet(
                f"border: 2px solid {border_color}; "
                f"background-color: {background_color}; "
                f"padding: 5px;"
            )
            thumbnail_label.setFixedWidth(STORY_BOARD_THUMBNAIL_WIDTH)

            # Load thumbnail from base64 data if available
            if thumbnail:
                try:
                    # Remove the data URI prefix if present
                    if thumbnail.startswith("data:image"):
                        thumbnail_data = thumbnail.split(",", 1)[1]
                    else:
                        thumbnail_data = thumbnail

                    # Decode base64 to bytes
                    image_bytes = base64.b64decode(thumbnail_data)

                    # Create QPixmap from bytes
                    pixmap = QPixmap()
                    pixmap.loadFromData(QByteArray(image_bytes))
                    pixmap = pixmap.scaledToWidth(
                        STORY_BOARD_THUMBNAIL_WIDTH, Qt.SmoothTransformation
                    )

                    # Display original size thumbnail
                    thumbnail_label.setPixmap(pixmap)
                    thumbnail_label.setToolTip(
                        f"Document: {doc_name}\nPath: {doc_path}\nSize: {pixmap.width()}x{pixmap.height()}"
                    )
                except Exception as e:
                    # If loading fails, show placeholder text
                    thumbnail_label.setText("No Preview Available")
                    thumbnail_label.setMinimumSize(200, 150)
            else:
                # No thumbnail available
                thumbnail_label.setText("No Preview Available")
                thumbnail_label.setMinimumSize(200, 150)

            # Create document name label
            name_label = QLabel(doc_name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("color: #cccccc; font-size: 11px; padding: 3px;")
            name_label.setWordWrap(True)

            # Add status indicator
            status_text = "✓ Opened" if opened else "✗ Closed"
            status_color = "#6a6" if opened else "#a66"
            status_label = QLabel(status_text)
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet(
                f"color: {status_color}; font-size: 10px; padding: 2px;"
            )

            # Add widgets to container
            thumb_layout.addWidget(thumbnail_label)
            thumb_layout.addWidget(name_label)
            # thumb_layout.addWidget(status_label)
            thumb_layout.addStretch()

            # Calculate row and column
            row = index // columns
            col = index % columns

            # Add container to grid
            grid_layout.addWidget(thumb_container, row, col)

        # Add stretch to fill empty space
        grid_layout.setRowStretch(grid_layout.rowCount(), 1)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
