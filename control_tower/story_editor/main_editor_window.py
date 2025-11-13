from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QToolBar,
    QAction,
    QScrollArea,
    QMenu,
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QByteArray, QTimer, QSize, Qt
from PyQt5.QtGui import QIcon, QTransform, QPixmap
import xml.etree.ElementTree as ET
import re
import uuid
import os
from configs.story_editor import (
    get_text_editor_font,
    get_tspan_editor_stylesheet,
    get_layer_header_stylesheet,
    get_window_stylesheet,
    get_toolbar_stylesheet,
    get_activate_button_disabled_stylesheet,
    get_activate_button_stylesheet,
    TEXT_EDITOR_MIN_HEIGHT,
    TEXT_EDITOR_MAX_HEIGHT,
    STORY_EDITOR_WINDOW_WIDTH,
    STORY_EDITOR_WINDOW_HEIGHT,
)
from configs.shortcuts import (
    NEW_TEXT_SHORTCUT,
    REFRESH_SHORTCUT,
    UPDATE_KRITA_SHORTCUT,
    PIN_WINDOW_SHORTCUT,
)
from story_editor.utils.text_updater import create_svg_data_for_doc
from story_editor.utils.svg_parser import parse_krita_svg, extract_elements_from_svg
from story_editor.widgets.find_replace import show_find_replace_dialog
from story_editor.utils.logs import write_log
from story_editor.widgets.new_text_edit import add_new_text_widget


