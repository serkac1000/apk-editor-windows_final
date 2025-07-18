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
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROJECTS_FOLDER'], app.config['TEMP_FOLDER']]:
    os.makedirs(folder, exist_ok=True)
    logger.info(f"Directory created/verified: {folder}")

# Import the APK Signer modu
try:
    fromer
    logger.info("APK Signer module imported successf")
except ImportError as e:
    logger.warning(f"Could not import APK Signer module: {str(e)}")
    logger.warning("APK signing functionality will be limited")

def is_vle_path):
    """Basic APK file validation"""
    try:
        # Check file size (not
        file_size = os.path.getsize(file_path
        if file_size < 1000 or file
            logger.warning(f"Invalid APK size: {file_size} bytes")
            return False
        
        # Check fil
        with open(file_patf:
            header = f.read(4)
            # ZIP fi

                logg")
                return False
        
        return True
    
        ")
        return False

def list_projects():
    """List all projects in the projects folder"""
    projects = []
    projects_folder = app.config['PROJECTS_FOLDER']
    
    try:
        for project_id in os.listdir(projecolder):
            project_path = os.path.join(projects_folder, project_id)
            if os.path.isdir(project_path):
                metadata_path = os.path.join(project_path, 'metadata.json')
                if o:
                    with open(metadata_path, s f:
        )
                    
                    # Add calculated fields
        
                    metada'))
                    metadata['has_signed'] = os.path.exis
     
                   tadata)

        # Sort by creation dt)
        projects.sort(key=lamb
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
    
    return projects

def get_project(project_id):
    """Get p
    try:
        project_path = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        metadata_path = os.path.join(project_path, 'metadata.json')
        
        if o
            with open(metadas f:
        f)
            
            # Add calculated fields
    else 0
            met

     
            return metadata
        
    exce as e:
        logger.error(f"Error getti)
    
    return None


def simple_decompile_apk(apk_path, project_id, project_name):
    """Simple APK decompilation without using APKT
    try:
        # Create project directory
        project_dir = os.path.join(app.config['PROJECTS)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create decompiled directory
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        os.makedirs(decompiled_dir, exist_ok=True)
        
        # Extract APK contents (it's just a ZIP file)
        with zipfile.ZipFile(apk_path, 'r') as zip_ref:
            zip_ref.extractall(decompiled_dir)
        
        # Create basic structure if it doesn't exist
        for
            os.makedirs(os.path.join(decompiled_dir, folder),e)
        
        xist
        strings_path = os.path.joxml')
        if not os.pa
            with open(strings
                f.write('''<?xml >
<resources>
    <string name="app_name">''' + project_name + '''<ring>
</resources>''')
        
        ata
        metadata = {
            'id': project_id,
            'name': project_name,
            'original_apk': os.path.basenameath),
        (),
            'status': 'decompiled'
        }
        
        # Save metadata
        metadata_pa
        
            json.dump(meta
        
        # Copy original APK tject
        shutil.copy2(apk_path, os.path.join(project_dir, 'original.apk'))
        
        logger.info(f"APK decompiled sid}")
        return True
    

        logger.error(f"Decompile error
        # Clean up on failure
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project)
        if os.path.exists(project_dir):
    r)
        return False


def get_project_resou
    ""
    d)
    decopiled')
    
    resources = {
        'images': [],
        'strings': [],
        'layouts': []
    }
    
    try:
        #
        irs = [
            'res/drawable',
            'res/drawable-hdpi',
            'res/drawable-mdpi',
            'res/drawable-xhdpi',
            'res/drawable-xxhdpi',
            'res/drawable-xxxhdpi'
        ]
        
        for drawable_dir in drawable_dirs:
            drawable_path _dir)
        th):
                for file in os
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        resources['image
                            'name': file,
                            'path': osile),
                            'size': os.path.getsifile))
                        })
        
        sources
        strings_path = os.path')
        if os.path.exists(strings_path):
            resources['strings'].append({
                'name': 'strings.xml',
                'path': 'res/values/strin
                'size': os.path.getsize(strings_pth)
            })
        
        # Get layout resources
        layout_path = )
        :
            for file in os:
                if file.endswith('.xml'):
    end({
                    file,
ile),
               )
            
        
    excee:
        logger.error(f"Error getti
    
    return resources

@app.route('/')
def index():
    """Main page with project list and upload form"""
:
ts()
        logger.info(f"Listed {len(proje")
        return reed=False)
    except Exception as e:
        logger.error(f"Error in index route: {o=True)
    ")
        return render_template('index.h


@app.route('/upload', methods=['POST'])
):
    """Handle APK file upload"""
    logger.info("APK upload")
    
    if 'apk_file' not in request.files:
        logger.warning("No file part in t)
)
        return redirect(url_for('index'))

    file = request.files['apk_file']
    if file.filename == '':
")
        rror')
        return redirect(url_for('ind))

    if not file.filename.lower().endswith('.apk'):
        logger.warning(f"Invalid file extension: {file.filename}")

        return redirect(url_for('index'))

    try:
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        filename = secure_file
        logger.info(f"Processing APK upload: {filen")

        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDue)
        
        # Save uploaded file
        upload_path = os.path.join(app.confige}")
        fileath)
        logger.info(f"APK saved to:
        
        # Verify file was saved correctly
        
            logger.error(f"File
            flash('Error saving uploaded )
            return redirect(url_for('index'))
            
        # Get file size for logging
        file_size = os.path.getsize(upload_pa
")
        
        # Basic file validation
        if not is_valid_apk(upload_path):
            logger.warning(f"Invalid APK format: {filename}")

            os.remo
            return redirect(url_for('index'))

        # Decompile APK using simple method (no APKTool dependency)
        proje'))
        logger.info(f"Decompiling APK with project name: {projec
        success = simple_decompile_apk(upload_path, project_id, project_name)


            logger.info(f"")
            flash(f'APK "{filename}" uploaded and decompiled s
            return redirect(url_for('project_view'd))
        else:
")
r')
            return redirect(url_for))

    except Exception as e:
        nfo=True)
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/project/<project_id>')
def project_view(project_id):
"
    try:
        logger.info(f"Viewing project: {project_id}")
        project = get_project(project_id)

            logger.warning(f"Project not found:)
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Get project resources
        resources = get_pr)
        logger.info(f"Retrieved resources for project: {project_id}")

        return render_template('project.html', 
ect, 
                            resources=resources, 
                            project_id=project_id,
                            app_prn
    exceas e:
        logger.error(f"Error in project_v)
        flash(f"An erro)
        return redirect(url_for('index'))


def edit_resource(project_id, :
    """Edit a specific resource"""
    try:
        d)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Get resource content
        decompiled_dir = os.path.join()
        full_path = os.path.join(decompil)
        
= None
        if resource_type in ['string', 'layout']:
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf- f:
                    resource_content = f.read()
        elif resource_type == 'image':
            if os.path.exists(full_path):
                resource_c}

        return render_template('edit_resource.html',
                            project=proje
,

                            resource_content=resource_content,
                            project_id=project_id)
    except Exception as e:
        fo=True)
        flash(f"An error occurred: {str(e)
        return redirect


@app.route('ST'])
def save_resource(project_id, resource_type, resource_path):
    """Save edited resource"""
    try:
        project = get_project(projec
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
            
        decompiled_dir = os.path.join(app.conled')
        full_path = os.path.join(decompiled_dir, resource_path)
        
        if resource_type == 'image':
            # Handle image upload
            if 'imaget.files:
                file = request.files['image_file']

                    # Ensure directory exists
                    os.makedirs(ook=True)
                    # Save uploaded file
                    file.save(full_pah)
                    flash('Image updated successfully!', 'success'
                else:
                    flash('No image selected', 'error')

        elif resource_type == 'string' or resource_type == 'layout':
t
            content = request.form.get('content',)
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist)
            # Save content
 f:
                f.write(coent)
            flash(f'{resource_type.capitalize()} updated successfullyess')

        return redirect(url_for('edit_resource', 
                            project_id=project_id, 
                            resource_type=resource_type, 
                            resource_path=resource_path))


        logger.error(f"Save resourcfo=True)
        flash(f'Save failed:')
        return redirect(url_for('edit_reso
        d, 
                            resource_type_type, 
                       th))


id>')
def compile_apk(project_id):
    """Compile APK (simplified version)"""
    try:
        project = get_project(project_id)
        t:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        # Simple compilation - create a Z
        project_dir = os.path.join(app.config['PROJ)
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        outpd.apk')
        
        # Check if original APK exists to use as a base
        original_apk = os.path.join(project_dir,
        if o
            # Copy original APK as a base
            shutil.copy2(original_apk, output_path)
            logger.info(f"Using original APKation")
            
            # Create a temporary directory for merging
            temp_dir = os.path.join(app.config['TEMP_FOLDER']id}")
            os.makedirs(temp_dir, 
            
            # Extract original APK to temp directory
            with zipfile.ZipFile(original_apk, 'r') as zip_ref:
                zip_r)
            
            # Copy modified files from decompiled directory to temp direcy
            for root
                for file in files:
                    src_path = os.path.join(root, fi
            ed_dir)
                    dst_path = os.path.join(tempth)
                    
                    # Ensure directory exists
                    os.makedirs(os.patue)
                    
                    # Copy file
                    shutil.copy2(src_path, dst_path)
            
            # Create new APK from temrectory
            with zipfile.ZipFile(ou
             ir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
        else:
        e
            logger.warning(f"Original APK non")
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIf:
                for root, dirs, files in os.wair):
        iles:
                        file_path = e)
                        arcname = os.pa_dir)
                        zipf.write(file_path, arcnam)
        
        # Copy to signed.apk for consistency
        signe)
        shutil.copy2(output_path, signed_path)
        
        # Ved
        if os.path.exists(output_path):
)
            logger.info(f"
            flash('APK compiled successfully!', 'success')
        else:
            logger.error(f"Failed to create compiled APK: {output_path}")
)
      
        return redirect(url_for('dow

    except Exception as e:
        ue)
        flash(f'Compile failed: {str(e)}')
        return redirect)


t_id>')
def download_apk(project_id):
    """Download compiled APK"""
    try:
        project = get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))

        PK first
        project_dir = os.path.join(
        signed_path = os.path.join(project_dir, 'signed.apk')
        if os.path.exists(signed_path):
            return send_file(signed_path, 
                        as_attachment=True, 
                        download_name=f"{project['name']}_modified.apk",
                        mimetype='application/vnd.android.package-archive')
        
        # Fall back to compiled APK
        compiled_path = os.path.join(project_dir, 'compiled.apk')
:
            return send_fipath, 
                        as_attachment=True, 
                        download_name=f"{project['na",
                        mimetype='application/vnd.android.package-archi')
 
        flash('Compiled APK not fo)
        return redirect(url_forct_id))

    exces e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        flash(f'Download failed: {str(eror')
        return redirect(url_for('proje_id))

@app.route('/
def delete_project(project_id):
    """Delete project"""
    try:
        project_dir = os.path.join(app.config['PROoject_id)
ir):
            shutil.rmtree(project_dir)

:
            flash('Project not found', 'error')
    except Exception as e:
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        rror')

    return redirect(url


['POST'])
def modify_gui(project_id):
    """Modify GUI based on user description (simplified ver"""
try:
        project = get_project_id)
        if not project:
            flash('Project not found', 'error')
)

        gui_changes = request.form.get('gui_c
         '')

        if not gui_changes:
            flash('Please describe the GUI changes you want', 'err
        id))

        # In this simplified version, we just aequest
        # but don't actually modify anyles
        
        # Update project meanges
        project_dir = os.path_id)
        metadata_path = os.path.join(project_dirjson')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
              )
            
            # Update fields
            metadata.update({
                'last_gui_changes': gui_changes,
e,
                'status': 'modified',
                'updated_at': datetime.now().isoformat()
})
            
            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)


        return redirect(urject_id))

    except Exception as e:
        logger.error(f"GUI modification error:rue)
')
ct_id))


@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    return app.send_static_file('favicon.ico')


@app.route('/refresh_preview/<project_id>')
def refresh_preview(project_id):
    """Refresh the app preview"""

view
        flash('Preview refreshed', 'success')
        return redirect(
    except Exception as e:
        =True)
        flash(f'Refresh failed: {str(e)}', 'error')
        return redirect(url_fort_id))


@app.route('OST'])
def generate_function():
    """Simplified function generation"""
    try:
        function_prompt = request.form.get('p()
        if not function_prompt:
error')
            return redire
            
        # Generate side
        fud4())
        function_code = f"""# Generated Function
# Generated at: {datetime.now().isoformat()}
# P

def generated_function():
    \"\"\"
    {function_prompt}
    \"\"\"

    return "Function implementation would go here"
"""

        # Save generated function
        function_file = os.path.join(app.config['TEMP_")
        with open(function_file, 'w') as :
e)

        flash(f'Functi')
        return re
    except Exception as e:
        logger.error(f"Generate funct)
)
))


