import json
import os
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QStackedWidget,
    QWidget,
    QScrollArea,
)
from PyQt5.QtCore import Qt

# Import all config loaders to refresh them after save
from . import main_window_loader, shortcuts_loader, story_editor_loader
from .app_paths import get_config_dir


class ConfigDialog(QDialog):
    """Dialog for editing multiple configuration files with tabs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(800, 700)

        # Configuration file paths - use user_data/config with fallback
        config_dir = get_config_dir()
        self.config_files = {
            "Main Window": os.path.join(config_dir, "main_window.json"),
            "Story Editor": os.path.join(config_dir, "story_editor.json"),
            "Shortcuts": os.path.join(config_dir, "shortcuts.json"),
        }

        self.configs = {}
        self.fields = {}

        self.setup_ui()
        self.load_all_configs()
        self.setup_connections()

    def setup_ui(self):
        """Setup the UI elements"""
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left side - Category list
        self.category_list = QListWidget()
        self.category_list.setMaximumWidth(150)
        self.category_list.addItems(self.config_files.keys())
        self.category_list.setCurrentRow(0)
        main_layout.addWidget(self.category_list)

        # Right side - Stacked widget for config pages
        right_layout = QVBoxLayout()

        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget)

        # Add info message
        self.info_label = QLabel(
            "Some changes require application restart to take effect"
        )
        self.info_label.setStyleSheet("color: #ecbd30; font-style: italic;")
        right_layout.addWidget(self.info_label)

        # Button layout
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save All")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        right_layout.addLayout(btn_layout)

        main_layout.addLayout(right_layout)

    def load_all_configs(self):
        """Load all configuration files and create pages"""
        for category_name, config_path in self.config_files.items():
            # Load config
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.configs[category_name] = config

            # Create page for this config
            page = self.create_config_page(category_name, config, config_path)
            self.stacked_widget.addWidget(page)

    def create_config_page(self, category_name, config, config_path):
        """Create a page for a specific configuration file"""
        page = QWidget()
        page_layout = QVBoxLayout(page)

        # Create scroll area for config fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)

        # Recursively create fields for nested config
        self.create_fields_recursive(content_layout, config, category_name, [])

        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)

        return page

    def create_fields_recursive(self, layout, config, category_name, path):
        """Recursively create fields for nested configuration"""
        if isinstance(config, dict):
            for key, value in config.items():
                current_path = path + [key]

                if isinstance(value, dict):
                    # Add section header
                    header = QLabel(f"[{key}]")
                    header.setStyleSheet(
                        "font-weight: bold; color: #4A9EFF; margin-top: 10px;"
                    )
                    layout.addWidget(header)

                    # Recursively add nested items
                    self.create_fields_recursive(
                        layout, value, category_name, current_path
                    )
                else:
                    # Add field for this value
                    hlayout = QHBoxLayout()

                    label = QLabel(key)
                    label.setAlignment(Qt.AlignLeft)

                    edit = QLineEdit(str(value))
                    edit.setFixedWidth(200)
                    edit.setAlignment(Qt.AlignRight)

                    hlayout.addWidget(label)
                    hlayout.addStretch()
                    hlayout.addWidget(edit)

                    layout.addLayout(hlayout)

                    # Store field with full path
                    field_key = (category_name, tuple(current_path))
                    self.fields[field_key] = (edit, type(value))

        layout.addStretch()

    def setup_connections(self):
        """Setup button connections"""
        self.category_list.currentRowChanged.connect(
            self.stacked_widget.setCurrentIndex
        )
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    def save_and_close(self):
        """Save all configurations and close dialog"""
        # Update config values from fields
        for (category_name, path_tuple), (edit, value_type) in self.fields.items():
            val = edit.text()

            # Type conversion
            try:
                if value_type == int:
                    val = int(val)
                elif value_type == float:
                    val = float(val)
                elif value_type == bool:
                    val = val.lower() in ("true", "1", "yes")
                # else keep as string
            except ValueError:
                # Keep original value if conversion fails
                pass

            # Navigate to nested location and update
            config = self.configs[category_name]
            path_list = list(path_tuple)

            # Navigate to parent
            for key in path_list[:-1]:
                config = config[key]

            # Set value
            config[path_list[-1]] = val

        # Write all configs to files
        for category_name, config_path in self.config_files.items():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.configs[category_name], f, indent=4)

        # Refresh all config loaders
        main_window_loader.reload_config()
        shortcuts_loader.reload_config()
        story_editor_loader.reload_config()

        self.accept()
