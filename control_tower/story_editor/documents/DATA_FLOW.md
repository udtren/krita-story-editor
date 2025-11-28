# Story Editor Data Flow Documentation

## Overview

This document explains how data flows through the Story Editor, from receiving SVG data from Krita to saving edited text back to the documents.

---

## 1. Opening the Story Editor

```
User clicks "Open Story Editor"
    ↓
StoryEditorWindow.show_text_editor()
    ↓
Socket request: "get_all_docs_svg_data"
    ↓
Krita Plugin collects data from all open .kra documents
    ↓
Returns: all_docs_svg_data (List[Dict])
    ↓
StoryEditorWindow.set_svg_data(all_docs_svg_data)
    ↓
create_text_editor_window() builds UI
```

---

## 2. Data Structure: all_docs_svg_data

**Type:** `List[Dict[str, Any]]`

**Source:** Received from Krita plugin via socket

**Purpose:** Read-only source data containing all documents and their text layers

**Example:**
```python
[
    {
        'document_name': 'Test001.kra',
        'document_path': 'C:\\Users\\...\\Test001.kra',
        'svg_data': [
            {
                'layer_name': 'layer2.shapelayer',
                'layer_id': 'layer2.shapelayer',
                'svg': '<svg width="344.76pt" height="193.56pt" viewBox="0 0 344.76 193.56">\n'
                       '<text id="shape807b_0" krita:textVersion="3" '
                       'transform="translate(44.52, 44.380625)" '
                       'fill="#ffffff" stroke="#000000" stroke-width="0" '
                       'style="font-size: 8;">MY_TEXT</text>\n</svg>'
            }
        ],
        'opened': False,  # Document status in Krita
        'thumbnail': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...'
    }
]
```

**Field Descriptions:**
- `document_name`: Filename of the .kra document
- `document_path`: Absolute path to the .kra file
- `svg_data`: List of text layers, each containing SVG XML
- `opened`: Boolean indicating if document is currently open in Krita
- `thumbnail`: Base64-encoded PNG image (data URI format)

---

## 3. UI Creation Process

```
create_text_editor_window()
    ↓
For each doc_data in all_docs_svg_data:
    ↓
    _create_document_section(doc_data)
        ↓
        ├─→ create_thumbnail_section()
        │       ├─→ create_thumbnail_label(thumbnail)
        │       │       └─→ decode_base64_thumbnail()
        │       └─→ create_document_status_label(opened)
        │
        ├─→ create_activate_button(doc_name, opened)
        │
        ├─→ _initialize_document_state(doc_name, doc_path, opened)
        │       └─→ Creates entry in all_docs_text_state
        │
        └─→ populate_layer_editors(svg_data)
                ↓
                For each layer in svg_data:
                    ↓
                    parse_krita_svg(svg)
                        ↓
                        Extracts: text_content, element_id, layer_shapes
                        ↓
                    create_text_editor_widget()
                        ↓
                        Creates QTextEdit with text_content
                        ↓
                    Store in all_docs_text_state
```

---

## 4. Data Structure: all_docs_text_state

**Type:** `Dict[str, Dict[str, Any]]`

**Purpose:** Editable state tracking user changes to text

**Created:** During UI creation from all_docs_svg_data

**Modified:** When user edits text or adds new text elements

**Example:**
```python
{
    'Test001.kra': {
        'document_name': 'Test001.kra',
        'document_path': 'C:\\Users\\...\\Test001.kra',
        'has_text_changes': False,
        'new_text_widgets': [],  # New text elements added by user
        'layer_groups': {
            'layer2.shapelayer': {
                'layer_name': 'layer2.shapelayer',
                'layer_id': 'layer2.shapelayer',
                'layer_shapes': [
                    {
                        'text_content': 'MY_TEXT',
                        'element_id': 'shape807b_0',
                        # ... other SVG attributes
                    }
                ],
                'svg_content': '<svg>...</svg>',  # Original SVG
                'changes': [
                    {
                        'new_text': QTextEdit,  # The actual widget
                        'shape_id': 'shape807b_0'
                    }
                ]
            }
        },
        'opened': False,
        'text_edit_widgets': [  # For find/replace functionality
            {
                'widget': QTextEdit,
                'document_name': 'Test001.kra',
                'layer_name': 'layer2.shapelayer',
                'layer_id': 'layer2.shapelayer',
                'shape_id': 'shape807b_0'
            }
        ]
    }
}
```

---

## 5. User Editing Process

