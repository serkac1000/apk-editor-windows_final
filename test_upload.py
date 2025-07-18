import os
import sys
import logging
import zipfile
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_upload.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TestUpload")

def create_test_apk():
    """Create a simple test APK file (actually just a ZIP with APK extension)"""
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")
        
        # Create some dummy files
        with open(os.path.join(temp_dir, "AndroidManifest.xml"), "w") as f:
            f.write("<manifest></manifest>")
        
        os.makedirs(os.path.join(temp_dir, "res", "values"), exist_ok=True)
        with open(os.path.join(temp_dir, "res", "values", "strings.xml"), "w") as f:
            f.write("<resources><string name='app_name'>Test App</string></resources>")
        
        # Create a ZIP file with APK extension
        apk_path = os.path.join("uploads", "test_app.apk")
        with zipfile.ZipFile(apk_path, "w") as zipf:
            # Add files to the ZIP
            zipf.write(os.path.join(temp_dir, "AndroidManifest.xml"), "AndroidManifest.xml")
            zipf.write(os.path.join(temp_dir, "res", "values", "strings.xml"), "res/values/strings.xml")
        
        logger.info(f"Created test APK: {apk_path}")
        return apk_path
    
    except Exception as e:
        logger.error(f"Error creating test APK: {str(e)}")
        return None

def test_simple_decompile():
    """Test the simple_decompile_apk function"""
    try:
        # Import the function from app_fix.py
        sys.path.append(".")
        from app_fix import simple_decompile_apk
        
        # Create a test APK
        apk_path = create_test_apk()
        if not apk_path:
            logger.error("Failed to create test APK")
            return False
        
        # Create project directories
        os.makedirs("projects", exist_ok=True)
        
        # Test the function
        project_id = "test_project"
        project_name = "Test Project"
        
        logger.info(f"Testing simple_decompile_apk with project_id={project_id}, project_name={project_name}")
        result = simple_decompile_apk(apk_path, project_id, project_name)
        
        if result:
            logger.info("Test passed: simple_decompile_apk returned True")
            
            # Check if project directory was created
            project_dir = os.path.join("projects", project_id)
            if os.path.exists(project_dir):
                logger.info(f"Project directory created: {project_dir}")
                
                # Check if metadata.json was created
                metadata_path = os.path.join(project_dir, "metadata.json")
                if os.path.exists(metadata_path):
                    logger.info(f"Metadata file created: {metadata_path}")
                    return True
                else:
                    logger.error(f"Metadata file not created: {metadata_path}")
            else:
                logger.error(f"Project directory not created: {project_dir}")
        else:
            logger.error("Test failed: simple_decompile_apk returned False")
        
        return result
    
    except Exception as e:
        logger.error(f"Error testing simple_decompile_apk: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing APK upload functionality...")
    
    # Ensure directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("projects", exist_ok=True)
    
    # Test simple_decompile_apk
    if test_simple_decompile():
        print("\n✅ Test passed! The APK upload functionality works correctly.")
    else:
        print("\n❌ Test failed! Check the log file for details.")
        print("   Log file: test_upload.log")