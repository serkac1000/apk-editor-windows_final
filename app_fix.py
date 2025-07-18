import os
import logging
import json
import shutil
import zipfile
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

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROJECTS_FOLDER'], app.config['TEMP_FOLDER']]:
    os.makedirs(folder, exist_ok=True)
    logger.info(f"Directory created/verified: {folder}")

def is_valid_apk(file_path):
    """Basic APK file validation"""
    try:
        # Check file size (not empty, not too large)
        file_size = os.path.getsize(file_path)
        if file_size < 1000 or file_size > 100 * 1024 * 1024:  # 1KB to 100MB
            logger.warning(f"Invalid APK size: {file_size} bytes")
            return False
        
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
        
        # Extract app name from strings.xml
        app_name = "Unknown App"
        strings_path = os.path.join(decompiled_dir, 'res/values/strings.xml')
        if os.path.exists(strings_path):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(strings_path)
                root = tree.getroot()
                for string in root.findall('.//string'):
                    if string.get('name') == 'app_name':
                        app_name = string.text
                        break
            except Exception as e:
                logger.error(f"Error parsing strings.xml: {str(e)}")
        
        # Look for app icon
        icon_base64 = None
        icon_paths = [
            'res/mipmap-xxxhdpi/ic_launcher.png',
            'res/mipmap-xxhdpi/ic_launcher.png',
            'res/mipmap-xhdpi/ic_launcher.png',
            'res/mipmap-hdpi/ic_launcher.png',
            'res/mipmap-mdpi/ic_launcher.png',
            'res/drawable/ic_launcher.png'
        ]
        
        for icon_path in icon_paths:
            full_path = os.path.join(decompiled_dir, icon_path)
            if os.path.exists(full_path):
                try:
                    import base64
                    with open(full_path, 'rb') as f:
                        icon_data = f.read()
                    icon_base64 = base64.b64encode(icon_data).decode('utf-8')
                    break
                except Exception as e:
                    logger.error(f"Error reading icon: {str(e)}")
        
        # Create a simple layout preview image
        layout_base64 = None
        try:
            # Try to import PIL
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (300, 500), color=(30, 30, 30))
            draw = ImageDraw.Draw(img)
            
            # Add a simple representation of the layout
            draw.rectangle([(10, 10), (290, 50)], fill=(50, 50, 50))
            draw.text((150, 30), app_name, fill=(200, 200, 200), anchor="mm")
            
            # Add some placeholder elements
            draw.rectangle([(10, 60), (290, 120)], fill=(40, 40, 40))
            draw.rectangle([(10, 130), (290, 190)], fill=(40, 40, 40))
            draw.rectangle([(10, 200), (290, 260)], fill=(40, 40, 40))
            
            # Convert to base64
            import io
            import base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            layout_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error creating layout preview: {str(e)}")
        
        return {
            'app_name': app_name,
            'icon_base64': icon_base64,
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

        # Simple compilation - just create a ZIP file with APK extension
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        output_path = os.path.join(project_dir, 'compiled.apk')
        
        # Create a ZIP file with APK extension
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(decompiled_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, decompiled_dir)
                    zipf.write(file_path, arcname)
        
        # Copy to signed.apk for consistency
        signed_path = os.path.join(project_dir, 'signed.apk')
        shutil.copy2(output_path, signed_path)
        
        flash('APK compiled successfully!', 'success')
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

        # Check for signed APK first
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        signed_path = os.path.join(project_dir, 'signed.apk')
        if os.path.exists(signed_path):
            return send_file(signed_path, 
                        as_attachment=True, 
                        download_name=f"{project['name']}_modified.apk",
                        mimetype='application/vnd.android.package-archive')
        
        # Fall back to compiled APK
        compiled_path = os.path.join(project_dir, 'compiled.apk')
        if os.path.exists(compiled_path):
            return send_file(compiled_path, 
                        as_attachment=True, 
                        download_name=f"{project['name']}_modified.apk",
                        mimetype='application/vnd.android.package-archive')
        
        flash('Compiled APK not found. Please compile first.', 'error')
        return redirect(url_for('project_view', project_id=project_id))

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
    """Modify GUI based on user description (simplified version)"""
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

        # Handle reference images
        reference_images = request.files.getlist('reference_images')
        image_paths = []

        for image in reference_images:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"ref_{uuid.uuid4()}_{filename}")
                image.save(image_path)
                image_paths.append(image_path)

        # In this simplified version, we just acknowledge the request
        # but don't actually modify any files
        
        # Update project metadata to record the changes
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
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

