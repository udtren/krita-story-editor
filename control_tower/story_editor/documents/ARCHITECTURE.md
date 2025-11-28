# Story Editor Architecture

## Visual Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                                                                   │
│  ┌─────────────┐  ┌──────────────────────────────────────────┐ │
│  │ Thumbnails  │  │          Document Content                 │ │
│  │  (Grid)     │  │                                          │ │
│  │             │  │  ┌────────────────────────────────────┐  │ │
│  │ [Doc1.kra]  │  │  │ [Activate Button]                  │  │ │
│  │   Opened    │  │  │                                    │  │ │
│  │             │  │  │  ┌──────────────────────────────┐  │  │ │
│  │ [Doc2.kra]  │  │  │  │ Layer: layer1.shapelayer    │  │  │ │
│  │   Closed    │  │  │  │ ┌──────────────────────────┐ │  │  │ │
│  │             │  │  │  │ │ QTextEdit: "MY_TEXT"    │ │  │  │ │
│  │ [Doc3.kra]  │  │  │  │ └──────────────────────────┘ │  │  │ │
│  │   Opened    │  │  │  │                             │  │  │ │
│  │             │  │  │  │ Layer: layer2.shapelayer    │  │  │ │
│  └─────────────┘  │  │  │ ┌──────────────────────────┐ │  │  │ │
│                    │  │  │ │ QTextEdit: "MORE TEXT"  │ │  │  │ │
│                    │  │  │ └──────────────────────────┘ │  │  │ │
│                    │  │  └──────────────────────────────┘  │  │ │
│                    │  └────────────────────────────────────┘  │ │
│                    └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │
                          Data flows through
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      StoryEditorWindow                           │
│                    (main_editor_window.py)                       │
│                                                                   │
│  State Management:                                               │
│  ┌────────────────────┐  ┌──────────────────────────────┐      │
│  │ all_docs_svg_data  │  │   all_docs_text_state        │      │
│  │  (Read-only)       │  │    (Editable)                │      │
│  │                    │  │                              │      │
│  │  From Krita ─────► │  │  ◄──── User Edits           │      │
│  │  via Socket        │  │                              │      │
│  └────────────────────┘  └──────────────────────────────┘      │
│           │                            │                         │
│           │                            │                         │
│           └──────────┬─────────────────┘                        │
│                      │                                           │
│              Delegates to UI Components                          │
│                      │                                           │
└──────────────────────┼───────────────────────────────────────────┘
                       │
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│scroll_areas │ │  thumbnail  │ │   document   │
│    .py      │ │     .py     │ │     .py      │
│             │ │             │ │              │
│ Creates:    │ │ Creates:    │ │ Creates:     │
│ • Thumbnail │ │ • Thumb     │ │ • Activate   │
│   scroll    │ │   labels    │ │   buttons    │
│ • Content   │ │ • Status    │ │ • Doc        │
│   scroll    │ │   labels    │ │   sections   │
└─────────────┘ └─────────────┘ └──────────────┘
                                       │
                                       │ Uses
                                       ▼
                              ┌──────────────┐
                              │ text_editor  │
                              │     .py      │
                              │              │
                              │ Creates:     │
                              │ • QTextEdit  │
                              │   widgets    │
                              │ • Populates  │
                              │   layers     │
                              └──────────────┘
```

---

## Data Flow Diagram

```
┌──────────┐
│  Krita   │
│  Plugin  │
└────┬─────┘
     │ Socket
     │ Communication
     │
     ▼
┌────────────────────────────────────────────────────┐
│            all_docs_svg_data                       │
│  [                                                 │
│    {                                               │
│      document_name: "Test001.kra"                 │
│      document_path: "C:\\...\\Test001.kra"        │
│      svg_data: [                                   │
│        {                                           │
│          layer_name: "layer2.shapelayer"          │
│          layer_id: "layer2.shapelayer"            │
│          svg: "<svg>...</svg>"  ◄── Contains text │
│        }                                           │
│      ]                                             │
│      opened: false                                 │
│      thumbnail: "data:image/png;base64,..."       │
│    }                                               │
│  ]                                                 │
└────────┬───────────────────────────────────────────┘
         │
         │ create_text_editor_window()
         │
         ▼
┌────────────────────────────────────────────────────┐
│         UI Creation Process                        │
│                                                    │
│  For each document:                                │
│    1. decode_base64_thumbnail()                    │
│       └─► QLabel with thumbnail                   │
│                                                    │
│    2. parse_krita_svg()                            │
│       └─► Extract text_content                    │
│                                                    │
│    3. create_text_editor_widget()                 │
│       └─► QTextEdit(text_content)                 │
│                                                    │
│    4. Store in all_docs_text_state                │
└────────┬───────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│         all_docs_text_state                        │
│  {                                                 │
│    "Test001.kra": {                                │
│      layer_groups: {                               │
│        "layer2.shapelayer": {                      │
│          changes: [                                │
│            {                                       │
│              new_text: QTextEdit ◄── User edits   │
│              shape_id: "shape807b_0"              │
│            }                                       │
│          ]                                         │
│        }                                           │
│      }                                             │
│    }                                               │
│  }                                                 │
└────────┬───────────────────────────────────────────┘
         │
         │ User clicks "Save"
         │
         ▼
