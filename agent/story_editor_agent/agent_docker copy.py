from .utils.logs import write_log
from krita import *
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtCore import QByteArray
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QDialog, QDialogButtonBox, QLabel
import json
import io
import sys
from .utils import get_all_svg_data
from .utils.get_svg_from_activenode import get_svg_from_activenode
from .utils import update_text_via_shapes
from .configs.story_editor_agent import (
    DIALOG_WIDTH,
    DIALOG_HEIGHT,
    get_output_dialog_stylesheet,
    get_dialog_label_stylesheet,
    get_dialog_stylesheet
)


class StoryEditorAgentDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor Agent")

        # Set up local server for communication
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.handle_connection)
        self.server.listen("krita_story_editor_bridge")

        self.clients = []

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        """Create the docker UI"""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # Debug button to get SVG from active node
        get_svg_from_activenode_btn = QPushButton("Get SVG from Active Node")
        get_svg_from_activenode_btn.clicked.connect(self.show_active_node_svg)
        get_svg_from_activenode_btn.setToolTip(
            "Click to view SVG data from the currently active vector layer")
        layout.addWidget(get_svg_from_activenode_btn)

        layout.addStretch()

        self.setWidget(main_widget)

    def show_active_node_svg(self):
        """Get SVG from active node and display in a popup"""
        # Capture print output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            # Call the function which prints to stdout
            get_svg_from_activenode()

            # Get the captured output
            output = captured_output.getvalue()

        except Exception as e:
            output = f"Error: {str(e)}"
        finally:
            # Restore stdout
            sys.stdout = old_stdout

        # Show in a dialog
        self.show_output_dialog(output)

    def show_output_dialog(self, output_text):
        """Show output in a copyable dialog window"""
        dialog = QDialog(self)
        dialog.setWindowTitle("SVG Output from Active Node")
        dialog.resize(DIALOG_WIDTH, DIALOG_HEIGHT)
        dialog.setStyleSheet(get_dialog_stylesheet())

        layout = QVBoxLayout(dialog)

        # Info label
        label = QLabel(
            "SVG data from active vector layer (you can select and copy):")
        label.setStyleSheet(get_dialog_label_stylesheet())
        layout.addWidget(label)

        # Text display
        text_edit = QTextEdit()
        text_edit.setPlainText(
            output_text if output_text else "No output or no active vector layer")
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(get_output_dialog_stylesheet())
        layout.addWidget(text_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec_()

    def handle_connection(self):
        client = self.server.nextPendingConnection()
        client.readyRead.connect(lambda: self.handle_message(client))
        self.clients.append(client)

    def handle_message(self, client):
        data = client.readAll().data().decode('utf-8')
        request = json.loads(data)

        # Process request and interact with Krita
        match request['action']:
            case 'text_update_request':
                try:
                    opened_docs = Krita.instance().documents()
                    merged_requests = request.get(
                        'merged_requests', {})
                    response_body = {}
                    for doc in opened_docs:
                        for item in merged_requests:
                            text_edit_type = item.get('text_edit_type', None)

                            if text_edit_type == 'existing_texts_updated':
                                '''updates_with_doc_info = {
                                    'document_name': doc_name,
                                    'updates': updates
                                }'''
                                updates_with_doc_info = item['data']

                                # Update text using shape API

                                if doc.name() == updates_with_doc_info.get('document_name'):

                                    result = update_text_via_shapes(
                                        doc, updates_with_doc_info.get('updates'))
                                    response_body[doc.name(
                                    )]["update_count"] += result
                                    break  # Exit loop once document is found and updated

                            if text_edit_type == "new_texts_added":
                                '''new_texts_with_doc_info = {
                                    'document_name': doc_name,
                                    'new_texts': new_texts
                                }'''
                                new_texts_with_doc_info = item['data']

                                if doc.name() == new_texts_with_doc_info.get('document_name'):

                                    for new_text in new_texts_with_doc_info.get('new_texts', []):
                                        svg_data = new_text.get('svg_data', '')

                                        if not doc:
                                            response = {'success': False,
                                                        'error': 'No active document'}
                                            break
                                        else:
                                            from .utils import new_text_via_shapes
                                            result = new_text_via_shapes(
                                                doc, svg_data)
                                            response_body[doc.name(
                                            )]["update_count"] += result
                                    break
                    response = {'success': True,
                                'text_update_request_result': response_body}
                    client.write(json.dumps(response).encode('utf-8'))
                except Exception as e:
                    response = {'success': False,
                                'text_update_request_result': str(e)}
                    client.write(json.dumps(response).encode('utf-8'))

                    # case 'get_all_svg_data':
                    #     doc = Krita.instance().activeDocument()

                    #     if not doc:
                    #         response = {'success': False,
                    #                     'error': 'No active document'}
                    #     else:
                    #         try:
                    #             # Get all text from vector layers
                    #             response_data = get_all_svg_data(doc)
                    #             response = {'success': True,
                    #                         'svg_data': response_data['svg_data']}
                    #         except Exception as e:
                    #             response = {'success': False, 'error': str(e)}
                    #     client.write(json.dumps(response).encode('utf-8'))

            case 'get_all_docs_svg_data':
                opened_docs = Krita.instance().documents()
                all_svg_data = []

                if not opened_docs:
                    response = {'success': False,
                                'error': 'No single active document'}
                else:
                    try:
                        for doc in opened_docs:
                            response_data = get_all_svg_data(doc)
                            all_svg_data.append(response_data)
                        response = {'success': True,
                                    'all_docs_svg_data': all_svg_data}
                    except Exception as e:
                        response = {'success': False, 'error': str(e)}
                client.write(json.dumps(response).encode('utf-8'))

            case _:
                # Unknown action
                response = {'success': False,
                            'error': f"Unknown action: {request['action']}"}
                client.write(json.dumps(response).encode('utf-8'))


class StoryEditorAgentFactory(DockWidgetFactoryBase):

    def __init__(self):
        super().__init__("StoryEditorAgentDocker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        return StoryEditorAgentDocker()
