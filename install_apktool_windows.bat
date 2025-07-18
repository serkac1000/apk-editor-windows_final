
@echo off
echo APKTool Installer for Windows
echo =============================
echo.

echo Creating tools directory...
mkdir tools 2>nul

echo.
echo Checking for Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Java not found!
    echo Please install Java JDK 8 or later from:
    echo https://www.oracle.com/java/technologies/downloads/
    echo.
    pause
    exit /b 1
)

echo Java found!
echo.

echo Downloading APKTool...
echo.

echo Downloading apktool.bat...
powershell -Command "try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/windows/apktool.bat' -OutFile 'tools\apktool.bat' } catch { Write-Host 'Failed to download apktool.bat'; exit 1 }"

echo Downloading apktool.jar...
powershell -Command "try { Invoke-WebRequest -Uri 'https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar' -OutFile 'tools\apktool.jar' } catch { Write-Host 'Failed to download apktool.jar'; exit 1 }"

echo.
echo Verifying installation...
if exist "tools\apktool.jar" (
    if exist "tools\apktool.bat" (
        echo SUCCESS: APKTool installed successfully!
        echo Location: %CD%\tools\
        echo.
        echo You can now use the full APK editing features.
    ) else (
        echo ERROR: apktool.bat not found
    )
) else (
    echo ERROR: apktool.jar not found
)

echo.
pause
