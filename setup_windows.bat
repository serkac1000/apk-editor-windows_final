@echo off
echo ===============================================
echo APK Editor Setup for Windows
echo ===============================================
echo.
echo IMPORTANT: If your antivirus flags this as a virus,
echo it's a FALSE POSITIVE. APK editors are flagged because
echo they modify executable files (APKs).
echo.
echo Please add this folder to your antivirus exclusions:
echo %CD%
echo.
echo See ANTIVIRUS_GUIDE.md for detailed instructions.
echo.
pause
echo.
echo Setting up APK Editor for Windows...
echo.

echo Installing Python dependencies...
pip install flask flask-sqlalchemy werkzeug gunicorn psycopg2-binary email-validator

echo.
echo Creating directories...
mkdir uploads 2>nul
mkdir projects 2>nul
mkdir temp 2>nul
mkdir tools 2>nul

echo.
echo Checking for Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Java not found! Please install Java JDK 8 or later.
    echo Download from: https://www.oracle.com/java/technologies/downloads/
    echo.
)

echo.
echo Checking for APKTool...
if not exist "tools\apktool.jar" (
    echo APKTool not found. Would you like to download it? (y/n)
    set /p choice=
    if /i "%choice%"=="y" (
        echo Downloading APKTool...
        powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/windows/apktool.bat' -OutFile 'tools\apktool.bat'"
        powershell -Command "Invoke-WebRequest -Uri 'https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.9.3.jar' -OutFile 'tools\apktool.jar'"
        echo APKTool downloaded successfully!
        echo.
    )
) else (
    echo APKTool found!
)

echo.
echo Setup complete!
echo.
echo Starting APK Editor...
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python main.py