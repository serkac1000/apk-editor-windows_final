@echo off
title APK Editor - Safe APK Development Tool
color 0A

echo.
echo ===============================================
echo    APK Editor - Safe APK Development Tool
echo ===============================================
echo.
echo Starting APK Editor with enhanced debugging...
echo.

REM Kill any existing Python processes that might be running the app
taskkill /F /IM python.exe /T 2>nul

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.8+ from python.org
    echo.
    pause
    exit /b 1
) else (
    echo Python found
)

REM Check Java
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Java not found - APK compilation will use simulation mode
    echo Install Java JDK 8+ for full functionality
) else (
    echo Java found
)

REM Create necessary directories
echo Creating necessary directories...
mkdir uploads 2>nul
mkdir projects 2>nul
mkdir temp 2>nul

echo.
echo Starting APK Editor in debug mode...
echo Web interface will open at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Run the simplified app with detailed error output
python simple_app.py

echo.
echo APK Editor stopped
pause