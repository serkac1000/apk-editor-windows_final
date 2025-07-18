@echo off
title APK Editor Diagnostics
color 0A

echo.
echo ===============================================
echo    APK Editor Diagnostics Tool
echo ===============================================
echo.
echo This tool will diagnose issues with the APK Editor
echo and help identify why it's getting stuck.
echo.
echo Press any key to start diagnostics...
pause >nul

echo.
echo Running diagnostics...
echo.

python debug_apk_editor.py

echo.
echo Diagnostics complete!
echo.
echo If issues were found, please check the log file:
echo apk_editor_debug.log
echo.
pause