from krita import *
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtCore import QByteArray
import json
from .utils import get_all_vector_text, update_vector_text


class StoryEditorAgentDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Editor Agent")

        # Set up local server for communication
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.handle_connection)
        self.server.listen("krita_story_editor_bridge")

        self.clients = []

    def handle_connection(self):
        client = self.server.nextPendingConnection()
        client.readyRead.connect(lambda: self.handle_message(client))
        self.clients.append(client)

    def handle_message(self, client):
        data = client.readAll().data().decode('utf-8')
        request = json.loads(data)

        # Process request and interact with Krita
        match request['action']:
            case 'get_layer_text':
                doc = Krita.instance().activeDocument()
                layer_name = request.get('layer_name')

                if not doc:
                    response = {'success': False,
                                'error': 'No active document'}
                else:
                    try:
                        # Get all text from vector layers
                        text_data = get_all_vector_text()
                        response = {'success': True, 'text_layers': text_data}
                    except Exception as e:
                        response = {'success': False, 'error': str(e)}
                client.write(json.dumps(response).encode('utf-8'))

            case 'update_layer_text':
                doc = Krita.instance().activeDocument()
                updates = request.get('updates', [])

                if not doc:
                    response = {'success': False,
                                'error': 'No active document'}
                else:
                    try:
                        # Update text in the .kra file
                        from .utils import update_text_in_kra
                        result = update_text_in_kra(doc, updates)
                        response = {'success': True, 'updated_count': result}
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
