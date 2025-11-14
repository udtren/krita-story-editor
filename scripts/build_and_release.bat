@echo off
echo ====================================
echo Story Editor - Full Build and Release
echo ====================================
echo.
echo This will:
echo 1. Build the executable
echo 2. Create distribution package
echo.
pause

REM Change to scripts directory where this file is located
cd /d "%~dp0"

echo.
echo ====================================
echo Step 1: Building Executable
echo ====================================
call build.bat

if errorlevel 1 (
    echo.
    echo ❌ Build failed! Aborting.
    pause
    exit /b 1
)

echo.
echo.
echo ====================================
echo Step 2: Creating Distribution Package
echo ====================================
call create_release.bat

echo.
echo.
echo ====================================
echo ✅ Complete!
echo ====================================
echo.
echo Your distribution package is ready in the 'release' folder
echo.
pause
