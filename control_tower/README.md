# Control Tower - Krita Story Editor

## Setup

### Windows
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Linux/Mac
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

### Windows
```powershell
# Using helper script
.\run.ps1

# Or manually
.\venv\Scripts\Activate.ps1
python main_test.py
```

### Linux/Mac
```bash
# Using helper script
./run.sh

# Or manually
source venv/bin/activate
python main_test.py
```

## Building Executables

### Install PyInstaller
```bash
pip install pyinstaller
```

### Build for current platform
```bash
pyinstaller --onefile --windowed --name ControlTower main_test.py
```

The executable will be in the `dist/` folder.
