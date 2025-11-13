# Krita Story Editor

A tool for editing text layers in Krita documents through a separate window.

# Architecture
![alt text](images/architecture.png)

## Components

### Story Editor
The main window where you edit text content. Shows all text layers from your Krita documents in editable text boxes. Changes you make here can be sent back to Krita.

### Story Editor Agent
A plugin that runs inside Krita. It reads text data from your Krita documents and sends it to the Story Editor. When you update text, it writes the changes back to your Krita file.

### Story Editor Control Tower
The launcher application. Use this to:
- Connect to the Story Editor Agent running in Krita
- Open the Story Editor window
- Manage templates
- Change settings

### Templates
XML files that control how new text looks when added to Krita (font, size, color, position). You can create and edit templates to match your workflow.

## How to Use

1. Open Krita and load the Story Editor Agent docker
2. Run the Control Tower application
3. Click "Connect to Agent" to connect to Krita
4. Click "Open Story Editor" to start editing text
5. Make changes and click "Update Krita" to save them back to your document
