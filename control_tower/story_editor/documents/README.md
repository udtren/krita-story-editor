# Story Editor Module

A modular, well-documented text editor for Krita documents with SVG text layers.

## Quick Start

```python
from story_editor.main_editor_window import StoryEditorWindow

# Create editor instance
editor = StoryEditorWindow(parent, socket_handler)

# Set parent window
editor.set_parent_window(parent_window)

# Show editor (fetches data from Krita)
editor.show_text_editor()
```

## Documentation

- **[DATA_FLOW.md](DATA_FLOW.md)** - Detailed data flow documentation with examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Visual architecture diagrams and component overview

## Module Structure

```
story_editor/
├── main_editor_window.py          # Core orchestrator (561 lines)
├── ui_components/                  # Modular UI components
│   ├── __init__.py                # Package exports
│   ├── scroll_areas.py            # Scroll area creation (88 lines)
│   ├── thumbnail.py               # Thumbnail widgets (152 lines)
│   ├── text_editor.py             # Text editor widgets (123 lines)
│   └── document.py                # Document sections (259 lines)
├── utils/                          # Utilities
│   ├── text_updater.py            # SVG update logic
│   └── svg_parser.py              # SVG parsing
├── widgets/                        # Custom widgets
│   ├── vertical_label.py          # Status labels
│   ├── find_replace.py            # Find/replace dialog
│   └── story_board_window.py      # Thumbnail overview
├── DATA_FLOW.md                   # Data flow documentation
├── ARCHITECTURE.md                # Architecture diagrams
└── README.md                      # This file
```

## Key Concepts

### Data Structures

#### all_docs_svg_data (Input from Krita)
```python
[{
    'document_name': 'Test001.kra',
    'document_path': 'C:\\...\\Test001.kra',
    'svg_data': [
        {
            'layer_name': 'layer2.shapelayer',
            'layer_id': 'layer2.shapelayer',
            'svg': '<svg>...</svg>'  # Contains text elements
        }
    ],
    'opened': False,
    'thumbnail': 'data:image/png;base64,...'
}]
```

#### all_docs_text_state (Editable State)
```python
{
    'Test001.kra': {
        'document_name': 'Test001.kra',
        'document_path': 'C:\\...\\Test001.kra',
        'layer_groups': {
            'layer2.shapelayer': {
                'changes': [
                    {
                        'new_text': QTextEdit,  # User edits here
                        'shape_id': 'shape807b_0'
                    }
                ]
            }
        },
        'new_text_widgets': [],  # Newly added text
        'text_edit_widgets': []  # For find/replace
    }
}
```

### Data Flow

1. **Fetch** → `show_text_editor()` requests data from Krita
2. **Receive** → `set_svg_data()` stores all_docs_svg_data
3. **Build UI** → `create_text_editor_window()` creates widgets
4. **Edit** → User modifies text in QTextEdit widgets
5. **Save** → `send_merged_svg_request()` updates Krita documents

## UI Components

### scroll_areas.py
Creates scroll containers for thumbnails and content.

```python
from story_editor.ui_components import scroll_areas as ui_scroll

scroll_area, layout = ui_scroll.create_thumbnail_scroll_area(editor_window)
```

### thumbnail.py
Creates thumbnail labels and status indicators.

```python
from story_editor.ui_components.thumbnail import (
    create_thumbnail_label,
    create_document_status_label
)

thumb_label = create_thumbnail_label(doc_name, doc_path, thumbnail_data)
status_label = create_document_status_label(opened=True)
```

### text_editor.py
Creates text editor widgets and populates layers.

```python
from story_editor.ui_components.text_editor import (
    create_text_editor_widget,
    populate_layer_editors
)

text_edit = create_text_editor_widget(doc_name, layer_name, layer_id, layer_shape)
populate_layer_editors(doc_name, doc_path, svg_data, layout, state)
```

### document.py
Orchestrates creation of complete document sections.

```python
from story_editor.ui_components.document import create_document_section

create_document_section(index, doc_data, thumb_layout, content_layout, editor)
```

## Common Tasks

### Adding a New UI Component

1. Create file in `ui_components/`
2. Define factory functions (not classes)
3. Add comprehensive docstring with data structure examples
4. Export in `ui_components/__init__.py`
5. Import in `main_editor_window.py`

### Modifying Text Processing

1. Update `utils/svg_parser.py` for parsing changes
2. Update `ui_components/text_editor.py` for UI changes
3. Update `utils/text_updater.py` for save logic

### Adding New Document Actions

1. Add method in `main_editor_window.py`
2. Add menu item in `show_thumbnail_context_menu()`
3. Add socket request method (e.g., `send_xxx_request()`)

## Testing

### Manual Testing Checklist

- [ ] Open Story Editor
- [ ] Verify thumbnails display correctly
- [ ] Test document activation (clicking thumbnails/buttons)
- [ ] Edit text in various documents
- [ ] Test save functionality
- [ ] Test refresh (preserves scroll position)
- [ ] Test find/replace
- [ ] Test context menu actions (activate, open, close, etc.)
- [ ] Test with opened and closed documents

### Unit Testing (Future)

```python
# Example test structure
def test_create_thumbnail_label():
    label = create_thumbnail_label("Test.kra", "/path", None)
    assert label.text() == "No\nPreview"

def test_populate_layer_editors():
    state = {}
    populate_layer_editors("Doc", "/path", svg_data, layout, state)
    assert "Doc" in state
    assert len(state["Doc"]["layer_groups"]) > 0
```

## Performance Notes

- **Scroll position preservation**: Uses `QTimer.singleShot(100)` to restore after UI builds
- **Image decoding**: Thumbnails decoded once on load, cached in QPixmap
- **State updates**: Only modified documents sent to Krita on save
- **Widget creation**: Lazy - only creates visible widgets

## Debugging

### Enable Debug Logging

```python
from story_editor.utils.logs import write_log

# Uncomment write_log calls in:
# - text_editor.py: populate_layer_editors()
# - main_editor_window.py: send_merged_svg_request()
```

### Common Issues

**Issue**: Thumbnails show "No Preview"
- Check: `thumbnail` field is valid base64 data
- Check: Data URI prefix is present

**Issue**: Text not saving
- Check: `opened` is True for the document
- Check: Socket connection is active
- Check: all_docs_text_state has changes

**Issue**: Scroll position not preserved
- Check: `_save_current_scroll_positions()` called before rebuild
- Check: `_restore_scroll_positions()` called after show

## Code Style

- **Type hints**: All public functions have type hints
- **Docstrings**: All modules and functions documented
- **Constants**: UPPER_CASE at module level
- **Private methods**: Prefix with `_`
- **Factory functions**: Not classes (except main window)

## Future Enhancements

- [ ] Replace dict state with dataclass instances
- [ ] Add unit tests for ui_components
- [ ] Extract context menu to separate module
- [ ] Add undo/redo for text editing
- [ ] Support for more SVG text attributes (font, color, etc.)
- [ ] Batch operations (apply style to all, etc.)

## Contributing

When adding features:
1. Update relevant documentation (DATA_FLOW.md, ARCHITECTURE.md)
2. Add type hints
3. Follow existing code style
4. Keep functions small and focused
5. Update this README

## Version History

- **v2.0** (2025-01) - Modular refactoring, comprehensive documentation
- **v1.0** (2024-12) - Initial monolithic implementation

## License

See main project LICENSE file.
