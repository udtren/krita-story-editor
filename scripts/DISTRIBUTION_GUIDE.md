# Story Editor - Distribution Guide

## Overview

The Story Editor application uses a **separate user_data folder** to store persistent user files (templates and configs) outside of the executable. This ensures that user-created content persists between application restarts and updates.

## Folder Structure

```
project_root/
├── control_tower/           # Source code (for development)
│   ├── main.py
│   ├── config/
│   ├── story_editor/
│   ├── build.bat           # Build the executable
│   └── create_release.bat  # Create distribution package
│
└── user_data/              # Persistent user data (NOT bundled in .exe)
    ├── templates/          # User-created text templates (.xml files)
    └── config/            # Configuration files (.json)
        └── template.json  # Default template configuration
```

## Build Process

### Step 1: Build the Executable

```cmd
cd control_tower
build.bat
```

This creates `control_tower/dist/StoryEditor.exe`

### Step 2: Create Distribution Package

```cmd
create_release.bat
```

This creates:
- `control_tower/release/StoryEditor_v1.0_TIMESTAMP/` folder
- `control_tower/release/StoryEditor_v1.0_TIMESTAMP.zip` file

## Distribution Package Contents

```
StoryEditor_v1.0_TIMESTAMP/
├── StoryEditor.exe         # The standalone application
├── user_data/              # Persistent data folder
│   ├── templates/          # Template files
│   └── config/            # Configuration files
└── README.txt             # User installation instructions
```

## How It Works

### Development Mode (Running .py files)
- `app_paths.py` detects it's running from source
- Points to `project_root/user_data/`

### Executable Mode (Running .exe)
- `app_paths.py` detects it's running as executable
- Points to `{exe_location}/user_data/`

### Key Functions in `app_paths.py`:

```python
get_app_root()              # Returns the application root directory
get_text_templates_path()   # Returns user_data/templates/
get_config_path()           # Returns user_data/config/template.json
get_resource_path(path)     # Returns bundled resources (fonts, images)
```

## User Installation

Users should:
1. Extract the entire zip file
2. Keep `StoryEditor.exe` and `user_data/` folder together
3. Run `StoryEditor.exe`

## Updates

When releasing a new version:
1. Users keep their existing `user_data/` folder
2. Replace only the `StoryEditor.exe` file
3. All templates and configs are preserved

## Testing

### Test in Development Mode:
```bash
cd control_tower
python main.py
```
Should use `project_root/user_data/`

### Test in Executable Mode:
1. Build: `build.bat`
2. Copy `dist/StoryEditor.exe` to a new folder
3. Copy `user_data/` folder to the same location
4. Run `StoryEditor.exe`
5. Create a template, close app, restart
6. Template should persist

## Files Modified

### Path Management:
- **config/app_paths.py** - Centralized path management for both dev and exe modes

### Updated to Use Persistent Paths:
- **config/template_manager.py** - Uses `get_text_templates_path()` and `get_config_path()`
- **config/template_loader.py** - Uses `get_config_path()`
- **story_editor/widgets/new_text_edit.py** - Uses `get_text_templates_path()`

### Distribution Scripts:
- **create_distribution.py** - Creates release package
- **create_release.bat** - Wrapper script for Windows

## Troubleshooting

### Templates disappear after restart
- Make sure `user_data/` folder is in the same directory as `StoryEditor.exe`
- Check that the application has write permissions to `user_data/`

### Config file not found
- The app automatically creates `user_data/config/` and `user_data/templates/` on first run
- If missing, manually create these folders next to `StoryEditor.exe`

### Can't find templates in Template Manager
- Templates must be in `user_data/templates/` folder
- Must have `.xml` extension
- Must be in the same directory as the executable

## Summary

✅ **Persistent Data**: Templates and configs survive app restarts
✅ **Update Friendly**: Users keep their data when updating
✅ **Portable**: Can move the entire folder anywhere
✅ **Clean Separation**: User data separate from application code
