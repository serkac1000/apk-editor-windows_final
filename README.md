# APK Editor

A web-based APK editor application built with Flask that allows users to upload, modify, and download APK files through a browser interface.

## ⚠️ IMPORTANT: Antivirus False Positive Notice

**This software may be flagged by antivirus programs as a potential threat. This is a FALSE POSITIVE.**

### Why This Happens:
- APK editors modify executable files (APK files)
- Downloads external development tools (APKTool)
- Creates temporary files and directories
- Performs operations similar to legitimate development tools

### This Tool Is Safe When:
- ✅ Downloaded from official/trusted sources
- ✅ Used for legitimate app development
- ✅ Used for educational purposes
- ✅ Source code is available for inspection

### How to Fix Antivirus Warnings:
1. **Add exclusions** to your antivirus software
2. **See ANTIVIRUS_GUIDE.md** for detailed instructions
3. **Use start_apk_editor.bat** for guided startup
4. **Verify the source code** (it's open source)

### DO NOT USE for:
- ❌ Modifying apps you don't own
- ❌ Bypassing app security measures  
- ❌ Any malicious purposes

## Features

- **Upload APK Files**: Upload APK files with custom project naming
- **Decompile APKs**: Extract resources including images, strings, and layouts
- **Edit Resources**: Web-based interface for editing:
  - Images (PNG, JPG, WEBP)
  - String resources (XML)
  - Layout files (XML)
- **Compile & Sign**: Recompile modified APKs and sign them
- **Download**: Download the final modified APK files
- **Project Management**: Track project status and manage multiple projects

## Installation

### Prerequisites

- Python 3.11+
- Java Runtime Environment (JRE) 8+ (for APKTool)
- APKTool (for actual APK operations)

### Quick Start

1. Install dependencies:
```bash
pip install flask flask-sqlalchemy werkzeug gunicorn psycopg2-binary email-validator
```

2. Run the application:
```bash
python main.py
```

3. Open your browser and go to `http://localhost:5000`

## Usage

1. **Upload APK**: Click "Upload APK" and select your APK file
2. **Edit Resources**: Browse and edit images, strings, and layouts
3. **Compile**: Click "Compile APK" to build your modified APK
4. **Download**: Download the final modified APK file

## Project Structure

```
apk-editor/
├── app.py              # Main Flask application
├── main.py             # Application entry point
├── apk_editor.py       # APK processing logic
├── utils/              # Utility classes
│   ├── apktool.py      # APKTool wrapper
│   └── file_manager.py # File management
├── templates/          # HTML templates
├── static/             # CSS and JavaScript files
├── projects/           # Project storage (created automatically)
├── uploads/            # Temporary uploads (created automatically)
└── temp/              # Temporary files (created automatically)
```

## Configuration

The application uses environment variables for configuration:

- `SESSION_SECRET`: Session secret key (default: dev-secret-key-change-in-production)

## Development

To run in development mode:

```bash
export FLASK_DEBUG=1
python main.py
```

## Notes

- Maximum file size: 100MB
- Supported file types: APK files only
- The application includes simulation mode when APKTool is not available
- All projects are stored locally in the `projects/` directory

## License

This project is for educational purposes. Ensure you have permission to modify APK files before using this tool.# apkeditorversion2
