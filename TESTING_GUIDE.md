# Testing Communication Between Krita Docker and Standalone Tool

## Overview
Your plugin uses **QLocalSocket/QLocalServer** for Inter-Process Communication (IPC):
- **Docker (Server)**: Runs inside Krita, listens on `krita_story_editor_bridge`
- **Standalone Tool (Client)**: Connects to the server and sends requests

## Quick Test Steps

### Step 1: Install the Krita Plugin
1. Copy the `agent` folder to Krita's pykrita directory:
   - Windows: `%APPDATA%\krita\pykrita\`
   - Linux: `~/.local/share/krita/pykrita/`
   - macOS: `~/Library/Application Support/krita/pykrita/`

2. Create/edit `story-editor-agent.desktop` in the same directory:
```ini
[Desktop Entry]
Type=Service
ServiceTypes=Krita/PyKrita
X-KDE-Library=story_editor_agent
X-Python-2-Compatible=false
Name=Story Editor Agent
Comment=Communication bridge for story editor
```

### Step 2: Enable in Krita
1. Launch Krita
2. Go to **Settings → Configure Krita → Python Plugin Manager**
3. Enable **Story Editor Agent**
4. Restart Krita
5. Go to **Settings → Dockers** and enable **Story Editor Agent**
6. The docker should appear in your workspace

### Step 3: Run the Test Tool
Open a terminal in the `control_tower` directory and run:
```powershell
python test_communication.py
```

### Step 4: Test Communication
1. Click **"Connect to Krita Docker"**
2. If successful, you'll see "✅ Connected to Krita docker!"
3. Click **"Test: Get Document Name"** to send a test request
4. The log will show the request sent and response received

## Expected Output

### Successful Test:
```
[LOG] Application started. Click 'Connect to Krita Docker' to begin.
[LOG] Attempting to connect to 'krita_story_editor_bridge'...
[LOG] ✅ Connected to Krita docker!
[LOG] --- Testing get_document_name ---
[LOG] 📤 Sending: {"action": "get_document_name"}
[LOG] 📥 Received: {"name": "Untitled"}
[LOG] ✅ Parsed response: {'name': 'Untitled'}
```

### Failed Connection:
```
[LOG] ⚠️ Connection failed! Make sure:
[LOG]   1. Krita is running
[LOG]   2. The Story Editor Agent docker is loaded
[LOG]   3. The docker is visible in Krita's workspace
```

## Troubleshooting

### Problem: "Connection failed"
**Solutions:**
- Verify Krita is running
- Check that the plugin is enabled in Python Plugin Manager
- Ensure the docker is visible (Settings → Dockers → Story Editor Agent)
- Check Krita's Python console for errors (Settings → Show Python Console)

### Problem: "Server already in use"
**Solutions:**
- Close all Krita instances and restart
- On Windows, check Task Manager for lingering Krita processes
- The docker might have failed to clean up the socket

### Problem: No response from docker
**Solutions:**
- Add debug logging to `agent_docker.py`
- Check if the action handler exists in the docker
- Verify JSON format is correct

## Adding More Test Cases

Edit `test_communication.py` and add new test methods:

```python
def test_custom_action(self):
    """Test a custom action"""
    self.log("\n--- Testing custom_action ---")
    self.send_request('custom_action', param1='value1', param2='value2')
```

Then add a corresponding handler in `agent_docker.py`:

```python
elif request['action'] == 'custom_action':
    param1 = request.get('param1')
    param2 = request.get('param2')
    response = {'result': f'Got {param1} and {param2}'}
    client.write(json.dumps(response).encode('utf-8'))
```

## Manual Testing with Python REPL

You can also test manually from Python:

```python
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QLocalSocket
import json
import sys

app = QApplication(sys.argv)
socket = QLocalSocket()
socket.connectToServer("krita_story_editor_bridge")

# Wait for connection
socket.waitForConnected(1000)

# Send request
request = json.dumps({'action': 'get_document_name'})
socket.write(request.encode('utf-8'))
socket.flush()

# Wait for response
socket.waitForReadyRead(1000)
data = socket.readAll().data().decode('utf-8')
print(f"Response: {data}")
```

## Debug Mode

To add more detailed logging to the docker, modify `agent_docker.py`:

```python
def handle_message(self, client):
    data = client.readAll().data().decode('utf-8')
    print(f"[DOCKER] Received: {data}")  # Debug log
    request = json.loads(data)
    
    # ... handle request ...
    
    print(f"[DOCKER] Sending: {json.dumps(response)}")  # Debug log
    client.write(json.dumps(response).encode('utf-8'))
```

View these logs in Krita's Python Console (Settings → Show Python Console).
