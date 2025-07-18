import os
import sys
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apk_editor_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("APKEditorDebug")

def debug_step(step_name):
    """Log a debug step with clear formatting"""
    logger.info(f"{'='*20} {step_name} {'='*20}")

def check_directory(path):
    """Check if directory exists and is writable"""
    debug_step(f"Checking directory: {path}")
    
    if not os.path.exists(path):
        logger.warning(f"Directory does not exist: {path}")
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory: {path}")
            logger.error(f"Error: {str(e)}")
            return False
    
    # Check if directory is writable
    test_file = os.path.join(path, f"test_write_{datetime.now().strftime('%Y%m%d%H%M%S')}.tmp")
    try:
        with open(test_file, 'w') as f:
            f.write("Test write")
        os.remove(test_file)
        logger.info(f"Directory is writable: {path}")
        return True
    except Exception as e:
        logger.error(f"Directory is not writable: {path}")
        logger.error(f"Error: {str(e)}")
        return False

def check_java():
    """Check if Java is installed and working"""
    debug_step("Checking Java installation")
    
    import subprocess
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Java is installed: {result.stderr.strip()}")
            return True
        else:
            logger.error("Java check failed")
            logger.error(f"Return code: {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            return False
    except Exception as e:
        logger.error("Failed to check Java")
        logger.error(f"Error: {str(e)}")
        return False

def check_apktool():
    """Check if APKTool is available"""
    debug_step("Checking APKTool")
    
    # Check common locations
    possible_paths = [
        './apktool.jar',
        './tools/apktool.jar',
        'tools/apktool.jar'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"APKTool found at: {path}")
            return path
    
    logger.warning("APKTool not found in common locations")
    return None

def test_file_manager():
    """Test FileManager initialization"""
    debug_step("Testing FileManager")
    
    try:
        from utils.file_manager import FileManager
        
        projects_folder = 'projects'
        if not os.path.exists(projects_folder):
            os.makedirs(projects_folder, exist_ok=True)
        
        logger.info("Initializing FileManager...")
        file_manager = FileManager(projects_folder)
        logger.info("FileManager initialized successfully")
        
        # Test listing projects
        logger.info("Testing list_projects method...")
        projects = file_manager.list_projects()
        logger.info(f"Found {len(projects)} projects")
        
        return True
    except Exception as e:
        logger.error("FileManager test failed")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_apktool_class():
    """Test APKTool class initialization"""
    debug_step("Testing APKTool class")
    
    try:
        from utils.apktool import APKTool
        
        logger.info("Initializing APKTool class...")
        apktool = APKTool()
        logger.info("APKTool class initialized successfully")
        
        # Check paths
        logger.info(f"APKTool path: {apktool.apktool_path}")
        logger.info(f"Java path: {apktool.java_path}")
        
        return True
    except Exception as e:
        logger.error("APKTool class test failed")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_apk_preview():
    """Test APKPreview initialization"""
    debug_step("Testing APKPreview")
    
    try:
        from utils.apk_preview import APKPreview
        
        temp_folder = 'temp'
        
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder, exist_ok=True)
        
        logger.info("Initializing APKPreview...")
        apk_preview = APKPreview(temp_folder)
        logger.info("APKPreview initialized successfully")
        
        return True
    except Exception as e:
        logger.error("APKPreview test failed")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_apk_editor():
    """Test APKEditor initialization step by step"""
    debug_step("Testing APKEditor step by step")
    
    try:
        # First test APKTool class separately
        if not test_apktool_class():
            logger.error("APKTool class test failed, cannot proceed with APKEditor test")
            return False
        
        # Import APKEditor
        logger.info("Importing APKEditor class...")
        from apk_editor import APKEditor
        logger.info("APKEditor class imported successfully")
        
        # Setup folders
        projects_folder = 'projects'
        temp_folder = 'temp'
        
        if not os.path.exists(projects_folder):
            os.makedirs(projects_folder, exist_ok=True)
        
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder, exist_ok=True)
        
        # Initialize APKEditor
        logger.info("Initializing APKEditor...")
        apk_editor = APKEditor(projects_folder, temp_folder)
        logger.info("APKEditor initialized successfully")
        
        # Check APKTool
        logger.info(f"APKTool path: {apk_editor.apktool.apktool_path}")
        logger.info(f"Java path: {apk_editor.apktool.java_path}")
        
        return True
    except Exception as e:
        logger.error("APKEditor test failed")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def run_diagnostics():
    """Run all diagnostic tests"""
    logger.info("Starting APK Editor diagnostics")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python version: {sys.version}")
    
    # Check directories
    uploads_ok = check_directory('uploads')
    projects_ok = check_directory('projects')
    temp_ok = check_directory('temp')
    tools_ok = check_directory('tools')
    
    # Check Java
    java_ok = check_java()
    
    # Check APKTool
    apktool_path = check_apktool()
    
    # Test components individually
    file_manager_ok = test_file_manager()
    apktool_class_ok = test_apktool_class()
    apk_preview_ok = test_apk_preview()
    
    # Test APKEditor last (most likely to fail)
    apk_editor_ok = test_apk_editor()
    
    # Print summary
    debug_step("Diagnostic Summary")
    logger.info(f"Uploads directory: {'✓' if uploads_ok else '✗'}")
    logger.info(f"Projects directory: {'✓' if projects_ok else '✗'}")
    logger.info(f"Temp directory: {'✓' if temp_ok else '✗'}")
    logger.info(f"Tools directory: {'✓' if tools_ok else '✗'}")
    logger.info(f"Java installation: {'✓' if java_ok else '✗'}")
    logger.info(f"APKTool found: {'✓' if apktool_path else '✗'}")
    logger.info(f"FileManager: {'✓' if file_manager_ok else '✗'}")
    logger.info(f"APKTool class: {'✓' if apktool_class_ok else '✗'}")
    logger.info(f"APKPreview: {'✓' if apk_preview_ok else '✗'}")
    logger.info(f"APKEditor: {'✓' if apk_editor_ok else '✗'}")
    
    # Overall status
    all_ok = all([uploads_ok, projects_ok, temp_ok, tools_ok, file_manager_ok, apk_editor_ok])
    logger.info(f"Overall status: {'✓' if all_ok else '✗'}")
    
    return all_ok

if __name__ == "__main__":
    success = run_diagnostics()
    
    if success:
        print("\n✅ All diagnostics passed! APK Editor should work correctly.")
    else:
        print("\n❌ Some diagnostics failed. Check the log file for details.")
        print("   Log file: apk_editor_debug.log")
        
        # Provide specific recommendations based on failures
        if not check_apktool():
            print("\n⚠️  APKTool not found! Please run install_apktool_windows.bat")
        
        if not check_java():
            print("\n⚠️  Java not found! Please install Java JDK 8 or later")
            print("   Download from: https://www.oracle.com/java/technologies/downloads/")