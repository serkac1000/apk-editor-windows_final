# APK Editor

## Overview

This is a web-based APK (Android Package) editor built with Flask that allows users to upload, decompile, edit, and recompile Android APK files through a browser interface. The application provides a GUI-based approach to modifying APK files without requiring users to use command-line tools directly.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a traditional web application architecture pattern:

- **Frontend**: HTML templates with Bootstrap for styling and JavaScript for interactivity
- **Backend**: Flask web framework with Python
- **File System**: Local file storage for projects and temporary files
- **APK Processing**: Integration with APKTool for decompiling and recompiling APK files
- **No Database**: Uses JSON files for project metadata storage

## Key Components

### Backend Architecture

1. **Flask Web Server** (`app.py`, `main.py`)
   - Handles HTTP requests and responses
   - Manages file uploads and downloads
   - Serves static files and templates
   - Implements session management with flash messages

2. **APK Editor Core** (`apk_editor.py`)
   - Main business logic for APK processing
   - Manages project creation and metadata
   - Coordinates with APKTool for decompilation/compilation

3. **Utility Classes**
   - `APKTool` (`utils/apktool.py`): Wrapper for APKTool command-line operations
   - `FileManager` (`utils/file_manager.py`): Handles project file operations and metadata management

### Frontend Architecture

1. **Template System**
   - Jinja2 templates with Bootstrap dark theme
   - Responsive design with mobile support
   - Modular template structure (index, project view, resource editor)

2. **Static Assets**
   - CSS for custom styling (`static/css/style.css`)
   - JavaScript for form validation and UI interactions (`static/js/main.js`)
   - Bootstrap CDN for styling framework
   - Feather icons for consistent iconography

### File Storage Structure

```
projects/
├── {project_id}/
│   ├── metadata.json
│   ├── original.apk
│   ├── decompiled/
│   ├── compiled.apk (after compilation)
│   └── signed.apk (after signing)
uploads/
└── {temporary_apk_files}
temp/
└── {temporary_processing_files}
```

## Recent Changes

### July 18, 2025 - Added AI Function Generator
- ✓ Added prompt-based function generation interface
- ✓ Support for uploading design images for reference
- ✓ Intelligent code generation based on user descriptions
- ✓ Generated functions include Android XML layouts and Java code
- ✓ Support for buttons, colors, icons, and layout generation
- ✓ Code viewing, copying, and downloading functionality
- ✓ Windows deployment package with setup scripts

## Data Flow

1. **APK Upload**: User uploads APK file through web interface
2. **Project Creation**: System generates unique project ID and creates directory structure
3. **Decompilation**: APKTool extracts APK contents to decompiled folder
4. **Editing**: User can browse and edit resources through web interface
5. **AI Function Generation**: Users can describe new functions and generate Android code
6. **Compilation**: Modified resources are recompiled into new APK
7. **Signing**: APK is signed for installation (when implemented)

## External Dependencies

### Runtime Dependencies
- **Flask**: Web framework for Python
- **APKTool**: Command-line tool for APK decompilation/compilation
- **Java**: Required by APKTool for processing
- **Bootstrap**: Frontend CSS framework (loaded via CDN)
- **Feather Icons**: Icon library (loaded via CDN)

### Development Dependencies
- **Werkzeug**: WSGI utilities for Flask
- **Jinja2**: Template engine (included with Flask)

### System Requirements
- Python 3.6+
- Java Runtime Environment (JRE) 8+
- APKTool installed and accessible in PATH

## Deployment Strategy

### Local Development
- Flask development server with debug mode
- Direct file system access for uploads and projects
- No external database required

### Production Considerations
- **File Storage**: Current implementation uses local file system
- **Scalability**: Single-instance application with no horizontal scaling support
- **Security**: Basic file validation, no user authentication implemented
- **Performance**: Synchronous processing may block for large APK files

### Configuration
- Environment variables for session secrets
- Configurable upload limits (100MB default)
- Flexible directory structure for different deployment environments

## Key Architectural Decisions

### File-Based Storage
- **Problem**: Need to store project metadata and files
- **Solution**: JSON files for metadata, filesystem for project data
- **Rationale**: Simplifies deployment, no database setup required
- **Trade-off**: Limited querying capabilities, potential concurrency issues

### Synchronous Processing
- **Problem**: APK processing can take time
- **Solution**: Synchronous processing with loading indicators
- **Rationale**: Simpler implementation, fewer moving parts
- **Trade-off**: UI may become unresponsive during processing

### Web-Based Interface
- **Problem**: Make APK editing accessible to non-technical users
- **Solution**: Browser-based GUI with familiar form controls
- **Rationale**: Cross-platform compatibility, no client installation
- **Trade-off**: Limited compared to desktop applications

### APKTool Integration
- **Problem**: Need to decompile and recompile APK files
- **Solution**: Wrapper around APKTool command-line utility
- **Rationale**: Leverages mature, well-tested tool
- **Trade-off**: External dependency, requires Java installation