class StoryEditorWindow:
    """Handles the text editor window functionality"""

    def __init__(self, parent, socket_handler):
        """
        Initialize the text editor window handler

        Args:
            parent: The parent widget (main window)
            socket_handler: Object with send_request and log methods
        """
        self.parent = parent
        self.socket_handler = socket_handler
        self.all_docs_svg_data = None
        self.parent_window = None  # Will be set by ControlTower

        self.doc_layouts = {}  # Store document layouts {doc_name: layout}
        self.active_doc_name = None  # Track which document is active for new text
        self.thumbnail_scroll_position = 0  # Track thumbnail scroll position
        self.content_scroll_position = 0  # Track content scroll position

    def set_parent_window(self, parent_window):
        """Set the persistent parent window"""
        self.parent_window = parent_window
        # Set close event handler on parent window
        self.parent_window.closeEvent = lambda event: self._on_window_close(event)

    def create_text_editor_window(self):
        """Create the content for the Story Editor"""
        if not self.all_docs_svg_data:
            self.socket_handler.log(
                "⚠️ No SVG data available. Make sure the request succeeded."
            )
            return

        # Save scroll positions before clearing content
        if hasattr(self, "thumbnail_scroll_area_widget"):
            self.thumbnail_scroll_position = (
                self.thumbnail_scroll_area_widget.verticalScrollBar().value()
            )
        if hasattr(self, "all_docs_scroll_area_widget"):
            self.content_scroll_position = (
                self.all_docs_scroll_area_widget.verticalScrollBar().value()
            )

        # Clear previous content in parent window's container
        if self.parent_window:
            # Remove all widgets from content_layout
            while self.parent_window.content_layout.count():
                child = self.parent_window.content_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        self.all_docs_text_state = {}
        self.new_text_widgets = []
        self.doc_layouts = {}
        self.active_doc_name = None

        #################################
        thumbnail_and_text_layout = QHBoxLayout()

        # Create scroll area for thumbnails
        thumbnail_scroll_area = QScrollArea()
        thumbnail_scroll_area.setWidgetResizable(True)
        thumbnail_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        thumbnail_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        thumbnail_scroll_area.setFrameShape(QScrollArea.NoFrame)
        thumbnail_scroll_area.setFixedWidth(140)  # Fixed width for thumbnail column

        # Create container widget for thumbnails
        thumbnail_container = QWidget()
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        # Set the container as scroll area's widget
        thumbnail_scroll_area.setWidget(thumbnail_container)

        # Store reference to thumbnail scroll area for saving position later
        self.thumbnail_scroll_area_widget = thumbnail_scroll_area

        # Create scroll area for all documents' content
        all_docs_scroll_area = QScrollArea()
        all_docs_scroll_area.setWidgetResizable(True)
        all_docs_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        all_docs_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        all_docs_scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Create container widget for all documents
        all_docs_container = QWidget()
        all_docs_layout = QVBoxLayout(all_docs_container)
        all_docs_layout.setContentsMargins(0, 0, 0, 0)

        # Set the container as scroll area's widget
        all_docs_scroll_area.setWidget(all_docs_container)

        # Store reference to all docs scroll area for saving position later
        self.all_docs_scroll_area_widget = all_docs_scroll_area

        thumbnail_and_text_layout.addWidget(thumbnail_scroll_area)
        thumbnail_and_text_layout.addWidget(all_docs_scroll_area)

        # write_log(f"all_docs_svg_data: {self.all_docs_svg_data}")

        # VBoxLayout for all layers
        for doc_data in self.all_docs_svg_data:
            doc_name = doc_data.get("document_name", "unknown")
            doc_path = doc_data.get("document_path", "unknown")
            self.svg_data = doc_data.get("svg_data", [])
            opened = doc_data.get("opened", True)
            thumbnail = doc_data.get("thumbnail", None)

            # Create a horizontal layout for this document (activate button + content)
            doc_horizontal_layout = QHBoxLayout()
            all_docs_layout.addLayout(doc_horizontal_layout)

            ###################################################
            # Thumbnail QVBoxLayout
            ###################################################

            # Create thumbnail label
            thumbnail_label = QLabel()
            thumbnail_label.setFixedSize(128, 128)
            thumbnail_label.setScaledContents(True)
            thumbnail_label.setStyleSheet(
                "border: 2px solid #555; background-color: #2b2b2b;"
            )
            thumbnail_label.setProperty("default_border", "#555")
            thumbnail_label.setProperty("active_border", "#aaa")

            # Load thumbnail from base64 data if available
            if thumbnail:
                try:
                    # Remove the data URI prefix if present
                    if thumbnail.startswith("data:image"):
                        thumbnail_data = thumbnail.split(",", 1)[1]
                    else:
                        thumbnail_data = thumbnail

                    # Decode base64 to bytes
                    import base64

                    image_bytes = base64.b64decode(thumbnail_data)

                    # Create QPixmap from bytes
                    pixmap = QPixmap()
                    pixmap.loadFromData(QByteArray(image_bytes))

                    # Set the pixmap to label
                    thumbnail_label.setPixmap(pixmap)

                    # Set tooltip with document info
                    thumbnail_label.setToolTip(
                        f"Document: {doc_name}\nPath: {doc_path}"
                    )
                except Exception as e:
                    # If loading fails, show placeholder text
                    thumbnail_label.setText("No\nPreview")
                    thumbnail_label.setAlignment(Qt.AlignCenter)
            else:
                # No thumbnail available
                thumbnail_label.setText("No\nPreview")
                thumbnail_label.setAlignment(Qt.AlignCenter)

            # Make thumbnail clickable
            if opened:
                thumbnail_label.setCursor(Qt.PointingHandCursor)
                thumbnail_label.mousePressEvent = (
                    lambda _, name=doc_name: self.thumbnail_clicked(name)
                )

            # Enable custom context menu for right-click
            thumbnail_label.setContextMenuPolicy(Qt.CustomContextMenu)
            thumbnail_label.customContextMenuRequested.connect(
                lambda pos, name=doc_name, label=thumbnail_label: self.show_thumbnail_context_menu(
                    pos, name, label
                )
            )

            thumbnail_layout.addWidget(
                thumbnail_label, alignment=Qt.AlignTop, stretch=0
            )
            ###################################################

            self.all_docs_text_state[doc_name] = {
                "document_name": doc_name,
                "document_path": doc_path,
                "has_text_changes": False,
                "new_text_widgets": [],
                "layer_groups": {},
                "opened": opened,
                "text_edit_widgets": [],  # For find/replace functionality
            }

            # Document header with clickable button to activate
            doc_header_layout = QHBoxLayout()

            # Activate button for this document
            # Add line breaks between each character for vertical text
            vertical_text = lambda: (
                "\n".join(f"{doc_name}") if opened else "\n".join(f"{doc_name}-closed-")
            )
            activate_btn = QPushButton(vertical_text())
            activate_btn.setFixedWidth(40)  # Make button thin
            activate_btn.setMinimumHeight(200)  # Make button tall

            if not opened:
                activate_btn.setStyleSheet(get_activate_button_disabled_stylesheet())
                activate_btn.setEnabled(False)  # Make button unclickable
                activate_btn.setToolTip(
                    f"Document: {doc_name} (offline)\nPath: {doc_path}"
                )
            else:
                activate_btn.setCheckable(True)
                activate_btn.setToolTip(
                    f"Document: {doc_name} (click to activate)\nPath: {doc_path}"
                )
                activate_btn.clicked.connect(
                    lambda checked, name=doc_name, btn=activate_btn: self.activate_document(
                        name, btn
                    )
                )
                activate_btn.setStyleSheet(get_activate_button_stylesheet())
            doc_header_layout.addWidget(activate_btn, alignment=Qt.AlignTop)
            doc_header_layout.addStretch()
            doc_horizontal_layout.addLayout(doc_header_layout, stretch=0)

            # Store button and thumbnail references for later activation
            if not hasattr(self, "doc_buttons"):
                self.doc_buttons = {}
            if not hasattr(self, "doc_thumbnails"):
                self.doc_thumbnails = {}
            self.doc_buttons[doc_name] = activate_btn
            self.doc_thumbnails[doc_name] = thumbnail_label

            # each document has its own QVBoxLayout wrapped in a container for border
            doc_container = QWidget()
            doc_level_layers_layout = QVBoxLayout(doc_container)
            doc_level_layers_layout.setContentsMargins(5, 5, 5, 5)
            doc_container.setStyleSheet(
                "border: 2px solid #333333; background-color: transparent;"
            )

            # Store the layout for this document
            self.doc_layouts[doc_name] = doc_level_layers_layout

            # Set first document as active by default
            # if self.active_doc_name is None:
            #     self.active_doc_name = doc_name
            #     activate_btn.setChecked(True)

            # For each layer
            for layer_data in self.svg_data:
                layer_name = layer_data.get("layer_name", "unknown")
                layer_id = layer_data.get("layer_id", "unknown")
                svg_content = layer_data.get("svg", "")

                parsed_svg_data = parse_krita_svg(
                    doc_name, doc_path, layer_id, svg_content
                )
                write_log(f"parsed_svg_data: {parsed_svg_data}")

                if not parsed_svg_data["layer_shapes"]:
                    continue

                self.all_docs_text_state[doc_name]["layer_groups"][layer_id] = {
                    "layer_name": layer_name,
                    "layer_id": layer_id,
                    "layer_shapes": parsed_svg_data["layer_shapes"],
                    "svg_content": svg_content,
                    "changes": [],
                }

                # Add QTextEdit for each text element
                for elem_idx, layer_shape in enumerate(parsed_svg_data["layer_shapes"]):
                    svg_section_level_layout = QHBoxLayout()
                    # QTextEdit for editing
                    text_edit = QTextEdit()
                    text_edit.setPlainText(layer_shape["text_content"])
                    text_edit.setToolTip(
                        f"Doc: {doc_name} | Layer: {layer_name} | Layer Id: {layer_id} | Shape ID: {layer_shape['element_id']}"
                    )
                    text_edit.setAcceptRichText(False)
                    text_edit.setFont(get_text_editor_font())
                    text_edit.setStyleSheet(get_tspan_editor_stylesheet())
                    text_edit.setMaximumHeight(TEXT_EDITOR_MAX_HEIGHT)

                    # Auto-adjust height based on content
                    doc_height = text_edit.document().size().height()
                    text_edit.setMinimumHeight(
                        min(
                            max(int(doc_height) + 10, TEXT_EDITOR_MIN_HEIGHT),
                            TEXT_EDITOR_MAX_HEIGHT,
                        )
                    )

                    svg_section_level_layout.addWidget(text_edit)

                    self.all_docs_text_state[doc_name]["layer_groups"][layer_id][
                        "changes"
                    ].append(
                        {
                            "new_text": text_edit,
                            "shape_id": layer_shape["element_id"],
                        }
                    )

                    # Add to text_edit_widgets list for find/replace functionality
                    self.all_docs_text_state[doc_name]["text_edit_widgets"].append(
                        {
                            "widget": text_edit,
                            "document_name": doc_name,
                            "layer_name": layer_name,
                            "layer_id": layer_id,
                            "shape_id": layer_shape["element_id"],
                        }
                    )

                    doc_level_layers_layout.addLayout(svg_section_level_layout)

            # Add each document container to horizontal layout (AFTER all layers processed)
            doc_horizontal_layout.addWidget(doc_container, stretch=1)

        # Add stretch at the end of thumbnail layout (inside the container for proper scrolling)
        thumbnail_layout.addStretch()

        # Add stretch at the end of all_docs_layout (inside the container for proper scrolling)
        all_docs_layout.addStretch()

        # Add content to parent window's container
        if self.parent_window:
            self.parent_window.content_layout.addLayout(thumbnail_and_text_layout)

            # Show the parent window
            self.parent_window.show()

            # Restore scroll positions after window is shown (use QTimer to ensure scrollbars are ready)
            QTimer.singleShot(100, self._restore_scroll_positions)

    def add_new_text_widget(self):
        """Add a new empty text editor widget for creating new text"""
        add_new_text_widget(
            self.active_doc_name,
            self.doc_layouts,
            self.all_docs_text_state,
            self.socket_handler,
        )

    def _restore_scroll_positions(self):
        """Restore saved scroll positions for both scroll areas"""
        if (
            hasattr(self, "thumbnail_scroll_area_widget")
            and self.thumbnail_scroll_position > 0
        ):
            self.thumbnail_scroll_area_widget.verticalScrollBar().setValue(
                self.thumbnail_scroll_position
            )

        if (
            hasattr(self, "all_docs_scroll_area_widget")
            and self.content_scroll_position > 0
        ):
            self.all_docs_scroll_area_widget.verticalScrollBar().setValue(
                self.content_scroll_position
            )

    def send_merged_svg_request(self):
        """Send update requests for all modified texts and add new texts"""

        merged_requests = []

        for doc_name, doc_state in self.all_docs_text_state.items():
            self.socket_handler.log(f"⏳ Creating update data for document: {doc_name}")

            doc_path = doc_state["document_path"]
            # layer_groups Contains all changes for the existing layers
            layer_groups = doc_state["layer_groups"]
            # new_text_widgets Contains all new text widgets added by the user
            new_text_widgets = doc_state["new_text_widgets"]

            result = create_svg_data_for_doc(
                doc_name=doc_name,
                doc_path=doc_path,
                layer_groups=layer_groups,
                new_text_widgets=new_text_widgets,
                socket_handler=self.socket_handler,
                opened=doc_state.get("opened"),
            )

            """
            final_result = {
                "doc_name": doc_name,
                "doc_path": doc_path,
                "existing_texts_updated": [],
                "new_texts_added": [],
                "has_changes": False,
                "opened": opened,
            }
            final_result["new_texts_added"].append({"svg_data": svg_data})
            final_result["existing_texts_updated"].append(
                    {
                        "layer_name": layer_name,
                        "layer_id": layer_id,
                        "svg_data": valid_svg_data,
                    }
                )
            """
            if result.get("has_changes"):
                merged_requests.append(result)
                self.socket_handler.log(
                    f"✅ Update data for document: {doc_name} added to the merged requests"
                )

        if len(merged_requests) > 0:
            # write_log(f"merged_requests before send to agent: {merged_requests}")
            self.socket_handler.log(
                f"--- {len(merged_requests)} documents to update ---"
            )
            self.socket_handler.send_request(
                "docs_svg_update",
                merged_requests=merged_requests,
                krita_files_folder=(
                    self.parent.krita_files_folder
                    if hasattr(self.parent, "krita_files_folder")
                    else None
                ),
            )
        else:
            self.socket_handler.log("⚠️ No updates or new texts to send.")

    def show_text_editor(self):
        """Show text editor window with SVG data from Krita document"""
        # self.socket_handler.log("--- Opening Story Editor ---")

        # Clear any existing data
        self.all_docs_svg_data = None

        # Set the waiting flag on the parent (main window)
        if hasattr(self.parent, "_waiting_for_svg"):
            self.parent._waiting_for_svg = "text_editor"

        # Get krita folder path if available
        krita_folder_path = None
        if hasattr(self.parent, "krita_files_folder"):
            krita_folder_path = self.parent.krita_files_folder

        # Request the SVG data
        # The window will be created when set_svg_data() is called with the response
        if krita_folder_path:
            self.socket_handler.send_request(
                "get_all_docs_svg_data", folder_path=krita_folder_path
            )
        else:
            self.socket_handler.send_request("get_all_docs_svg_data")

    def set_svg_data(self, all_docs_svg_data):
        """Store the received SVG data and create the editor window"""
        self.all_docs_svg_data = all_docs_svg_data
        # Automatically create the window when data is received
        self.create_text_editor_window()
        # Disable the open button when window is shown
        self._update_open_button_state(False)

    def _on_window_close(self, event):
        """Handle window close event to re-enable the open button"""
        # Re-enable the open button
        self._update_open_button_state(True)
        # Accept the close event
        event.accept()

    def _update_open_button_state(self, enabled):
        """Update the state of the 'Open Story Editor' button in the main window"""
        if hasattr(self.parent, "show_story_editor_btn"):
            self.parent.show_story_editor_btn.setEnabled(enabled)
            if enabled:
                self.parent.show_story_editor_btn.setText("Open Story Editor")
                self.parent.show_story_editor_btn.setStyleSheet(
                    "background-color: #414a8e; color: #1a1625; padding: 5px;"
                )
            else:
                self.parent.show_story_editor_btn.setText("Story Editor is Open")
                self.parent.show_story_editor_btn.setStyleSheet(
                    "background-color: #666666; color: #999999; padding: 5px;"
                )

    def thumbnail_clicked(self, doc_name):
        """Handle thumbnail click - activate the document"""
        self.activate_document(doc_name)

    def activate_document(self, doc_name, clicked_btn=None):
        """Activate a document for adding new text"""
        # Uncheck all other buttons and reset thumbnail borders
        if hasattr(self, "doc_buttons"):
            for name, btn in self.doc_buttons.items():
                if name != doc_name:
                    btn.setChecked(False)
                    # Reset thumbnail border
                    if hasattr(self, "doc_thumbnails") and name in self.doc_thumbnails:
                        thumbnail = self.doc_thumbnails[name]
                        default_border = thumbnail.property("default_border")
                        thumbnail.setStyleSheet(
                            f"border: 2px solid {default_border}; background-color: #2b2b2b;"
                        )

        # Check the clicked button and update its thumbnail
        if hasattr(self, "doc_buttons") and doc_name in self.doc_buttons:
            self.doc_buttons[doc_name].setChecked(True)

        if hasattr(self, "doc_thumbnails") and doc_name in self.doc_thumbnails:
            thumbnail = self.doc_thumbnails[doc_name]
            active_border = thumbnail.property("active_border")
            thumbnail.setStyleSheet(
                f"border: 2px solid {active_border}; background-color: #2b2b2b;"
            )

        # Set active document
        self.active_doc_name = doc_name
        # self.socket_handler.log(f"📄 Activated document: {doc_name}")

    def refresh_data(self):
        """Refresh the editor window with latest data from Krita"""
        self.socket_handler.log("🔄 Refreshing data from Krita")
        # Simply request new data, which will rebuild the window
        self.show_text_editor()

    def save_all_opened_docs(self):
        """Save all opened Krita documents"""
        self.socket_handler.log("💾 Saving all opened documents")
        self.socket_handler.send_request("save_all_opened_docs")

    def show_find_replace(self):
        """Show the find/replace dialog"""
        if not hasattr(self, "all_docs_text_state") or not self.all_docs_text_state:
            self.socket_handler.log("⚠️ No text editors available")
            return

        show_find_replace_dialog(self.parent_window, self.all_docs_text_state)

    def show_thumbnail_context_menu(self, pos, doc_name, thumbnail_label):
        """Show context menu for thumbnail"""
        menu = QMenu(self.parent_window)

        # Add "Activate" action
        activate_action = menu.addAction("Activate")
        activate_action.triggered.connect(
            lambda: self.send_activate_document_request(doc_name)
        )

        # Add "Close" action
        close_action = menu.addAction("Close")
        close_action.triggered.connect(
            lambda: self.send_close_document_request(doc_name)
        )

        # Show menu at global position
        menu.exec_(thumbnail_label.mapToGlobal(pos))

    def send_close_document_request(self, doc_name):
        """Send close_document request to the agent"""
        self.socket_handler.log(f"❌ Requesting to close document: {doc_name}")
        self.socket_handler.send_request("close_document", doc_name=doc_name)

    def send_activate_document_request(self, doc_name):
        """Send activate_document request to the agent"""
        self.socket_handler.log(f"➡️ Requesting to activate document: {doc_name}")
        self.socket_handler.send_request("activate_document", doc_name=doc_name)
