@echo off
echo ====================================
echo Building Control Tower Executable
echo ====================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
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

REM Run the build script
echo.
echo Running build script...
python build_executable.py

echo.
echo ====================================
echo Build process completed!
echo ====================================
pause
