@echo off
echo ===============================================
echo APK Editor - Simplified Version
echo ===============================================
echo This is a simplified version of the APK Editor
echo that focuses only on the core functionality.

REM Kill any existing Python processes
taskkill /F /IM python.exe /T

REM Create necessary directories
echo Creating necessary directories...
mkdir uploads 2>nul
mkdir projects 2>nul
mkdir temp 2>nul
mkdir tools 2>nul
mkdir tools\keystores 2>nul

REM Start the application
echo Starting APK Editor...
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
python simple_app_fixed.py