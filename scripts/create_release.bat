@echo off
echo ====================================
echo Creating Story Editor Release Package
echo ====================================
echo.

REM Change to project root (parent of scripts)
cd /d "%~dp0.."

REM Activate virtual environment (in control_tower folder)
if exist "control_tower\venv\Scripts\activate.bat" (
    call control_tower\venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run scripts\build.bat first
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "dist\StoryEditor.exe" (
    echo Error: StoryEditor.exe not found!
    echo.
    echo Please run scripts\build.bat first to create the executable
    pause
    exit /b 1
)

REM Run the distribution script from scripts folder
echo.
echo Creating distribution package...
python scripts\create_distribution.py

echo.
echo ====================================
echo Release creation completed!
echo ====================================
pause