┌────────────────────────────────────────────────────┐
│     send_merged_svg_request()                      │
│                                                    │
│  For each document:                                │
│    1. Read text from QTextEdit                     │
│    2. create_svg_data_for_doc()                    │
│       └─► Generate new SVG with updated text      │
│    3. Build update request                         │
└────────┬───────────────────────────────────────────┘
         │
         │ Socket
         │ Communication
         ▼
┌──────────┐
│  Krita   │
│  Plugin  │
│          │
│ Updates  │
│  .kra    │
│  files   │
└──────────┘
```

---

## Module Dependency Graph

```
┌────────────────────────────────────────┐
│      main_editor_window.py             │
│  (Orchestrator & State Manager)        │
└──────┬─────────────┬──────────────┬────┘
       │             │              │
       │             │              │
       ▼             ▼              ▼
┌─────────────┐ ┌──────────┐ ┌──────────────┐
│scroll_areas │ │thumbnail │ │  document    │
└─────────────┘ └──────────┘ └──────┬───────┘
                                     │
                                     │ imports
                   ┌─────────────────┼─────────────┐
                   │                 │             │
                   ▼                 ▼             ▼
            ┌──────────┐      ┌──────────┐  ┌──────────┐
            │thumbnail │      │text_editor│  │utils/    │
            │          │      │          │  │svg_parser│
            └──────────┘      └──────────┘  └──────────┘
```

---

## Component Responsibilities

### Core Components

```
┌──────────────────────────────────────────────────────────┐
│ main_editor_window.py                                    │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ • Window lifecycle (open/close)                         │
│ • Socket communication with Krita                       │
│ • State management (all_docs_svg_data, text_state)     │
│ • High-level UI orchestration                           │
│ • Event handling (clicks, saves, refreshes)             │
│                                                          │
│ Does NOT:                                                │
│ • Create UI widgets directly                            │
│ • Parse SVG                                              │
│ • Decode images                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ ui_components/document.py                                │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ • Create complete document sections                     │
│ • Coordinate thumbnail, button, and editor creation     │
│ • Initialize document state                             │
│ • Layout document UI                                     │
│                                                          │
│ Key Functions:                                           │
│ • create_document_section()                             │
│ • create_activate_button()                              │
│ • create_thumbnail_section()                            │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ ui_components/thumbnail.py                               │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ • Decode base64 images                                  │
│ • Create thumbnail QLabels                              │
│ • Create status labels (opened/closed)                  │
│ • Scale images to fit                                    │
│                                                          │
│ Key Functions:                                           │
│ • decode_base64_thumbnail()                             │
│ • create_thumbnail_label()                              │
│ • create_document_status_label()                        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ ui_components/text_editor.py                             │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ • Parse SVG to extract text                             │
│ • Create QTextEdit widgets                              │
│ • Populate all layers for a document                    │
│ • Store widget references in state                      │
│                                                          │
│ Key Functions:                                           │
│ • create_text_editor_widget()                           │
│ • populate_layer_editors()                              │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ ui_components/scroll_areas.py                            │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ • Create scroll containers                              │
│ • Configure scroll policies                             │
│ • Set up grid/vertical layouts                          │
│                                                          │
│ Key Functions:                                           │
│ • create_thumbnail_scroll_area()                        │
│ • create_content_scroll_area()                          │
└──────────────────────────────────────────────────────────┘
```

---

## State Transitions

```
┌─────────────┐
│   Initial   │
│   (Empty)   │
└──────┬──────┘
       │
       │ show_text_editor()
       ▼
┌─────────────┐
│  Fetching   │
│    Data     │
└──────┬──────┘
       │
       │ set_svg_data()
       ▼
┌─────────────┐
│  Building   │
│     UI      │
└──────┬──────┘
       │
       │ create_text_editor_window()
       ▼
┌─────────────┐
│   Ready     │ ◄────┐
│ (Editing)   │      │
└──────┬──────┘      │
       │             │
       │ User edits  │
       │             │
       │ refresh_data()
       ▼             │
┌─────────────┐      │
│   Saving    │      │
│  (Optional) │──────┘
└─────────────┘
       │
       │ send_merged_svg_request()
       ▼
┌─────────────┐
│  Complete   │
└─────────────┘
```

---

## Threading & Async Behavior

```
Main UI Thread
├── User interactions (typing, clicking)
├── Widget updates
└── QTimer for delayed scroll restore

Socket Thread (Krita Communication)
├── send_request("get_all_docs_svg_data")
├── Receives: all_docs_svg_data
├── send_request("docs_svg_update")
└── Receives: success/failure response

Note: All UI updates happen on main thread
      Socket communication is async but UI updates are synchronous
```

---

## Error Handling Flow

```
┌─────────────────┐
│ Socket Request  │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Success│ ──► set_svg_data() ──► UI Created
    └────────┘
         │
         ▼
    ┌────────┐
    │  Error │ ──► Log warning ──► Show empty window
    └────────┘


┌─────────────────┐
│ Thumbnail Load  │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Success│ ──► Show image in QLabel
    └────────┘
         │
         ▼
    ┌────────┐
    │  Error │ ──► Show "No Preview" placeholder
    └────────┘
```

---

## Summary

This architecture achieves:

✅ **Separation of Concerns** - Each module has a clear, single purpose

✅ **Data Integrity** - Source data (all_docs_svg_data) never modified

✅ **Maintainability** - Changes isolated to specific modules

✅ **Testability** - UI components can be tested independently

✅ **Scalability** - Easy to add new document types or text formats

✅ **Performance** - Efficient state updates, minimal re-renders