```
User types in QTextEdit widget
    ↓
Text changed in widget
    ↓
Widget reference stored in:
    all_docs_text_state[doc_name]['layer_groups'][layer_id]['changes']
    ↓
When user clicks "Save" or "Update Krita":
    ↓
send_merged_svg_request()
```

---

## 6. Saving Changes Back to Krita

```
send_merged_svg_request()
    ↓
For each doc in all_docs_text_state:
    ↓
    create_svg_data_for_doc()
        ↓
        For each layer_group:
            ↓
            Read text from QTextEdit widget
                ↓
            Generate new SVG with updated text
                ↓
            Create update request
        ↓
        Collect all updates for this document
    ↓
Send merged_requests to Krita via socket
    ↓
Krita updates text in .kra documents
```

---

## 7. Key Transformations

### SVG → Editable Text

```python
# Input: SVG XML string
svg = '<svg><text id="shape807b_0">MY_TEXT</text></svg>'

# Process: parse_krita_svg()
parsed = parse_krita_svg(doc_name, doc_path, layer_id, svg)

# Output: Structured data
{
    'layer_shapes': [
        {
            'text_content': 'MY_TEXT',      # ← User edits this
            'element_id': 'shape807b_0',
            'transform': 'translate(44.52, 44.380625)',
            'fill': '#ffffff',
            # ... other attributes
        }
    ]
}
```

### Edited Text → SVG

```python
# Input: User's edited text from QTextEdit
new_text = text_edit.toPlainText()  # "UPDATED TEXT"

# Process: create_svg_data_for_doc()
# Reconstructs SVG with new text
new_svg = '<svg><text id="shape807b_0">UPDATED TEXT</text></svg>'

# Output: Update request sent to Krita
{
    'layer_name': 'layer2.shapelayer',
    'layer_id': 'layer2.shapelayer',
    'svg_data': new_svg
}
```

### Thumbnail Display

```python
# Input: Base64 data URI
thumbnail = 'data:image/png;base64,iVBORw0KGgo...'

# Process: decode_base64_thumbnail()
# 1. Remove prefix: 'data:image/png;base64,'
# 2. Decode: base64.b64decode() → bytes
# 3. Load: QPixmap.loadFromData()
# 4. Scale: pixmap.scaledToWidth()

# Output: QPixmap displayed in QLabel
```

---

## 8. Module Responsibilities

| Module | Input | Output | Purpose |
|--------|-------|--------|---------|
| `main_editor_window.py` | Socket data | UI window | Orchestrates overall flow |
| `scroll_areas.py` | Window ref | Scroll widgets | Creates layout containers |
| `thumbnail.py` | Base64 image | QLabel | Displays document thumbnails |
| `text_editor.py` | SVG data | QTextEdit | Creates editable text fields |
| `document.py` | doc_data | Complete UI | Assembles document sections |

---

## 9. Common Operations

### Adding New Text
```
User clicks "Add New Text"
    ↓
add_new_text_widget()
    ↓
Creates empty QTextEdit
    ↓
Stores in all_docs_text_state[doc_name]['new_text_widgets']
    ↓
On save: Generates new SVG text element
```

### Find/Replace
```
User opens Find/Replace dialog
    ↓
show_find_replace_dialog(all_docs_text_state)
    ↓
Iterates through all text_edit_widgets
    ↓
Searches/replaces text in QTextEdit widgets
```

### Refresh Data
```
User clicks "Refresh"
    ↓
refresh_data()
    ↓
Calls show_text_editor() again
    ↓
Fetches fresh data from Krita
    ↓
Rebuilds entire UI
```

---

## 10. State Management

### Read-Only State
- `all_docs_svg_data`: Never modified, used as source of truth

### Editable State
- `all_docs_text_state`: Modified as user edits
- QTextEdit widgets: Contain actual user input
- `doc_buttons`, `doc_thumbnails`: UI element references

### Transient State
- `thumbnail_scroll_position`: Preserved during refresh
- `content_scroll_position`: Preserved during refresh
- `active_doc_name`: Currently selected document

---

## Summary

The Story Editor uses a clear separation between:
1. **Source data** (`all_docs_svg_data`) - Read-only from Krita
2. **UI state** (`all_docs_text_state`) - Tracks user edits
3. **UI widgets** - Display and allow editing

This architecture ensures:
- Data integrity (source never corrupted)
- Easy refresh (rebuild from source)
- Clear editing flow (state tracks changes)
- Simple save (state → update requests)
