import os
import shutil
import zipfile
import logging
import json
from datetime import datetime

logger = logging.getLogger("APKEditor")

class APKPlusHandler:
    """Handler for APK+ format files"""
    
    def __init__(self, temp_folder):
        """Initialize the handler with a temp folder for processing"""
        self.temp_folder = temp_folder
        os.makedirs(temp_folder, exist_ok=True)
    
    def is_apk_plus(self, file_path):
        """Check if a file is in APK+ format"""
        try:
            # Check file extension
            if file_path.lower().endswith('.apk+'):
                return True
                
            # Check for APK+ signature in the file
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Check for APK+ metadata file
                if 'apk_plus_metadata.json' in zipf.namelist():
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error checking APK+ format: {str(e)}")
            return False
    
    def convert_to_apk_plus(self, apk_path):
        """Convert standard APK to APK+ format"""
        try:
            # Create output path
            output_path = apk_path.replace('.apk', '.apk+')
            if not output_path.endswith('.apk+'):
                output_path += '.apk+'
                
            # Create a temporary directory for processing
            temp_dir = os.path.join(self.temp_folder, f"apk_plus_{os.path.basename(apk_path)}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Extract APK contents
                with zipfile.ZipFile(apk_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Create APK+ metadata
                metadata = {
                    'original_apk': os.path.basename(apk_path),
                    'converted_at': datetime.now().isoformat(),
                    'format_version': '1.0',
                    'is_installable': False
                }
                
                # Save metadata to the extracted directory
                metadata_path = os.path.join(temp_dir, 'apk_plus_metadata.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Create APK+ file
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                logger.info(f"APK converted to APK+ format: {output_path}")
                return True, output_path
                
            finally:
                # Clean up temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            logger.error(f"Error converting to APK+: {str(e)}")
            return False, str(e)
    
    def create_installable_apk_plus(self, apk_path):
        """Create an installable APK+ file"""
        try:
            # First convert to regular APK+
            success, output_path = self.convert_to_apk_plus(apk_path)
            if not success:
                return False, output_path
            
            # Create a temporary directory for processing
            temp_dir = os.path.join(self.temp_folder, f"installable_{os.path.basename(apk_path)}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Extract APK+ contents
                with zipfile.ZipFile(output_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Update metadata to mark as installable
                metadata_path = os.path.join(temp_dir, 'apk_plus_metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    metadata['is_installable'] = True
                    metadata['original_apk_included'] = True
                    
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                
                # Include the original APK in the APK+ package
                original_apk_dir = os.path.join(temp_dir, 'original_apk')
                os.makedirs(original_apk_dir, exist_ok=True)
                shutil.copy2(apk_path, os.path.join(original_apk_dir, os.path.basename(apk_path)))
                
                # Create installable APK+ file
                installable_path = output_path.replace('.apk+', '_installable.apk+')
                with zipfile.ZipFile(installable_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                logger.info(f"Created installable APK+: {installable_path}")
                
                # Remove the non-installable version
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                return True, installable_path
                
            finally:
                # Clean up temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            logger.error(f"Error creating installable APK+: {str(e)}")
            return False, str(e)
    
    def convert_to_standard_apk(self, apk_plus_path):
        """Convert APK+ format back to standard APK"""
        try:
            # Create output path
            output_path = apk_plus_path.replace('.apk+', '.apk')
            if output_path == apk_plus_path:  # If no extension change happened
                output_path = apk_plus_path + '.converted.apk'
                
            # Create a temporary directory for processing
            temp_dir = os.path.join(self.temp_folder, f"std_apk_{os.path.basename(apk_plus_path)}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Extract APK+ contents
                with zipfile.ZipFile(apk_plus_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Check if this is an installable APK+ with the original APK included
                metadata_path = os.path.join(temp_dir, 'apk_plus_metadata.json')
                original_apk_included = False
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        original_apk_included = metadata.get('original_apk_included', False)
                        original_apk_name = metadata.get('original_apk', '')
                        
                        if original_apk_included and original_apk_name:
                            original_apk_path = os.path.join(temp_dir, 'original_apk', original_apk_name)
                            if os.path.exists(original_apk_path):
                                # Simply copy the original APK
                                shutil.copy2(original_apk_path, output_path)
                                logger.info(f"Restored original APK from APK+: {output_path}")
                                return True, output_path
                    except Exception as e:
                        logger.error(f"Error reading APK+ metadata: {str(e)}")
                
                # If no original APK or not installable, create a new APK from the contents
                # Remove APK+ specific files
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                original_apk_dir = os.path.join(temp_dir, 'original_apk')
                if os.path.exists(original_apk_dir):
                    shutil.rmtree(original_apk_dir)
                
                # Create standard APK file
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # First add AndroidManifest.xml if it exists
                    manifest_path = os.path.join(temp_dir, "AndroidManifest.xml")
                    if os.path.exists(manifest_path):
                        zipf.write(manifest_path, "AndroidManifest.xml")
                    
                    # Then add classes.dex files
                    for dex_file in ["classes.dex", "classes2.dex", "classes3.dex"]:
                        dex_path = os.path.join(temp_dir, dex_file)
                        if os.path.exists(dex_path):
                            zipf.write(dex_path, dex_file)
                    
                    # Then add resources.arsc
                    resources_path = os.path.join(temp_dir, "resources.arsc")
                    if os.path.exists(resources_path):
                        zipf.write(resources_path, "resources.arsc")
                    
                    # Add all other files
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            
                            # Skip files we've already added or APK+ specific files
                            if arcname in ["AndroidManifest.xml", "classes.dex", "classes2.dex", "classes3.dex", "resources.arsc", "apk_plus_metadata.json"]:
                                continue
                            
                            # Skip original_apk directory
                            if arcname.startswith('original_apk/'):
                                continue
                            
                            zipf.write(file_path, arcname)
                
                logger.info(f"APK+ converted to standard APK: {output_path}")
                return True, output_path
                
            finally:
                # Clean up temp directory
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        except Exception as e:
            logger.error(f"Error converting to standard APK: {str(e)}")
            return False, str(e)