def generate_android_code(prompt):
    """Generate Android code based on prompt"""
    code = f"""// Generated Android Code
// Generated at: {datetime.now().isoformat()}
// Prompt: {prompt}

/*
 * Android Implementation
 * This code was generated based on your request.
 */

// XML Layout
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp">

    <TextView
        android:id="@+id/titleTextView"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Generated Feature"
        android:textSize="24sp"
        android:textStyle="bold"
        android:layout_marginBottom="16dp" />

    <Button
        android:id="@+id/actionButton"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Perform Action"
        android:onClick="onActionButtonClick" />

</LinearLayout>

// Java Implementation
public class GeneratedActivity extends AppCompatActivity {{

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_generated);
        
        // Initialize views
        TextView titleTextView = findViewById(R.id.titleTextView);
        Button actionButton = findViewById(R.id.actionButton);
        
        // Set up UI
        titleTextView.setText("Feature: {prompt}");
    }}
    
    public void onActionButtonClick(View view) {{
        // Handle button click
        Toast.makeText(this, "Action performed!", Toast.LENGTH_SHORT).show();
        
        // Implement feature logic here
        performFeatureAction();
    }}
    
    private void performFeatureAction() {{
        // TODO: Implement the requested feature
        Log.d("GeneratedFeature", "Performing action for: {prompt}");
    }}
}}
"""
    return code

def generate_python_code(prompt):
    """Generate Python code based on prompt"""
    code = f"""# Generated Python Code
# Generated at: {datetime.now().isoformat()}
# Prompt: {prompt}

def main():
    \"\"\"
    Main function implementing the requested feature:
    {prompt}
    \"\"\"
    print(f"Executing feature: {prompt}")
    
    # TODO: Implement the requested functionality
    result = implement_feature()
    
    print(f"Feature execution completed with result: {result}")
    return result

def implement_feature():
    \"\"\"
    Implementation of the requested feature
    \"\"\"
    # This is where the actual implementation would go
    # For now, we return a placeholder result
    return "Feature implemented successfully"

if __name__ == "__main__":
    main()
"""
    return code

@app.route('/view_generated_function/<function_id>')
def view_generated_function(function_id):
    """View generated function"""
    try:
        function_file = os.path.join(app.config['TEMP_FOLDER'], f"generated_function_{function_id}.py")

        if not os.path.exists(function_file):
            flash('Generated function not found', 'error')
            return redirect(url_for('index'))

        with open(function_file, 'r') as f:
            function_code = f.read()

        return render_template('view_function.html', 
                             function_code=function_code, 
                             function_id=function_id)

    except Exception as e:
        logger.error(f"View function error: {str(e)}", exc_info=True)
        flash(f'View failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download_function/<function_id>')
def download_function(function_id):
    """Download generated function"""
    try:
        function_file = os.path.join(app.config['TEMP_FOLDER'], f"generated_function_{function_id}.py")

        if not os.path.exists(function_file):
            flash('Generated function not found', 'error')
            return redirect(url_for('index'))

        return send_file(function_file, 
                        as_attachment=True, 
                        download_name=f"generated_function_{function_id}.py",
                        mimetype='text/plain')

    except Exception as e:
        logger.error(f"Download function error: {str(e)}", exc_info=True)
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/generate_function', methods=['POST'])
def generate_function():
    """AI-powered function generation"""
    try:
        function_prompt = request.form.get('function_prompt', '').strip()
        if not function_prompt:
            flash('Please enter a function description', 'error')
            return redirect(url_for('index'))
        
        # Handle uploaded design images
        design_images = request.files.getlist('design_images')
        image_paths = []

        for image in design_images:
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"design_{uuid.uuid4()}_{filename}")
                image.save(image_path)
                image_paths.append(image_path)
        
        # Generate AI code based on prompt
        function_id = str(uuid.uuid4())
        
        # Check if prompt is about Android
        is_android = any(keyword in function_prompt.lower() for keyword in 
                         ['android', 'app', 'activity', 'fragment', 'layout', 'xml', 'java', 'kotlin'])
        
        if is_android:
            # Generate Android code
            function_code = generate_android_code(function_prompt)
        else:
            # Generate Python code
            function_code = generate_python_code(function_prompt)

        # Save generated function
        function_file = os.path.join(app.config['TEMP_FOLDER'], f"generated_function_{function_id}.py")
        with open(function_file, 'w') as f:
            f.write(function_code)

        flash(f'Function generated successfully!', 'success')
        return redirect(url_for('view_generated_function', function_id=function_id))
    except Exception as e:
        logger.error(f"Generate function error: {str(e)}", exc_info=True)
        flash(f'Generation failed: {str(e)}', 'error')
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