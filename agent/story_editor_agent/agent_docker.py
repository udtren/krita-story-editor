import os
from krita import *
from PyQt5.QtNetwork import QLocalServer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QDialog,
    QDialogButtonBox,
    QLabel,
)
import json
import io
import sys
from .utils import (
    get_opened_doc_svg_data,
    add_svg_layer_to_doc,
    get_svg_from_activenode,
    update_doc_layers_svg,
    get_all_offline_docs_from_folder,
    update_offline_kra_file,
    krita_file_name_safe,
    get_comic_config_info,
)
from .config.story_editor_agent import (
    DIALOG_WIDTH,
    DIALOG_HEIGHT,
    get_output_dialog_stylesheet,
    get_dialog_label_stylesheet,
    get_dialog_stylesheet,
)
from .utils.logs import write_log


class StoryEditorAgentDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor Agent")

        # Set up local server for communication
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.handle_connection)
        self.server.listen("krita_story_editor_bridge")

        self.clients = []
        self.comic_config_info = None

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        """Create the docker UI"""
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # get SVG from active node for creating template
        get_svg_from_activenode_btn = QPushButton("Get SVG from Active Node")
        get_svg_from_activenode_btn.clicked.connect(self.show_active_node_svg)
        get_svg_from_activenode_btn.setToolTip(
            "Click to view SVG data from the currently active vector layer"
        )
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
        label = QLabel("SVG data from active vector layer (you can select and copy):")
        label.setStyleSheet(get_dialog_label_stylesheet())
        layout.addWidget(label)

        # Text display
        text_edit = QTextEdit()
        text_edit.setPlainText(
            output_text if output_text else "No output or no active vector layer"
        )
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
        data = client.readAll().data().decode("utf-8")
        request = json.loads(data)

        # Process request and interact with Krita
        match request["action"]:
            case "docs_svg_update":
                try:
                    opened_docs = Krita.instance().documents()
                    merged_requests = request.get("merged_requests", {})

                    write_log(f"Received merged requests: {merged_requests}")

                    ############################################################
                    # Separate opened and offline requests
                    ############################################################
                    opened_docs_requests = []
                    offline_docs_requests = []

                    for doc_data in merged_requests:
                        if doc_data.get("opened", False):
                            opened_docs_requests.append(doc_data)
                        else:
                            offline_docs_requests.append(doc_data)

                    # Sort both lists by document_name
                    opened_docs_requests.sort(key=lambda x: x.get("doc_name", ""))
                    offline_docs_requests.sort(key=lambda x: x.get("doc_name", ""))

                    write_log(
                        f"Opened documents: {[d.get('doc_name') for d in opened_docs_requests]}"
                    )
                    write_log(
                        f"Offline documents: {[d.get('doc_name') for d in offline_docs_requests]}"
                    )
                    ############################################################

                    ############################################################
                    # Update Opened Documents
                    ############################################################
                    online_progress_messages = []

                    for doc in opened_docs:
                        for doc_data in opened_docs_requests:
                            write_log(
                                f"[DEBUG] agent_docker compare Document name: {krita_file_name_safe(doc)}"
                            )
                            if krita_file_name_safe(doc) == doc_data.get("doc_name"):

                                existing_texts_updated = doc_data.get(
                                    "existing_texts_updated", []
                                )
                                new_texts_added = doc_data.get("new_texts_added", [])

                                result_message_base = f"{krita_file_name_safe(doc)}: "

                                if len(existing_texts_updated) > 0:

                                    result = update_doc_layers_svg(
                                        doc, existing_texts_updated
                                    )

                                    if result["success"]:
                                        result_message_base += f"\n  Updated {result.get('count', 0)} existing texts. "

                                    else:
                                        online_progress_messages.append(
                                            f"{krita_file_name_safe(doc)}: Updating existing texts failed."
                                        )
                                if len(new_texts_added) > 0:

                                    result = add_svg_layer_to_doc(doc, new_texts_added)
                                    if result["success"]:
                                        result_message_base += f"\n  Added {result.get('count', 0)} new texts. "

                                    else:
                                        online_progress_messages.append(
                                            f"{krita_file_name_safe(doc)}: Creating new texts failed."
                                        )
                                online_progress_messages.append(result_message_base)

                    ############################################################
                    # Update Offline Documents
                    ############################################################
                    offline_progress_messages = []

                    if len(offline_docs_requests) > 0:

                        write_log(
                            f"Updating offline .kra files: {[d.get('doc_path') for d in offline_docs_requests]}"
                        )

                        for doc_data in offline_docs_requests:
                            doc_name = doc_data.get("doc_name")
                            doc_path = doc_data.get("doc_path")
                            existing_texts_updated = doc_data.get(
                                "existing_texts_updated", []
                            )

                            # Check if file exists
                            if not os.path.exists(doc_path):
                                write_log(f"[WARNING] File not found: {doc_path}")
                                continue

                            result = update_offline_kra_file(
                                doc_path, existing_texts_updated
                            )
                            offline_progress_messages.append(result.get("result", ""))

                    ############################################################
                    final_message = "Text update applied successfully"
                    if online_progress_messages:
                        final_message += (
                            "\n" + "\n".join(online_progress_messages) + "\n"
                        )
                    if offline_progress_messages:
                        final_message += (
                            "\n" + "\n".join(offline_progress_messages) + "\n"
                        )

                    response = {
                        "success": True,
                        "docs_svg_update_result": final_message,
                    }
                    client.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    response = {"success": False, "docs_svg_update_result": str(e)}
                    client.write(json.dumps(response).encode("utf-8"))

            case "get_all_docs_svg_data":
                opened_docs = Krita.instance().documents()
                krita_folder_path = request.get("folder_path", None)
                all_svg_data = []
                opened_docs_path = []

                ####################################################
                # Get all docs svg data from opened documents
                ####################################################
                if not opened_docs:
                    response = {"success": False, "error": "No single active document"}
                else:
                    try:
                        for doc in opened_docs:
                            response_data = get_opened_doc_svg_data(doc)
                            all_svg_data.append(response_data)
                            opened_docs_path.append(
                                response_data.get("document_path", "")
                            )

                    except Exception as e:
                        response = {"success": False, "error": str(e)}
                ####################################################

                if krita_folder_path:
                    ####################################################
                    # Get all docs svg data from .kra files in folder
                    ####################################################
                    try:
                        write_log(f"krita_folder_path: {krita_folder_path}")
                        offline_docs_svg_data = get_all_offline_docs_from_folder(
                            krita_folder_path, opened_docs_path
                        )
                        all_svg_data.extend(offline_docs_svg_data)

                    except Exception as e:
                        response = {"success": False, "error": str(e)}
                    ####################################################

                    self.comic_config_info = get_comic_config_info(krita_folder_path)
                else:
                    self.comic_config_info = None

                # Sort all_svg_data by document_name
                all_svg_data.sort(key=lambda x: x.get("document_name", ""))

                if self.comic_config_info:
                    write_log(f"Comic config info: {self.comic_config_info}")

                    response = {
                        "success": True,
                        "all_docs_svg_data": all_svg_data,
                        "comic_config_info": self.comic_config_info,
                    }
                    client.write(json.dumps(response).encode("utf-8"))
                else:
                    response = {"success": True, "all_docs_svg_data": all_svg_data}
                    client.write(json.dumps(response).encode("utf-8"))

            case "save_all_opened_docs":
                try:
                    opened_docs = Krita.instance().documents()
                    for doc in opened_docs:
                        doc.save()
                    response = {
                        "success": True,
                        "response_type": "save_all_opened_docs",
                        "result": "All opened documents saved.",
                    }
                    client.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    response = {"success": False, "error": str(e)}
                    client.write(json.dumps(response).encode("utf-8"))

            case "activate_document":
                try:
                    doc_name = request.get("doc_name", "")
                    opened_docs = Krita.instance().documents()
                    target_doc = None
                    for doc in opened_docs:
                        if krita_file_name_safe(doc) == doc_name:
                            target_doc = doc
                            break
                    if target_doc:
                        Krita.instance().setActiveDocument(target_doc)
                        Application.activeWindow().addView(target_doc)
                        response = {
                            "success": True,
                            "response_type": "activate_document",
                            "result": f"Document '{doc_name}' activated.",
                        }
                    else:
                        response = {
                            "success": False,
                            "response_type": "activate_document",
                            "error": f"Document '{doc_name}' not found among opened documents.",
                        }
                    client.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    response = {"success": False, "error": str(e)}
                    client.write(json.dumps(response).encode("utf-8"))

            case "open_document":
                try:
                    doc_path = request.get("doc_path", "")
                    if os.path.exists(doc_path):
                        opened_doc = Krita.instance().openDocument(doc_path)
                        if opened_doc:
                            Krita.instance().setActiveDocument(opened_doc)
                            Application.activeWindow().addView(opened_doc)
                        response = {
                            "success": True,
                            "response_type": "open_document",
                            "result": f"Document '{doc_path}' opened.",
                        }
                    else:
                        response = {
                            "success": False,
                            "response_type": "open_document",
                            "error": f"File '{doc_path}' does not exist.",
                        }
                    client.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    response = {"success": False, "error": str(e)}
                    client.write(json.dumps(response).encode("utf-8"))

            case "close_document":
                try:
                    doc_name = request.get("doc_name", "")
                    opened_docs = Krita.instance().documents()
                    target_doc = None
                    for doc in opened_docs:
                        if krita_file_name_safe(doc) == doc_name:
                            target_doc = doc
                            break
                    if target_doc:
                        target_doc.close()
                        response = {
                            "success": True,
                            "response_type": "close_document",
                            "result": f"Document '{doc_name}' closed.",
                        }
                    else:
                        response = {
                            "success": False,
                            "response_type": "close_document",
                            "error": f"Document '{doc_name}' not found among opened documents.",
                        }
                    client.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    response = {"success": False, "error": str(e)}
                    client.write(json.dumps(response).encode("utf-8"))

            case _:
                # Unknown action
                response = {
                    "success": False,
                    "error": f"Unknown action: {request['action']}",
                }
                client.write(json.dumps(response).encode("utf-8"))


class StoryEditorAgentFactory(DockWidgetFactoryBase):

    def __init__(self):
        super().__init__("StoryEditorAgentDocker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        return StoryEditorAgentDocker()
