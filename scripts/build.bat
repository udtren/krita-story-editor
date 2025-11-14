@echo off
echo ====================================
echo Building Control Tower Executable
echo ====================================
echo.

REM Change to project root (parent of scripts)
cd /d "%~dp0.."

REM Activate virtual environment (in control_tower folder)
if exist "control_tower\venv\Scripts\activate.bat" (
    call control_tower\venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run from control_tower: python -m venv venv
    echo Then run: .\venv\Scripts\Activate.ps1
    echo And install: pip install -r requirements.txt pyinstaller
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Check if Pillow is installed (for icon conversion)
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Pillow not found. Installing for icon support...
    pip install Pillow
)

REM Run the build script from scripts folder
echo.
echo Running build script...
python scripts\build_executable.py

echo.
echo ====================================
echo Build process completed!
echo ====================================
pause
