from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QLabel, QLineEdit,
                             QTextEdit, QSplitter, QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt
import xml.etree.ElementTree as ET


class SvgTreeEditor:
    """Handles the SVG tree editor window with split view"""

    def __init__(self, parent, socket_handler):
        """
        Initialize the SVG tree editor handler

        Args:
            parent: The parent widget (main window)
            socket_handler: Object with send_request and log methods
        """
        self.parent = parent
        self.socket_handler = socket_handler
        self.svg_data = None
        self.svg_editor_window = None
        self.current_element = None
        self.current_tree_item = None

    def show_svg_editor(self):
        """Show SVG editor window with SVG data from Krita document"""
        self.socket_handler.log("\n--- Opening SVG Tree Editor ---")

        # Clear any existing data
        self.svg_data = None

        # Request the SVG data
        self.socket_handler.send_request('get_all_svg_data')

    def set_svg_data(self, svg_data):
        """Store the received SVG data and create the editor window"""
        self.svg_data = svg_data
        # Automatically create the window when data is received
        self.create_svg_editor_window()

    def create_svg_editor_window(self):
        """Create the SVG tree editor window with split view"""
        if not self.svg_data:
            self.socket_handler.log("⚠️ No SVG data available. Make sure the request succeeded.")
            return

        # Close existing window if it exists
        if self.svg_editor_window:
            self.svg_editor_window.close()

        # Create new window
        self.svg_editor_window = QWidget()
        self.svg_editor_window.setWindowTitle("SVG Tree Editor")
        self.svg_editor_window.resize(1200, 700)

        # Main layout
        main_layout = QVBoxLayout(self.svg_editor_window)

        # Top bar with buttons
        top_bar = QHBoxLayout()

        # Update button
        update_btn = QPushButton("Update Krita")
        update_btn.clicked.connect(self.update_svg_in_krita)
        top_bar.addWidget(update_btn)

        top_bar.addStretch()

        # Close button
        close_btn = QPushButton("X")
        close_btn.setMaximumWidth(30)
        close_btn.setMaximumHeight(30)
        close_btn.clicked.connect(self.svg_editor_window.close)
        top_bar.addWidget(close_btn)
        main_layout.addLayout(top_bar)

        # Create splitter for split view
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Tree view
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Layer selector label
        layer_label = QLabel("SVG Layers:")
        left_layout.addWidget(layer_label)

        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Element", "Attributes"])
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.tree_widget)

        splitter.addWidget(left_widget)

        # Right side: Details panel
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        details_label = QLabel("Element Details:")
        details_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(details_label)

        # Details form
        details_group = QGroupBox("Properties")
        details_form = QFormLayout()

        # Element tag name
        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setPlaceholderText("Element tag name")
        self.tag_name_edit.textChanged.connect(self.on_details_changed)
        details_form.addRow("Tag Name:", self.tag_name_edit)

        # Attributes editor
        attr_label = QLabel("Attributes (format: name=\"value\", one per line):")
        details_form.addRow(attr_label)

        self.attributes_edit = QTextEdit()
        self.attributes_edit.setPlaceholderText('id="shape0"\ntransform="translate(0, 0)"')
        self.attributes_edit.setMaximumHeight(150)
        self.attributes_edit.textChanged.connect(self.on_details_changed)
        details_form.addRow(self.attributes_edit)

        # Text content
        text_label = QLabel("Text Content:")
        details_form.addRow(text_label)

        self.text_content_edit = QTextEdit()
        self.text_content_edit.setPlaceholderText("Element text content")
        self.text_content_edit.textChanged.connect(self.on_details_changed)
        details_form.addRow(self.text_content_edit)

        details_group.setLayout(details_form)
        right_layout.addWidget(details_group)

        # Raw XML preview
        preview_label = QLabel("Raw XML Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(preview_label)

        self.xml_preview = QTextEdit()
        self.xml_preview.setReadOnly(True)
        self.xml_preview.setMaximumHeight(200)
        right_layout.addWidget(self.xml_preview)

        right_layout.addStretch()

        splitter.addWidget(right_widget)

        # Set splitter sizes (40% left, 60% right)
        splitter.setSizes([480, 720])

        main_layout.addWidget(splitter)

        # Populate tree with SVG data
        self.populate_tree()

        # Show the window
        self.svg_editor_window.show()
        self.socket_handler.log(f"✅ SVG tree editor opened with {len(self.svg_data)} layer(s)")

    def populate_tree(self):
        """Populate the tree widget with SVG data"""
        self.tree_widget.clear()

        for layer_data in self.svg_data:
            layer_name = layer_data.get('layer_name', 'Unknown')
            layer_id = layer_data.get('layer_id', 'Unknown')
            svg_content = layer_data.get('svg', '')

            # Create layer root item
            layer_item = QTreeWidgetItem(self.tree_widget)
            layer_item.setText(0, f"Layer: {layer_name}")
            layer_item.setText(1, f"ID: {layer_id}")
            layer_item.setData(0, Qt.UserRole, {'type': 'layer', 'data': layer_data})

            # Parse SVG and build tree
            try:
                root = ET.fromstring(svg_content)
                self.add_element_to_tree(root, layer_item, layer_data)
            except Exception as e:
                error_item = QTreeWidgetItem(layer_item)
                error_item.setText(0, f"Error parsing SVG: {str(e)}")

            layer_item.setExpanded(True)

    def add_element_to_tree(self, element, parent_item, layer_data):
        """Recursively add XML elements to the tree"""
        # Get tag without namespace
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

        # Create tree item
        item = QTreeWidgetItem(parent_item)
        item.setText(0, tag)

        # Format attributes for display
        attrs = []
        for key, value in element.attrib.items():
            # Truncate long values
            display_value = value[:30] + "..." if len(value) > 30 else value
            attrs.append(f'{key}="{display_value}"')

        item.setText(1, ", ".join(attrs) if attrs else "")

        # Store element data
        item.setData(0, Qt.UserRole, {
            'type': 'element',
            'element': element,
            'layer_data': layer_data,
            'tag': tag,
            'full_tag': element.tag
        })

        # Add text content if exists
        if element.text and element.text.strip():
            text_item = QTreeWidgetItem(item)
            text_content = element.text.strip()
            display_text = text_content[:50] + "..." if len(text_content) > 50 else text_content
            text_item.setText(0, f"[Text: {display_text}]")
            text_item.setData(0, Qt.UserRole, {
                'type': 'text',
                'parent_element': element,
                'layer_data': layer_data
            })

        # Recursively add child elements
        for child in element:
            self.add_element_to_tree(child, item, layer_data)

            # Add tail text if exists
            if child.tail and child.tail.strip():
                tail_item = QTreeWidgetItem(item)
                tail_content = child.tail.strip()
                display_tail = tail_content[:50] + "..." if len(tail_content) > 50 else tail_content
                tail_item.setText(0, f"[Text: {display_tail}]")
                tail_item.setData(0, Qt.UserRole, {
                    'type': 'tail',
                    'parent_element': element,
                    'child_element': child,
                    'layer_data': layer_data
                })

    def on_tree_item_clicked(self, item, column):
        """Handle tree item click to show details"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        item_type = data.get('type')
        self.current_tree_item = item

        if item_type == 'element':
            self.current_element = data.get('element')
            self.show_element_details(self.current_element, data.get('tag'))
        elif item_type == 'text':
            self.current_element = data.get('parent_element')
            self.show_text_details(self.current_element, is_tail=False)
        elif item_type == 'tail':
            self.current_element = data.get('parent_element')
            child = data.get('child_element')
            self.show_text_details(child, is_tail=True)
        elif item_type == 'layer':
            self.show_layer_details(data.get('data'))

    def show_element_details(self, element, tag):
        """Show element details in the details panel"""
        # Set tag name
        self.tag_name_edit.blockSignals(True)
        self.tag_name_edit.setText(tag)
        self.tag_name_edit.blockSignals(False)

        # Set attributes
        self.attributes_edit.blockSignals(True)
        attrs_text = "\n".join([f'{key}="{value}"' for key, value in element.attrib.items()])
        self.attributes_edit.setPlainText(attrs_text)
        self.attributes_edit.blockSignals(False)

        # Set text content
        self.text_content_edit.blockSignals(True)
        text = element.text if element.text else ""
        self.text_content_edit.setPlainText(text)
        self.text_content_edit.blockSignals(False)

        # Update XML preview
        self.update_xml_preview(element)

    def show_text_details(self, element, is_tail=False):
        """Show text node details"""
        # Clear tag and attributes
        self.tag_name_edit.blockSignals(True)
        self.tag_name_edit.setText("[Text Node]")
        self.tag_name_edit.setReadOnly(True)
        self.tag_name_edit.blockSignals(False)

        self.attributes_edit.blockSignals(True)
        self.attributes_edit.setPlainText("")
        self.attributes_edit.setReadOnly(True)
        self.attributes_edit.blockSignals(False)

        # Set text content
        self.text_content_edit.blockSignals(True)
        text = element.tail if is_tail else element.text
        self.text_content_edit.setPlainText(text if text else "")
        self.text_content_edit.setReadOnly(False)
        self.text_content_edit.blockSignals(False)

        # Update preview
        self.xml_preview.setPlainText(f"Text content: {text if text else '(empty)'}")

    def show_layer_details(self, layer_data):
        """Show layer details"""
        layer_name = layer_data.get('layer_name', 'Unknown')
        layer_id = layer_data.get('layer_id', 'Unknown')

        # Clear editors
        self.tag_name_edit.blockSignals(True)
        self.tag_name_edit.setText(f"[Layer: {layer_name}]")
        self.tag_name_edit.setReadOnly(True)
        self.tag_name_edit.blockSignals(False)

        self.attributes_edit.blockSignals(True)
        self.attributes_edit.setPlainText(f"Layer ID: {layer_id}")
        self.attributes_edit.setReadOnly(True)
        self.attributes_edit.blockSignals(False)

        self.text_content_edit.blockSignals(True)
        self.text_content_edit.setPlainText("")
        self.text_content_edit.setReadOnly(True)
        self.text_content_edit.blockSignals(False)

        # Show full SVG in preview
        svg_content = layer_data.get('svg', '')
        self.xml_preview.setPlainText(svg_content[:1000] + "..." if len(svg_content) > 1000 else svg_content)

    def on_details_changed(self):
        """Handle changes in the details panel"""
        if not self.current_element:
            return

        # Update element based on changes
        # This is called whenever user edits tag, attributes, or text

    def update_xml_preview(self, element):
        """Update the XML preview with current element"""
        try:
            # Get the element's position in the original SVG
            # Find the layer data from current tree item
            if self.current_tree_item:
                data = self.current_tree_item.data(0, Qt.UserRole)
                if data and data.get('layer_data'):
                    layer_data = data.get('layer_data')
                    original_svg = layer_data.get('svg', '')

                    # Try to extract the original XML for this element from the SVG
                    if hasattr(element, 'attrib') and 'id' in element.attrib:
                        shape_id = element.attrib['id']
                        # Use regex to find the original element in the SVG
                        import re
                        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
                        pattern = rf'<{tag}[^>]*id="{re.escape(shape_id)}"[^>]*(?:/>|>.*?</{tag}>)'
                        match = re.search(pattern, original_svg, re.DOTALL)
                        if match:
                            self.xml_preview.setPlainText(match.group(0))
                            return

            # Fallback: use ET.tostring but clean up namespaces
            xml_str = ET.tostring(element, encoding='unicode', method='xml')
            # Remove namespace prefixes like ns0:, ns1: etc
            import re
            xml_str = re.sub(r'<ns\d+:', '<', xml_str)
            xml_str = re.sub(r'</ns\d+:', '</', xml_str)
            xml_str = re.sub(r'xmlns:ns\d+="[^"]*"\s*', '', xml_str)
            self.xml_preview.setPlainText(xml_str)
        except Exception as e:
            self.xml_preview.setPlainText(f"Error generating preview: {str(e)}")

    def update_svg_in_krita(self):
        """Send updated SVG data back to Krita"""
        self.socket_handler.log("\n--- Updating SVG in Krita ---")
        self.socket_handler.log("⚠️ SVG update to Krita not yet implemented")
        # TODO: Implement SVG update functionality
        # This would need a new action in the agent to accept updated SVG
