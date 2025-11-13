# Krita Story Editor

A tool for editing text layers across multiple Krita documents, whether they are open or closed. Edit all your text content in one place and sync changes back to your files.

# Architecture
![alt text](images/architecture.png)

The tool has 3 main parts: the Story Editor for editing text, the Agent running inside Krita that handles document operations, and the Control Tower that connects them together and manages the data flow.

## Components

### Story Editor
The main editing window where you work with text content. It receives text data from the Agent and displays it in editable text boxes.

**Toolbar buttons:**
- **Add New Text Widget**  
  First, the target document need to be saved already. Activate your target document by clicking its name bar or thumbnail. Then click the Add button to create a new empty text widget at the bottom of that document's section. You can choose a template from the dropdown menu or use the default.

- **Refresh from Krita Document**  
  Clicking refresh makes the Agent send the latest data to the Story Editor. Use this when you manually edit or move text in Krita, or when you open or close documents.

- **Save All Opened Documents**  
  Saves all currently opened Krita documents.

- **Update Krita**  
  Sends all text data from the Story Editor to the Agent in Krita. The Agent then updates any Krita documents where text has been changed. The agent will then send latest krita document data to the story editor automatically.

**Text Edit Box:**

In Krita, each text layer is a vector layer containing SVG data. A vector layer can have one or more text shapes. For example, if you create a text in a vector layer, that's one shape. Adding another text to the same layer creates a second shape.

The Story Editor creates one text box for each shape in each document. If a Krita document has 2 text layers—one with 2 shapes and another with 1 shape—the Story Editor will display 3 text boxes.

When adding new text using "Add New Text Widget", you can create multiple shapes in a single Krita layer by separating them with three line breaks (press Enter three times).

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
