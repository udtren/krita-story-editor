@echo off
echo ====================================
echo Creating Story Editor Release Package
echo ====================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run build.bat first
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "dist\StoryEditor.exe" (
    echo Error: StoryEditor.exe not found!
    echo.
    echo Please run build.bat first to create the executable
    pause
    exit /b 1
)

REM Run the distribution script
echo.
echo Creating distribution package...
python create_distribution.py

echo.
echo ====================================
echo Release creation completed!
echo ====================================
pause
