# Building Control Tower as Standalone Executable

This guide explains how to build Control Tower into a single executable file that users can run without installing Python or dependencies.

## Prerequisites

- Python 3.8 or higher
- Virtual environment with dependencies installed

## Quick Build (Windows)

### Option 1: Using the Build Script (Easiest)

1. **Run the build batch file:**
   ```cmd
   build.bat
   ```

   This will automatically:
   - Activate the virtual environment
   - Install PyInstaller if needed
   - Build the executable
   - Show the output location

2. **Find your executable:**
   - Location: `dist\ControlTower.exe`
   - This is a standalone file - just distribute this one file!

### Option 2: Manual Build

1. **Activate virtual environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

3. **Run the build script:**
   ```bash
   python build_executable.py
   ```

4. **Or use PyInstaller directly:**
   ```bash
   pyinstaller --onefile --windowed --name ControlTower ^
       --add-data "config;config" ^
       --add-data "fonts;fonts" ^
       --add-data "images;images" ^
       --add-data "story_editor;story_editor" ^
       main.py
   ```

## Linux/Mac Build

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

3. **Build:**
   ```bash
   pyinstaller --onefile --windowed --name ControlTower \
       --add-data "config:config" \
       --add-data "fonts:fonts" \
       --add-data "images:images" \
       --add-data "story_editor:story_editor" \
       main.py
   ```

## Output

After building, you'll find:

- **Executable:** `dist/ControlTower.exe` (Windows) or `dist/ControlTower` (Linux/Mac)
- **Build files:** `build/` directory (can be deleted)
- **Spec file:** `ControlTower.spec` (can be deleted or kept for future builds)

## Distribution

### Creating a Release Package

After building the executable, create a distribution package:

**Windows:**
```cmd
create_release.bat
```

**Manual:**
```bash
python create_distribution.py
```

This creates a folder and zip file containing:
- `StoryEditor.exe` - The standalone application
- `user_data/` - Persistent configuration and template folder
- `README.txt` - Installation instructions for users

The zip file is ready to distribute to users!

### What's Included

**In the executable:**
- Python interpreter
- PyQt5 and all dependencies
- All your application code
- Bundled fonts and images

**In user_data/ folder:**
- `templates/` - User-created text templates (editable, persistent)
- `config/` - Configuration files (editable, persistent)

### Important: User Data Persistence

The `user_data` folder **must** be in the same directory as `StoryEditor.exe`. This folder:
- Persists between application restarts
- Contains user-editable templates and configs
- Should be kept when updating to new versions

## Troubleshooting

### Build fails with "module not found"

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try cleaning the build: Delete `build/` and `dist/` folders, then rebuild

### Executable won't run

- Check antivirus software (sometimes flags PyInstaller executables)
- Run from command line to see error messages
- Ensure all data files are being bundled (check the `--add-data` flags)

### Executable is too large

The single-file executable will be 50-100MB because it includes Python and PyQt5. This is normal.

To reduce size, you can use `--onedir` instead of `--onefile` to create a folder with the executable and dependencies (usually results in smaller total size but more files to distribute).

## Advanced: Custom Icon (Windows)

1. Convert `images/coffee_pixel.png` to `.ico` format
2. Update `build_executable.py` to use the `.ico` file
3. Rebuild

## Notes

- **First run may be slow:** The executable needs to extract files on first run
- **Antivirus warnings:** Some antivirus software may flag PyInstaller executables as suspicious (false positive)
- **Platform-specific:** Build on Windows for Windows, Linux for Linux, etc.
- **Size:** Expect 50-100MB for the executable (includes Python runtime + PyQt5)
