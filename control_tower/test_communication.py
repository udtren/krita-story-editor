"""
Test script for the Krita Docker <-> Standalone Tool communication
This demonstrates how to test the communication between the docker and control tower.
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QLabel
from PyQt5.QtNetwork import QLocalSocket
from PyQt5.QtCore import QTimer
import json
import sys


class TestControlTower(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Tower - Communication Test")
        self.resize(500, 400)
        
        # Set up socket
        self.socket = QLocalSocket(self)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_data_received)
        self.socket.errorOccurred.connect(self.on_error)
        
        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Connection status
        self.status_label = QLabel("Status: Not Connected")
        layout.addWidget(self.status_label)
        
        # Connect button
        self.connect_btn = QPushButton("Connect to Krita Docker")
        self.connect_btn.clicked.connect(self.connect_to_docker)
        layout.addWidget(self.connect_btn)
        
        # Test button
        self.test_btn = QPushButton("Test: Get Document Name")
        self.test_btn.clicked.connect(self.test_get_document_name)
        self.test_btn.setEnabled(False)
        layout.addWidget(self.test_btn)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        self.log("Application started. Click 'Connect to Krita Docker' to begin.")
    
    def log(self, message):
        """Add a message to the log output"""
        self.log_output.append(f"[LOG] {message}")
    
    def connect_to_docker(self):
        """Connect to the Krita docker's local server"""
        self.log("Attempting to connect to 'krita_story_editor_bridge'...")
        self.socket.connectToServer("krita_story_editor_bridge")
        
        # Give it a moment to connect
        QTimer.singleShot(1000, self.check_connection)
    
    def check_connection(self):
        """Check if connection was successful"""
        if self.socket.state() != QLocalSocket.LocalSocketState.ConnectedState:
            self.log("⚠️ Connection failed! Make sure:")
            self.log("  1. Krita is running")
            self.log("  2. The Story Editor Agent docker is loaded")
            self.log("  3. The docker is visible in Krita's workspace")
    
    def on_connected(self):
        """Called when successfully connected"""
        self.log("✅ Connected to Krita docker!")
        self.status_label.setText("Status: Connected")
        self.status_label.setStyleSheet("color: green;")
        self.connect_btn.setEnabled(False)
        self.test_btn.setEnabled(True)
    
    def on_disconnected(self):
        """Called when disconnected"""
        self.log("❌ Disconnected from Krita docker")
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("color: red;")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(False)
    
    def on_error(self, error):
        """Called when socket error occurs"""
        error_msg = self.socket.errorString()
        self.log(f"❌ Socket Error: {error_msg}")
    
    def send_request(self, action, **params):
        """Send a request to the Krita docker"""
        request = {'action': action, **params}
        json_data = json.dumps(request)
        self.log(f"📤 Sending: {json_data}")
        self.socket.write(json_data.encode('utf-8'))
        self.socket.flush()
    
    def on_data_received(self):
        """Handle data received from the Krita docker"""
        data = self.socket.readAll().data().decode('utf-8')
        self.log(f"📥 Received: {data}")
        
        try:
            response = json.loads(data)
            self.log(f"✅ Parsed response: {response}")
        except json.JSONDecodeError as e:
            self.log(f"⚠️ Failed to parse JSON: {e}")
    
    def test_get_document_name(self):
        """Test the get_document_name action"""
        self.log("\n--- Testing get_document_name ---")
        self.send_request('get_document_name')


def main():
    app = QApplication(sys.argv)
    window = TestControlTower()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