@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum sierror')
'))


@app.errorhandler(500)
def server_error(e):

    flash("Internal server err)
    return redirect(url_for('index'))


@app.route('/sign_apk_page/<pr)
def sign_apk_page(project_id):
    """S"
    try:
        project = get_p
        if not project:
            flash('Project not found', 'error
        '))
        
        # Check if compiled APK exists
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'],
        compiled_path = os.path.join(project_
        if not os.path.exists(compiled_path):
            flash('Compiled APK not found. Please compile first.', 'error')
        ect_id))
        
        # Initialize APK signer
        ])
        
        # Get available keystores
        
        
        return render_template('sign_apk.html',
                            project=project,
                            project_id=project_i
                          ores)
    except Exception as e:
        logger.error(f"Error in sign_apk_page: {str(e)e)
        flash(f"An error occurred: {str(e)}", "error")
t_id))

@app.route('/sign_apk/<pr])
def sign_apk(project_id):
    """Sre"""
    try:
        project = get_p
        if not project:
            flash('Project not found', 'error')
        
        
        # Get form data
        keystore = request.form.get('keystore')
        alias = request.form.get('alias')
        
        
        # Check if compiled APK exists
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'],id)
        compiled_path = os.path.join(project_dir, 'compiled.apk')
        pk')
        
        if not os.path.exists(compiled_path):
            flash('Compiled APK not found. Please compile first.', 'error')
        d))
        
        # Initialize APK signer
        ER'])
        
        # Use debug keystore if
        if keystore == 'debug':
            keystore = Nore
            alias = None
        ne
        
        # Sign the APK
        )
        
        if success:
            flash('APK signed successfully!', 'success')
            rd))
        else:
            flash(f'Failed to sign APK: {result}', 'error')
        d))
        
    except Exception as e:
        logger.error(f"Error in sign_apk: {str(e)}", eue)
        flash(f"An error occurred: {str(e)}", "error")


@app.route('/create_keystore/<pr)
def create_keystore(project_id)
    """Ce"""
    try:
        # Get form data
        keystore_name = request.form.get('key')
        alias = request.form.get('key_alias')
        password = request.form.get('key_password')
        common_name = request.form.get('common_')
        org_unit = request.form.get('
        org = request.form.get('org')
        locality = request.form.get('locality')
        state = request.form.get('state')
        country = request.form.get('country')
         25))
        
        # Initialize APK signer
        '])
        
        # Create keystore
        success, result = signer.create_key
            keystore_name, alias, passwd,
            common_name, org_unit, org,
          validity
        )
        
        if success:
            f)
        else:
        ')
        
        d))
        
    except Exception as e:
        logger.error(f"Error in create_keystore: {str(rue)
        flash(f"An error occurred: {str(e)}", "error")


@app.route('/download_tools')
def download_tools():
    """Dng"""
    try:
        # Initialize APK signer
        
        
        # Download tools
        ls()
        
        if success:
            fess')
        else:
        r')
        
        x'))
        
    except Exception as e:
        logger.error(f"Error downloading tools: {str(eTrue)
        flash(f"An error occurred: {str(ert=5000)0.0.0', pohost='0., bug=Truerun(deapp.ion")
    plicator apK Editng AP"Startio(inf   logger.n__':
 __ == '__mai
if __namex'))

r('inde(url_fon redirectetur        rr")
"erro)}", 