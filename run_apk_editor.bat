@echo off
title APK Editor - Simplified Version
color 0A

echo.
echo ===============================================
echo    APK Editor - Simplified Version
echo ===============================================
echo.
echo This is a simplified version of the APK Editor
echo that focuses only on the core functionality.
echo.

REM Kill any existing Python processes that might be running the app
taskkill /F /IM python.exe /T 2>nul

echo Creating necessary directories...
mkdir uploads 2>nul
mkdir projects 2>nul
mkdir temp 2>nul
mkdir tools 2>nul

echo.
echo Starting APK Editor...
echo Open your browser to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python simple_app.py

echo.
echo APK Editor stopped
pause