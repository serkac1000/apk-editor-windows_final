import os
import logging
import json
import shutil
import zipfile
import subprocess
import base64
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apk_editor.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("APKEditor")

# Create Flask app
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROJECTS_FOLDER'] = 'projects'
app.config['TEMP_FOLDER'] = 'temp'
app.config['TOOLS_FOLDER'] = 'tools'
app.config['KEYSTORE_FOLDER'] = os.path.join('tools', 'keystores')

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROJECTS_FOLDER'], app.config['TEMP_FOLDER'], app.config['TOOLS_FOLDER'], app.config['KEYSTORE_FOLDER']]:
    os.makedirs(folder, exist_ok=True)
    logger.info(f"Directory created/verified: {folder}")

# Import the APK Signer module (with error handling)
try:
    from tools.apk_signer import APKSigner
    logger.info("APK Signer module imported successfully")
except ImportError as e:
    logger.warning(f"Could not import APK Signer module: {str(e)}")
    logger.warning("APK signing functionality will be limited")

def is_valid_apk(file_path):
    """Basic APK file validation"""
    try:
        # Check file size (not empty, not too large)
        file_size = os.path.getsize(file_path)
        if file_size < 1000 or file_size > 100 * 1024 * 1024:  # 1KB to 100MB
            logger.warning(f"Invalid APK size: {file_size} bytes")
            return False
        
        # Check if it's an APK+ file
        try:
            from tools.apk_plus_handler import APKPlusHandler
            apk_plus_handler = APKPlusHandler(app.config['TEMP_FOLDER'])
            if apk_plus_handler.is_apk_plus(file_path):
                logger.info(f"Detected APK+ format: {file_path}")
                return True
        except ImportError:
            logger.warning("APK+ handler not available, skipping APK+ check")
        
        # Check file signature (APK files are ZIP files)
        with open(file_path, 'rb') as f:
            header = f.read(4)
            # ZIP file signature: PK (0x504B)
            if header[:2] != b'PK':
                logger.warning(f"Invalid APK signature: {header[:2]}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"APK validation error: {str(e)}")
        return False

def list_projects():
    """List all projects in the projects folder"""
    projects = []
    projects_folder = app.config['PROJECTS_FOLDER']
    
    try:
        for project_id in os.listdir(projects_folder):
            project_path = os.path.join(projects_folder, project_id)
            if os.path.isdir(project_path):
                metadata_path = os.path.join(project_path, 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Add calculated fields
                    metadata['size'] = os.path.getsize(os.path.join(project_path, 'original.apk')) if os.path.exists(os.path.join(project_path, 'original.apk')) else 0
                    metadata['has_compiled'] = os.path.exists(os.path.join(project_path, 'compiled.apk'))
                    metadata['has_signed'] = os.path.exists(os.path.join(project_path, 'signed.apk'))
                    
                    projects.append(metadata)
        
        # Sort by creation date (newest first)
        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
    
    return projects

def get_project(project_id):
    """Get project metadata"""
    try:
        project_path = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        metadata_path = os.path.join(project_path, 'metadata.json')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Add calculated fields
            metadata['size'] = os.path.getsize(os.path.join(project_path, 'original.apk')) if os.path.exists(os.path.join(project_path, 'original.apk')) else 0
            metadata['has_compiled'] = os.path.exists(os.path.join(project_path, 'compiled.apk'))
            metadata['has_signed'] = os.path.exists(os.path.join(project_path, 'signed.apk'))
            
            return metadata
        
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
    
    return None

def simple_decompile_apk(apk_path, project_id, project_name):
    """Simple APK decompilation without using APKTool"""
    try:
        # Create project directory
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create decompiled directory
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        os.makedirs(decompiled_dir, exist_ok=True)
        
        # Extract APK contents (it's just a ZIP file)
        with zipfile.ZipFile(apk_path, 'r') as zip_ref:
            zip_ref.extractall(decompiled_dir)
        
        # Create basic structure if it doesn't exist
        for folder in ['res/drawable', 'res/layout', 'res/values']:
            os.makedirs(os.path.join(decompiled_dir, folder), exist_ok=True)
        
        # Create a basic strings.xml if it doesn't exist
        strings_path = os.path.join(decompiled_dir, 'res/values/strings.xml')
        if not os.path.exists(strings_path):
            with open(strings_path, 'w') as f:
                f.write('''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">''' + project_name + '''</string>
</resources>''')
        
        # Create project metadata
        metadata = {
            'id': project_id,
            'name': project_name,
            'original_apk': os.path.basename(apk_path),
            'created_at': datetime.now().isoformat(),
            'status': 'decompiled'
        }
        
        # Save metadata
        metadata_path = os.path.join(project_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Copy original APK to project
        shutil.copy2(apk_path, os.path.join(project_dir, 'original.apk'))
        
        logger.info(f"APK decompiled successfully: {project_id}")
        return True
        
    except Exception as e:
        logger.error(f"Decompile error: {str(e)}")
        # Clean up on failure
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        return False

def get_project_resources(project_id):
    """Get available resources for editing"""
    project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
    decompiled_dir = os.path.join(project_dir, 'decompiled')
    
    resources = {
        'images': [],
        'strings': [],
        'layouts': []
    }
    
    try:
        # Get drawable resources (images)
        drawable_dirs = [
            'res/drawable',
            'res/drawable-hdpi',
            'res/drawable-mdpi',
            'res/drawable-xhdpi',
            'res/drawable-xxhdpi',
            'res/drawable-xxxhdpi'
        ]
        
        for drawable_dir in drawable_dirs:
            drawable_path = os.path.join(decompiled_dir, drawable_dir)
            if os.path.exists(drawable_path):
                for file in os.listdir(drawable_path):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        resources['images'].append({
                            'name': file,
                            'path': os.path.join(drawable_dir, file),
                            'size': os.path.getsize(os.path.join(drawable_path, file))
                        })
        
        # Get string resources
        strings_path = os.path.join(decompiled_dir, 'res/values/strings.xml')
        if os.path.exists(strings_path):
            resources['strings'].append({
                'name': 'strings.xml',
                'path': 'res/values/strings.xml',
                'size': os.path.getsize(strings_path)
            })
        
        # Get layout resources
        layout_path = os.path.join(decompiled_dir, 'res/layout')
        if os.path.exists(layout_path):
            for file in os.listdir(layout_path):
                if file.endswith('.xml'):
                    resources['layouts'].append({
                        'name': file,
                        'path': os.path.join('res/layout', file),
                        'size': os.path.getsize(os.path.join(layout_path, file))
                    })
        
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
    
    return resources

@app.route('/')
def index():
    """Main page with project list and upload form"""
    try:
        projects = list_projects()
        logger.info(f"Listed {len(projects)} projects")
        return render_template('index.html', projects=projects, gemini_enabled=False)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('index.html', projects=[], gemini_enabled=False)

@app.route('/upload', methods=['POST'])
def upload_apk():
    """Handle APK file upload"""
    logger.info("APK upload request received")
    
    if 'apk_file' not in request.files:
        logger.warning("No file part in the request")
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    file = request.files['apk_file']
    if file.filename == '':
        logger.warning("Empty filename submitted")
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if not file.filename.lower().endswith('.apk'):
        logger.warning(f"Invalid file extension: {file.filename}")
        flash('Please upload an APK file', 'error')
        return redirect(url_for('index'))

    try:
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        logger.info(f"Processing APK upload: {filename} (Project ID: {project_id})")

        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{project_id}_{filename}")
        file.save(upload_path)
        logger.info(f"APK saved to: {upload_path}")
        
        # Verify file was saved correctly
        if not os.path.exists(upload_path):
            logger.error(f"File was not saved correctly: {upload_path}")
            flash('Error saving uploaded file', 'error')
            return redirect(url_for('index'))
            
        # Get file size for logging
        file_size = os.path.getsize(upload_path)
        logger.info(f"Uploaded file size: {file_size} bytes")
        
        # Basic file validation
        if not is_valid_apk(upload_path):
            logger.warning(f"Invalid APK format: {filename}")
            flash('Invalid APK file format', 'error')
            os.remove(upload_path)
            return redirect(url_for('index'))

        # Decompile APK using simple method (no APKTool dependency)
        project_name = request.form.get('project_name', filename.replace('.apk', ''))
        logger.info(f"Decompiling APK with project name: {project_name}")
        success = simple_decompile_apk(upload_path, project_id, project_name)

        if success:
            logger.info(f"APK decompiled successfully: {project_id}")
            flash(f'APK "{filename}" uploaded and decompiled successfully!', 'success')
            return redirect(url_for('project_view', project_id=project_id))
        else:
            logger.error(f"Failed to decompile APK: {filename}")
            flash('Failed to decompile APK. Please check if it\'s a valid APK file.', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(url_for('index'))

def generate_app_preview(project_id):
    """Generate a simple app preview"""
    try:
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        
        # Get project metadata
        project = get_project(project_id)
        if not project:
            return None
            
        # Import AI helper
        try:
            # Make sure utils directory exists
            os.makedirs('utils', exist_ok=True)
            
            # Check if ai_helper.py exists, if not, we'll use the fallback
            if not os.path.exists(os.path.join('utils', 'ai_helper.py')):
                raise ImportError("AI Helper module not found")
                
            from utils.ai_helper import AIHelper
            ai_helper = AIHelper(app.config['TEMP_FOLDER'])
            
            # Get color scheme from project metadata
            color_scheme = project.get('color_scheme', 'blue')
            
            # Generate preview
            preview_info = ai_helper.generate_app_preview(
                project_name=project['name'],
                color_scheme=color_scheme,
                gui_changes=project.get('last_gui_changes', '')
            )
            
            if preview_info:
                return {
                    'app_name': project['name'],
                    'icon_base64': None,  # We don't extract the icon in this simplified version
                    'layout_base64': preview_info['preview_base64']
                }
                
        except ImportError as e:
            logger.warning(f"AI Helper module not available: {str(e)}, using fallback preview")
        except Exception as e:
            logger.warning(f"Error using AI Helper: {str(e)}, using fallback preview")
            
        # Fallback to simple preview generation
        from PIL import Image, ImageDraw, ImageFont
        import io
        import base64
        
        # Create a simple layout preview image
        img = Image.new('RGB', (300, 500), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Add a simple representation of the layout
        draw.rectangle([(10, 10), (290, 50)], fill=(50, 50, 50))
        
        # Try to use a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            
        # Add app name
        draw.text((150, 30), project['name'], fill=(200, 200, 200), anchor="mm")
        
        # Add some placeholder elements
        draw.rectangle([(10, 60), (290, 120)], fill=(40, 40, 40))
        draw.rectangle([(10, 130), (290, 190)], fill=(40, 40, 40))
        draw.rectangle([(10, 200), (290, 260)], fill=(40, 40, 40))
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        layout_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            'app_name': project['name'],
            'icon_base64': None,
            'layout_base64': layout_base64
        }
    except Exception as e:
        logger.error(f"Error generating app preview: {str(e)}")
        return None

@app.route('/project/<project_id>')
def project_view(project_id):
    """View project details and resources"""
    try:
        logger.info(f"Viewing project: {project_id}")
        project = get_project(project_id)
        if not project:
            logger.warning(f"Project not found: {project_id}")
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Get project resources
        resources = get_project_resources(project_id)
        logger.info(f"Retrieved resources for project: {project_id}")
        
        # Generate app preview
        app_preview = generate_app_preview(project_id)
        logger.info(f"Generated app preview for project: {project_id}")

        return render_template('project.html', 
                            project=project, 
                            resources=resources, 
                            project_id=project_id,
                            app_preview=app_preview)
    except Exception as e:
        logger.error(f"Error in project_view: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/edit/<project_id>/<resource_type>/<path:resource_path>')
def edit_resource(project_id, resource_type, resource_path):
    """Edit a specific resource"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Get resource content
        decompiled_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id, 'decompiled')
        full_path = os.path.join(decompiled_dir, resource_path)
        
        resource_content = None
        if resource_type in ['string', 'layout']:
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    resource_content = f.read()
        elif resource_type == 'image':
            if os.path.exists(full_path):
                resource_content = {'exists': True, 'path': full_path}

        return render_template('edit_resource.html',
                            project=project,
                            resource_type=resource_type,
                            resource_path=resource_path,
                            resource_content=resource_content,
                            project_id=project_id)
    except Exception as e:
        logger.error(f"Error in edit_resource: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/save_resource/<project_id>/<resource_type>/<path:resource_path>', methods=['POST'])
def save_resource(project_id, resource_type, resource_path):
    """Save edited resource"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
            
        decompiled_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id, 'decompiled')
        full_path = os.path.join(decompiled_dir, resource_path)
        
        if resource_type == 'image':
            # Handle image upload
            if 'image_file' in request.files:
                file = request.files['image_file']
                if file.filename != '':
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    # Save uploaded file
                    file.save(full_path)
                    flash('Image updated successfully!', 'success')
                else:
                    flash('No image selected', 'error')

        elif resource_type == 'string' or resource_type == 'layout':
            # Handle text content
            content = request.form.get('content', '')
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # Save content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            flash(f'{resource_type.capitalize()} updated successfully!', 'success')

        return redirect(url_for('edit_resource', 
                            project_id=project_id, 
                            resource_type=resource_type, 
                            resource_path=resource_path))

    except Exception as e:
        logger.error(f"Save resource error: {str(e)}", exc_info=True)
        flash(f'Save failed: {str(e)}', 'error')
        return redirect(url_for('edit_resource', 
                            project_id=project_id, 
                            resource_type=resource_type, 
                            resource_path=resource_path))

@app.route('/compile/<project_id>')
def compile_apk(project_id):
    """Compile APK (simplified version)"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Simple compilation - create a ZIP file with APK extension
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        output_path = os.path.join(project_dir, 'compiled.apk')
        
        # Check if original APK exists to use as a base
        original_apk = os.path.join(project_dir, 'original.apk')
        if os.path.exists(original_apk):
            logger.info(f"Using original APK as base for compilation")
            
            # Create a temporary directory for merging
            temp_dir = os.path.join(app.config['TEMP_FOLDER'], f"compile_{project_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Extract original APK to temp directory
                with zipfile.ZipFile(original_apk, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Copy modified files from decompiled directory to temp directory
                for root, dirs, files in os.walk(decompiled_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, decompiled_dir)
                        dst_path = os.path.join(temp_dir, rel_path)
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(src_path, dst_path)
                
                # Create new APK from temp directory with proper structure
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # First add AndroidManifest.xml
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
                            
                            # Skip files we've already added
                            if arcname in ["AndroidManifest.xml", "classes.dex", "classes2.dex", "classes3.dex", "resources.arsc"]:
                                continue
                            
                            zipf.write(file_path, arcname)
                
                logger.info(f"Created APK with proper structure: {output_path}")
            except Exception as e:
                logger.error(f"Error creating APK with proper structure: {str(e)}")
                # Fall back to copying the original APK
                shutil.copy2(original_apk, output_path)
                logger.info(f"Copied original APK as fallback: {output_path}")
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir)
        else:
            # Fallback to simple ZIP creation if original APK is not available
            logger.warning(f"Original APK not found, creating simple ZIP with APK extension")
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # First add AndroidManifest.xml if it exists
                manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
                if os.path.exists(manifest_path):
                    zipf.write(manifest_path, "AndroidManifest.xml")
                
                # Add all other files
                for root, dirs, files in os.walk(decompiled_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, decompiled_dir)
                        
                        # Skip AndroidManifest.xml as we've already added it
                        if arcname == "AndroidManifest.xml":
                            continue
                        
                        zipf.write(file_path, arcname)
        
        # Fix and sign the APK to make it installable
        signed_path = os.path.join(project_dir, 'signed.apk')
        
        try:
            # Try to use the APK fixer
            from tools.apk_fixer import APKFixer
            fixer = APKFixer(app.config['TEMP_FOLDER'])
            
            # Fix and sign the APK
            success, result = fixer.fix_apk(output_path, signed_path)
            
            if success:
                logger.info(f"APK fixed and signed: {signed_path}")
                # Update project metadata to reflect signing
                metadata_path = os.path.join(project_dir, 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Update fields
                    metadata.update({
                        'status': 'signed',
                        'signed_at': datetime.now().isoformat()
                    })
                    
                    # Save updated metadata
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
            else:
                logger.warning(f"Failed to fix and sign APK: {result}")
                # Just copy the compiled APK as signed.apk
                shutil.copy2(output_path, signed_path)
        except Exception as e:
            logger.warning(f"Error fixing and signing APK: {str(e)}")
            # Just copy the compiled APK as signed.apk
            shutil.copy2(output_path, signed_path)
        
        # Create a special version for direct installation
        installable_path = os.path.join(project_dir, 'installable.apk')
        try:
            # Just copy the original APK as the installable version
            # This ensures we have a valid APK structure
            if os.path.exists(original_apk):
                shutil.copy2(original_apk, installable_path)
                logger.info(f"Created installable APK from original: {installable_path}")
            else:
                # If no original APK, use the signed one
                shutil.copy2(signed_path, installable_path)
                logger.info(f"Created installable APK from signed: {installable_path}")
        except Exception as e:
            logger.warning(f"Error creating installable APK: {str(e)}")
        
        # Verify the APK was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Compiled APK created successfully: {output_path} ({file_size} bytes)")
            flash('APK compiled and signed successfully! You can now download and install it.', 'success')
        else:
            logger.error(f"Failed to create compiled APK: {output_path}")
            flash('Failed to compile APK', 'error')
            
        return redirect(url_for('download_apk', project_id=project_id))

    except Exception as e:
        logger.error(f"Compile error: {str(e)}", exc_info=True)
        flash(f'Compile failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/download/<project_id>')
def download_apk(project_id):
    """Download compiled APK"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Get format preference (APK or APK+)
        format_type = request.args.get('format', 'apk')
        
        # Check for installable APK first (best option)
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        installable_path = os.path.join(project_dir, 'installable.apk')
        
        # Check for signed APK next
        signed_path = os.path.join(project_dir, 'signed.apk')
        
        # Fall back to compiled APK
        compiled_path = os.path.join(project_dir, 'compiled.apk')
        
        # Determine which file to use
        if os.path.exists(installable_path):
            source_path = installable_path
            file_type = "installable"
        elif os.path.exists(signed_path):
            source_path = signed_path
            file_type = "signed"
        elif os.path.exists(compiled_path):
            source_path = compiled_path
            file_type = "compiled"
        else:
            flash('Compiled APK not found. Please compile first.', 'error')
            return redirect(url_for('project_view', project_id=project_id))
        
        # If APK+ format is requested, create a special version
        if format_type.lower() == 'apk+':
            try:
                # For APK+ format, we'll create a copy of the original APK
                # but rename it with .apk+ extension
                apk_plus_path = os.path.join(project_dir, f"{file_type}.apk+")
                
                # Use the original APK as the base (most reliable)
                original_apk = os.path.join(project_dir, 'original.apk')
                if os.path.exists(original_apk):
                    # Simply copy the original APK with .apk+ extension
                    shutil.copy2(original_apk, apk_plus_path)
                    logger.info(f"Created APK+ from original APK: {apk_plus_path}")
                else:
                    # If original APK doesn't exist, use the source path
                    shutil.copy2(source_path, apk_plus_path)
                    logger.info(f"Created APK+ from {file_type} APK: {apk_plus_path}")
                
                # Return the file with .apk+ extension
                # Note: This won't be directly installable on Android, but can be used with APK+ tools
                return send_file(apk_plus_path, 
                            as_attachment=True, 
                            download_name=f"{project['name']}.apk+",
                            mimetype='application/octet-stream')
            except Exception as e:
                logger.error(f"Error creating APK+ format: {str(e)}")
                # Fall back to standard APK
                flash('Error creating APK+ format, downloading standard APK instead.', 'warning')
            except Exception as e:
                logger.error(f"Error creating APK+ format: {str(e)}")
                # Fall back to standard APK
                flash('Error creating APK+ format, downloading standard APK instead.', 'warning')
            except ImportError:
                logger.warning("APK+ handler not available")
                flash('APK+ format not supported, downloading standard APK instead.', 'warning')
            except Exception as e:
                logger.error(f"Error converting to APK+ format: {str(e)}")
                flash('Error creating APK+ format, downloading standard APK instead.', 'warning')
        
        # Return the standard APK
        return send_file(source_path, 
                    as_attachment=True, 
                    download_name=f"{project['name']}_modified.apk",
                    mimetype='application/vnd.android.package-archive')

    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/delete/<project_id>')
def delete_project(project_id):
    """Delete project"""
    try:
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            flash('Project deleted successfully!', 'success')
        else:
            flash('Project not found', 'error')
    except Exception as e:
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        flash(f'Delete failed: {str(e)}', 'error')

    return redirect(url_for('index'))

@app.route('/modify_gui/<project_id>', methods=['POST'])
def modify_gui(project_id):
    """Modify GUI based on user description with AI assistance"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        gui_changes = request.form.get('gui_changes', '').strip()
        color_scheme = request.form.get('color_scheme', '')

        if not gui_changes:
            flash('Please describe the GUI changes you want', 'error')
            return redirect(url_for('project_view', project_id=project_id))

        # Get project directory
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        
        # Try to use AI helper for GUI modifications
        try:
            from utils.ai_helper import AIHelper
            ai_helper = AIHelper(app.config['TEMP_FOLDER'])
            
            # Apply GUI changes using AI helper
            result = ai_helper.apply_gui_changes(
                project_id=project_id,
                project_dir=project_dir,
                gui_changes=gui_changes,
                color_scheme=color_scheme
            )
            
            if result and result.get('modified_files'):
                logger.info(f"AI helper modified {len(result['modified_files'])} files")
                flash(f'AI applied changes to {len(result["modified_files"])} files!', 'success')
            
            # Generate a new preview
            preview_info = ai_helper.generate_app_preview(
                project_name=project['name'],
                color_scheme=color_scheme,
                gui_changes=gui_changes
            )
            
            if preview_info:
                # Save preview image to project directory
                preview_path = os.path.join(project_dir, 'preview.png')
                with open(preview_path, 'wb') as f:
                    import base64
                    f.write(base64.b64decode(preview_info['preview_base64']))
                logger.info(f"Saved new preview image to {preview_path}")
        
        except ImportError as e:
            logger.warning(f"AI Helper not available: {str(e)}")
            flash('Using simplified GUI modification (AI features not available)', 'info')
        except Exception as e:
            logger.error(f"Error using AI helper: {str(e)}")
            flash(f'AI processing error: {str(e)}', 'warning')
        
        # Update project metadata to record the changes
        metadata_path = os.path.join(project_dir, 'metadata.json')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Update fields
            metadata.update({
                'last_gui_changes': gui_changes,
                'color_scheme': color_scheme,
                'status': 'modified',
                'updated_at': datetime.now().isoformat()
            })
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

        flash('GUI modifications applied successfully!', 'success')
        return redirect(url_for('project_view', project_id=project_id))

    except Exception as e:
        logger.error(f"GUI modification error: {str(e)}", exc_info=True)
        flash(f'Modification failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    return app.send_static_file('favicon.ico')

@app.route('/refresh_preview/<project_id>')
def refresh_preview(project_id):
    """Refresh the app preview"""
    try:
        # Simply redirect back to the project view
        flash('Preview refreshed', 'success')
        return redirect(url_for('project_view', project_id=project_id))
    except Exception as e:
        logger.error(f"Refresh preview error: {str(e)}", exc_info=True)
        flash(f'Refresh failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/generate_function', methods=['POST'])
def generate_function():
    """Simplified function generation"""
    try:
        function_prompt = request.form.get('function_prompt', '').strip()
        if not function_prompt:
            flash('Please enter a function description', 'error')
            return redirect(url_for('index'))
            
        # Generate simple placeholder code
        function_id = str(uuid.uuid4())
        function_code = f"""# Generated Function
# Generated at: {datetime.now().isoformat()}
# Prompt: {function_prompt}

def generated_function():
    \"\"\"
    {function_prompt}
    \"\"\"
    print("Function generated based on: {function_prompt}")
    return "Function implementation would go here"
"""

        # Save generated function
        function_file = os.path.join(app.config['TEMP_FOLDER'], f"generated_function_{function_id}.py")
        with open(function_file, 'w') as f:
            f.write(function_code)

        flash(f'Function generated successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Generate function error: {str(e)}", exc_info=True)
        flash(f'Generation failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/sign_apk_page/<project_id>')
def sign_apk_page(project_id):
    """Show APK signing page"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
        
        # Check if compiled APK exists
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        compiled_path = os.path.join(project_dir, 'compiled.apk')
        if not os.path.exists(compiled_path):
            flash('Compiled APK not found. Please compile first.', 'error')
            return redirect(url_for('project_view', project_id=project_id))
        
        # Initialize APK signer
        try:
            signer = APKSigner(app.config['TOOLS_FOLDER'])
            # Get available keystores
            keystores = signer.list_keystores()
        except Exception as e:
            logger.error(f"Error initializing APK signer: {str(e)}")
            keystores = []
        
        return render_template('sign_apk.html',
                            project=project,
                            project_id=project_id,
                            keystores=keystores)
    except Exception as e:
        logger.error(f"Error in sign_apk_page: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/sign_apk/<project_id>', methods=['POST'])
def sign_apk(project_id):
    """Sign APK with selected keystore"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
        
        # Get form data
        keystore = request.form.get('keystore')
        alias = request.form.get('alias')
        password = request.form.get('password')
        
        # Check if compiled APK exists
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        compiled_path = os.path.join(project_dir, 'compiled.apk')
        signed_path = os.path.join(project_dir, 'signed.apk')
        
        if not os.path.exists(compiled_path):
            flash('Compiled APK not found. Please compile first.', 'error')
            return redirect(url_for('sign_apk_page', project_id=project_id))
        
        # Initialize APK signer
        try:
            signer = APKSigner(app.config['TOOLS_FOLDER'])
            
            # Use debug keystore if "debug" is selected
            if keystore == 'debug':
                keystore = None  # APKSigner will use debug keystore
                alias = None
                password = None
            
            # Sign the APK
            success, result = signer.sign_apk(compiled_path, signed_path, keystore, alias, password)
            
            if success:
                flash('APK signed successfully!', 'success')
                return redirect(url_for('download_apk', project_id=project_id))
            else:
                flash(f'Failed to sign APK: {result}', 'error')
                return redirect(url_for('sign_apk_page', project_id=project_id))
        except Exception as e:
            logger.error(f"Error signing APK: {str(e)}")
            flash(f"Error signing APK: {str(e)}", "error")
            return redirect(url_for('sign_apk_page', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error in sign_apk: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('sign_apk_page', project_id=project_id))

@app.route('/create_keystore/<project_id>', methods=['POST'])
def create_keystore(project_id):
    """Create a new keystore"""
    try:
        # Get form data
        keystore_name = request.form.get('keystore_name')
        alias = request.form.get('key_alias')
        password = request.form.get('key_password')
        common_name = request.form.get('common_name')
        org_unit = request.form.get('org_unit')
        org = request.form.get('org')
        locality = request.form.get('locality')
        state = request.form.get('state')
        country = request.form.get('country')
        validity = int(request.form.get('validity', 25))
        
        # Initialize APK signer
        try:
            signer = APKSigner(app.config['TOOLS_FOLDER'])
            
            # Create keystore
            success, result = signer.create_keystore(
                keystore_name, alias, password,
                common_name, org_unit, org,
                locality, state, country, validity
            )
            
            if success:
                flash('Keystore created successfully!', 'success')
            else:
                flash(f'Failed to create keystore: {result}', 'error')
        except Exception as e:
            logger.error(f"Error creating keystore: {str(e)}")
            flash(f"Error creating keystore: {str(e)}", "error")
        
        return redirect(url_for('sign_apk_page', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error in create_keystore: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('sign_apk_page', project_id=project_id))

@app.route('/download_tools')
def download_tools():
    """Download required tools for APK signing"""
    try:
        # Initialize APK signer
        try:
            signer = APKSigner(app.config['TOOLS_FOLDER'])
            
            # Download tools
            success, message = signer.download_tools()
            
            if success:
                flash(f'Tools downloaded successfully: {message}', 'success')
            else:
                flash(f'Failed to download tools: {message}', 'error')
        except Exception as e:
            logger.error(f"Error downloading tools: {str(e)}")
            flash(f"Error downloading tools: {str(e)}", "error")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Error downloading tools: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 100MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}", exc_info=True)
    flash("Internal server error. Please check the logs for details.", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    logger.info("Starting APK Editor application")
    app.run(debug=True, host='0.0.0.0', port=5000)

# APK Conversion Routes
@app.route('/convert')
def convert_apk_page():
    """Show APK conversion page"""
    try:
        # Get recent conversions from temp folder
        conversions = []
        temp_dir = app.config['TEMP_FOLDER']
        
        # Look for conversion records
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        if os.path.exists(conversion_record):
            try:
                with open(conversion_record, 'r') as f:
                    conversions = json.load(f)
            except Exception as e:
                logger.error(f"Error loading conversion records: {str(e)}")
        
        return render_template('convert_apk.html', conversions=conversions)
    except Exception as e:
        logger.error(f"Error in convert_apk_page: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/convert/apk-to-plus', methods=['POST'])
def convert_apk_to_plus():
    """Convert APK to APK+ format"""
    try:
        if 'apk_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        file = request.files['apk_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        if not file.filename.lower().endswith('.apk'):
            flash('Please upload an APK file', 'error')
            return redirect(url_for('convert_apk_page'))

        # Get option for making installable
        make_installable = 'make_installable' in request.form
        
        # Save the uploaded APK
        temp_dir = app.config['TEMP_FOLDER']
        original_filename = secure_filename(file.filename)
        conversion_id = str(uuid.uuid4())
        original_path = os.path.join(temp_dir, f"original_{conversion_id}.apk")
        file.save(original_path)
        
        # Convert to APK+
        if make_installable:
            # Create an installable APK+ (actually an APK with APK+ content)
            converted_filename = original_filename.replace('.apk', '_plus.apk')
            converted_path = os.path.join(temp_dir, f"converted_{conversion_id}.apk")
            
            # Copy the original APK and add APK+ marker
            shutil.copy2(original_path, converted_path)
            
            # Add a marker file inside the APK to indicate it's APK+ format
            try:
                with zipfile.ZipFile(converted_path, 'a', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.writestr('META-INF/APK_PLUS_MARKER', 'This APK contains APK+ format data')
            except Exception as e:
                logger.warning(f"Could not add APK+ marker to APK: {str(e)}")
        else:
            # Create a true APK+ file (not installable)
            converted_filename = original_filename.replace('.apk', '.apk+')
            converted_path = os.path.join(temp_dir, f"converted_{conversion_id}.apk+")
            
            # Simply copy the file with .apk+ extension
            shutil.copy2(original_path, converted_path)
        
        # Record the conversion
        conversion = {
            'id': conversion_id,
            'original_file': original_filename,
            'converted_file': converted_filename,
            'original_path': original_path,
            'converted_path': converted_path,
            'type': 'to_plus',
            'date': datetime.now().isoformat(),
            'installable': make_installable
        }
        
        # Save conversion record
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        conversions = []
        if os.path.exists(conversion_record):
            try:
                with open(conversion_record, 'r') as f:
                    conversions = json.load(f)
            except Exception as e:
                logger.error(f"Error loading conversion records: {str(e)}")
        
        # Add new conversion and limit to 10 most recent
        conversions.insert(0, conversion)
        conversions = conversions[:10]
        
        with open(conversion_record, 'w') as f:
            json.dump(conversions, f, indent=2)
        
        # Return the converted file
        flash(f'APK converted to {"installable " if make_installable else ""}APK+ format successfully!', 'success')
        return send_file(converted_path, 
                    as_attachment=True, 
                    download_name=converted_filename,
                    mimetype='application/octet-stream')
    except Exception as e:
        logger.error(f"Error converting APK to APK+: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('convert_apk_page'))

# This route has been moved to a consolidated implementation below
def convert_plus_to_apk_old():
    """Convert APK+ to APK format (old implementation)"""
    try:
        if 'apk_plus_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        file = request.files['apk_plus_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        if not file.filename.lower().endswith('.apk+'):
            flash('Please upload an APK+ file', 'error')
            return redirect(url_for('convert_apk_page'))

        # Get option for signing
        sign_apk = 'sign_apk' in request.form
        
        # Save the uploaded APK+
        temp_dir = app.config['TEMP_FOLDER']
        original_filename = secure_filename(file.filename)
        conversion_id = str(uuid.uuid4())
        original_path = os.path.join(temp_dir, f"original_{conversion_id}.apk+")
        file.save(original_path)
        
        # Convert to APK
        converted_filename = original_filename.replace('.apk+', '.apk')
        converted_path = os.path.join(temp_dir, f"converted_{conversion_id}.apk")
        
        # Simply copy the file with .apk extension
        shutil.copy2(original_path, converted_path)
        
        # Sign the APK if requested
        if sign_apk:
            try:
                # Try to use the APK signer
                from tools.apk_signer import APKSigner
                signer = APKSigner(app.config['TOOLS_FOLDER'])
                
                # Sign with debug keystore
                success, result = signer.sign_apk(converted_path, converted_path)
                
                if success:
                    logger.info(f"APK signed successfully: {converted_path}")
                else:
                    logger.warning(f"Failed to sign APK: {result}")
            except Exception as e:
                logger.warning(f"Error signing APK: {str(e)}")
        
        # Record the conversion
        conversion = {
            'id': conversion_id,
            'original_file': original_filename,
            'converted_file': converted_filename,
            'original_path': original_path,
            'converted_path': converted_path,
            'type': 'to_apk',
            'date': datetime.now().isoformat(),
            'signed': sign_apk
        }
        
        # Save conversion record
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        conversions = []
        if os.path.exists(conversion_record):
            try:
                with open(conversion_record, 'r') as f:
                    conversions = json.load(f)
            except Exception as e:
                logger.error(f"Error loading conversion records: {str(e)}")
        
        # Add new conversion and limit to 10 most recent
        conversions.insert(0, conversion)
        conversions = conversions[:10]
        
        with open(conversion_record, 'w') as f:
            json.dump(conversions, f, indent=2)
        
        # Return the converted file
        flash(f'APK+ converted to {"signed " if sign_apk else ""}APK format successfully!', 'success')
        return send_file(converted_path, 
                    as_attachment=True, 
                    download_name=converted_filename,
                    mimetype='application/vnd.android.package-archive')
    except Exception as e:
        logger.error(f"Error converting APK+ to APK: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('convert_apk_page'))

# This route has been moved to a consolidated implementation below
def download_conversion_old(conversion_id):
    """Download a previously converted file (old implementation)"""
    try:
        # Get conversion record
        temp_dir = app.config['TEMP_FOLDER']
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        
        if not os.path.exists(conversion_record):
            flash('Conversion record not found', 'error')
            return redirect(url_for('convert_apk_page'))
        
        with open(conversion_record, 'r') as f:
            conversions = json.load(f)
        
        # Find the requested conversion
        conversion = None
        for c in conversions:
            if c['id'] == conversion_id:
                conversion = c
                break
        
        if not conversion:
            flash('Conversion not found', 'error')
            return redirect(url_for('convert_apk_page'))
        
        # Check if the converted file exists
        converted_path = conversion['converted_path']
        if not os.path.exists(converted_path):
            flash('Converted file not found', 'error')
            return redirect(url_for('convert_apk_page'))
        
        # Determine MIME type based on file extension
        if converted_path.lower().endswith('.apk'):
            mimetype = 'application/vnd.android.package-archive'
        else:
            mimetype = 'application/octet-stream'
        
        # Return the converted file
        return send_file(converted_path, 
                    as_attachment=True, 
                    download_name=conversion['converted_file'],
                    mimetype=mimetype)
    except Exception as e:
        logger.error(f"Error downloading conversion: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('convert_apk_page'))
# This route is already defined above
def convert_apk_page_duplicate():
    """Show APK conversion page (duplicate)"""
    try:
        # Get recent conversions from temp folder
        conversions = []
        temp_dir = app.config['TEMP_FOLDER']
        
        # Look for conversion records
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        if os.path.exists(conversion_record):
            try:
                with open(conversion_record, 'r') as f:
                    conversions = json.load(f)
            except Exception as e:
                logger.error(f"Error reading conversion records: {str(e)}")
        
        return render_template('convert_apk.html', conversions=conversions)
    except Exception as e:
        logger.error(f"Error in convert_apk_page: {str(e)}", exc_info=True)
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/convert/apk-to-plus', methods=['POST'])
def convert_apk_to_plus():
    """Convert APK to APK+ format"""
    try:
        if 'apk_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        file = request.files['apk_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        if not file.filename.lower().endswith('.apk'):
            flash('Please upload an APK file', 'error')
            return redirect(url_for('convert_apk_page'))

        # Generate unique ID for this conversion
        conversion_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        # Save uploaded file
        upload_path = os.path.join(app.config['TEMP_FOLDER'], f"convert_{conversion_id}_{filename}")
        file.save(upload_path)
        
        # Check if file is valid
        if not is_valid_apk(upload_path):
            flash('Invalid APK file format', 'error')
            os.remove(upload_path)
            return redirect(url_for('convert_apk_page'))
        
        try:
            # Import APK+ handler
            from tools.apk_plus_handler import APKPlusHandler
            handler = APKPlusHandler(app.config['TEMP_FOLDER'])
            
            # Convert to APK+
            make_installable = request.form.get('make_installable') == 'on'
            
            if make_installable:
                success, output_path = handler.create_installable_apk_plus(upload_path)
            else:
                success, output_path = handler.convert_to_apk_plus(upload_path)
            
            if success:
                # Record the conversion
                conversion_record = {
                    'id': conversion_id,
                    'original_file': filename,
                    'converted_file': os.path.basename(output_path),
                    'type': 'to_plus',
                    'date': datetime.now().isoformat(),
                    'path': output_path
                }
                
                # Save to conversion history
                save_conversion_record(conversion_record)
                
                flash('APK converted to APK+ format successfully!', 'success')
                return redirect(url_for('download_conversion', conversion_id=conversion_id))
            else:
                flash(f'Conversion failed: {output_path}', 'error')
                return redirect(url_for('convert_apk_page'))
                
        except ImportError:
            flash('APK+ handler module not available', 'error')
            return redirect(url_for('convert_apk_page'))
            
    except Exception as e:
        logger.error(f"Convert APK to APK+ error: {str(e)}", exc_info=True)
        flash(f'Conversion failed: {str(e)}', 'error')
        return redirect(url_for('convert_apk_page'))

@app.route('/convert/plus-to-apk', methods=['POST'])
def convert_plus_to_apk():
    """Convert APK+ to standard APK format"""
    try:
        if 'apk_plus_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        file = request.files['apk_plus_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('convert_apk_page'))

        # Generate unique ID for this conversion
        conversion_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        # Save uploaded file
        upload_path = os.path.join(app.config['TEMP_FOLDER'], f"convert_{conversion_id}_{filename}")
        file.save(upload_path)
        
        try:
            # Import APK+ handler
            from tools.apk_plus_handler import APKPlusHandler
            handler = APKPlusHandler(app.config['TEMP_FOLDER'])
            
            # Check if it's a valid APK+ file
            if not handler.is_apk_plus(upload_path):
                flash('Invalid APK+ file format', 'error')
                os.remove(upload_path)
                return redirect(url_for('convert_apk_page'))
            
            # Convert to standard APK
            success, output_path = handler.convert_to_standard_apk(upload_path)
            
            if success:
                # Sign the APK if requested
                sign_apk = request.form.get('sign_apk') == 'on'
                
                if sign_apk:
                    try:
                        # Try to use the APK fixer to sign
                        from tools.apk_fixer import APKFixer
                        fixer = APKFixer(app.config['TEMP_FOLDER'])
                        
                        signed_path = output_path.replace('.apk', '_signed.apk')
                        sign_success, sign_result = fixer.fix_apk(output_path, signed_path)
                        
                        if sign_success:
                            output_path = signed_path
                    except ImportError:
                        logger.warning("APK Fixer not available, skipping signing")
                
                # Record the conversion
                conversion_record = {
                    'id': conversion_id,
                    'original_file': filename,
                    'converted_file': os.path.basename(output_path),
                    'type': 'to_standard',
                    'date': datetime.now().isoformat(),
                    'path': output_path
                }
                
                # Save to conversion history
                save_conversion_record(conversion_record)
                
                flash('APK+ converted to standard APK format successfully!', 'success')
                return redirect(url_for('download_conversion', conversion_id=conversion_id))
            else:
                flash(f'Conversion failed: {output_path}', 'error')
                return redirect(url_for('convert_apk_page'))
                
        except ImportError:
            flash('APK+ handler module not available', 'error')
            return redirect(url_for('convert_apk_page'))
            
    except Exception as e:
        logger.error(f"Convert APK+ to APK error: {str(e)}", exc_info=True)
        flash(f'Conversion failed: {str(e)}', 'error')
        return redirect(url_for('convert_apk_page'))

def save_conversion_record(record):
    """Save conversion record to history"""
    try:
        temp_dir = app.config['TEMP_FOLDER']
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        
        conversions = []
        if os.path.exists(conversion_record):
            try:
                with open(conversion_record, 'r') as f:
                    conversions = json.load(f)
            except Exception:
                conversions = []
        
        # Add new record
        conversions.append(record)
        
        # Keep only the last 10 conversions
        if len(conversions) > 10:
            conversions = conversions[-10:]
        
        # Save updated records
        with open(conversion_record, 'w') as f:
            json.dump(conversions, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error saving conversion record: {str(e)}")

@app.route('/download/conversion/<conversion_id>')
def download_conversion(conversion_id):
    """Download converted APK file"""
    try:
        temp_dir = app.config['TEMP_FOLDER']
        conversion_record = os.path.join(temp_dir, 'conversions.json')
        
        if not os.path.exists(conversion_record):
            flash('Conversion record not found', 'error')
            return redirect(url_for('convert_apk_page'))
        
        with open(conversion_record, 'r') as f:
            conversions = json.load(f)
        
        # Find the conversion record
        conversion = None
        for record in conversions:
            if record.get('id') == conversion_id:
                conversion = record
                break
        
        if not conversion:
            flash('Conversion not found', 'error')
            return redirect(url_for('convert_apk_page'))
        
        # Check if the file exists
        file_path = conversion.get('path')
        if not file_path or not os.path.exists(file_path):
            flash('Converted file not found', 'error')
            return redirect(url_for('convert_apk_page'))
        
        # Determine the file type for download name
        download_name = conversion.get('converted_file', 'converted_file')
        
        return send_file(file_path, 
                    as_attachment=True, 
                    download_name=download_name,
                    mimetype='application/octet-stream')
        
    except Exception as e:
        logger.error(f"Download conversion error: {str(e)}", exc_info=True)
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('convert_apk_page'))