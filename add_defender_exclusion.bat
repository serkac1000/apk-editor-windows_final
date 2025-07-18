@echo off
title Add Windows Defender Exclusion for APK Editor
echo.
echo ===============================================
echo  Windows Defender Exclusion Setup
echo ===============================================
echo.
echo This script will add APK Editor to Windows Defender exclusions
echo to prevent false positive virus detections.
echo.
echo ⚠️  You may need to run this as Administrator
echo.
echo Current directory: %CD%
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul
echo.

echo Adding folder exclusion to Windows Defender...
powershell -Command "Add-MpPreference -ExclusionPath '%CD%'" 2>nul

if %errorlevel% equ 0 (
    echo ✅ Successfully added folder exclusion
) else (
    echo ❌ Failed to add exclusion - try running as Administrator
    echo.
    echo Manual steps:
    echo 1. Open Windows Security
    echo 2. Go to Virus ^& threat protection
    echo 3. Click "Manage settings" under Virus ^& threat protection settings
    echo 4. Click "Add or remove exclusions"
    echo 5. Add folder: %CD%
)

echo.
echo Adding process exclusion for Python...
powershell -Command "Add-MpPreference -ExclusionProcess 'python.exe'" 2>nul

if %errorlevel% equ 0 (
    echo ✅ Successfully added Python process exclusion
) else (
    echo ⚠️  Could not add Python process exclusion
)

echo.
echo ===============================================
echo  Exclusion Setup Complete
echo ===============================================
echo.
echo Your APK Editor should now run without antivirus warnings.
echo If you still get warnings, check ANTIVIRUS_GUIDE.md
echo.
pause