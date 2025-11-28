from krita import *  # type: ignore
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
from collections import deque
from PyQt5.QtCore import QTimer
import json
import io
import sys
from .utils import get_svg_from_activenode
from .config.story_editor_agent import (
    DIALOG_WIDTH,
    DIALOG_HEIGHT,
    get_output_dialog_stylesheet,
    get_dialog_label_stylesheet,
    get_dialog_stylesheet,
)
from .utils.logs import write_log
from .handlers import ACTION_HANDLERS

try:
    from quick_access_manager.gesture.gesture_main import (
        pause_gesture_event_filter,
        resume_gesture_event_filter,
    )

    GESTURE_AVAILABLE = True
except ImportError:
    GESTURE_AVAILABLE = False


class StoryEditorAgentDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor Agent")

        # Set up local server for communication
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.handle_connection)
        self.server.listen("krita_story_editor_bridge")

        self.clients = []
        self.krita_folder_path = None
        self.comic_config_info = None

        # Create UI
        self.setup_ui()

        # Task queue system
        self.task_queue = deque()
        self.is_processing = False

        # Timer for processing queue (processes one task per interval)
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.process_next_task)
        self.queue_timer.setInterval(50)  # 50ms between tasks

    def handle_connection(self):
        client = self.server.nextPendingConnection()
        client.readyRead.connect(lambda: self.handle_message(client))
        self.clients.append(client)

    def handle_message(self, client):
        """Queue incoming messages instead of processing immediately"""
        try:
            data = client.readAll().data().decode("utf-8")
            request = json.loads(data)

            # Add to queue with client reference
            self.task_queue.append((client, request))
            write_log(
                f"Queued task: {request.get('action', 'unknown')} (queue size: {len(self.task_queue)})"
            )

            # Start processing if not already
            if not self.queue_timer.isActive():
                self.queue_timer.start()
        except json.JSONDecodeError as e:
            write_log(f"Failed to parse JSON: {e}")
            response = {"success": False, "error": f"Invalid JSON: {e}"}
            client.write(json.dumps(response).encode("utf-8"))

    def process_next_task(self):
        """Process one task from the queue"""
        if not self.task_queue:
            self.queue_timer.stop()
            self.is_processing = False
            # Resume gestures when all tasks are done
            # if GESTURE_AVAILABLE:
            #     resume_gesture_event_filter()
            #     write_log("Resumed gesture event filter")
            return

        # Pause gestures when starting to process (only on first task)
        if not self.is_processing:
            self.is_processing = True
            # if GESTURE_AVAILABLE:
            #     pause_gesture_event_filter()
            #     write_log("Paused gesture event filter")

        client, request = self.task_queue.popleft()
        self._execute_task(client, request)

    def _execute_task(self, client, request):
        """Execute the given task request"""
        try:
            action = request.get("action")

            # Look up the handler for this action
            handler = ACTION_HANDLERS.get(action)

            if handler:
                handler(client, request, self)
            else:
                # Unknown action
                response = {
                    "success": False,
                    "error": f"Unknown action: {action}",
                }
                client.write(json.dumps(response).encode("utf-8"))
        except Exception as e:
            write_log(f"Error handling message: {e}")
            response = {"success": False, "error": str(e)}
            client.write(json.dumps(response).encode("utf-8"))

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


class StoryEditorAgentFactory(DockWidgetFactoryBase):

    def __init__(self):
        super().__init__("StoryEditorAgentDocker", DockWidgetFactory.DockRight)

    def createDockWidget(self):
        return StoryEditorAgentDocker()
