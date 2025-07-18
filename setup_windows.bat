@echo off
echo Setting up APK Editor for Windows...
echo.

echo Installing Python dependencies...
pip install flask flask-sqlalchemy werkzeug gunicorn psycopg2-binary email-validator

echo.
echo Creating directories...
mkdir uploads 2>nul
mkdir projects 2>nul
mkdir temp 2>nul

echo.
echo Setup complete!
echo.
echo Starting APK Editor...
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python main.py