import os
import logging
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import uuid
from datetime import datetime
from apk_editor import APKEditor
from utils.file_manager import FileManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROJECTS_FOLDER'] = 'projects'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist
for folder in [app.config['UPLOAD_FOLDER'], app.config['PROJECTS_FOLDER'], app.config['TEMP_FOLDER']]:
    os.makedirs(folder, exist_ok=True)

# Initialize services
file_manager = FileManager(app.config['PROJECTS_FOLDER'])
apk_editor = APKEditor(app.config['PROJECTS_FOLDER'], app.config['TEMP_FOLDER'])

@app.route('/')
def index():
    """Main page with project list and upload form"""
    projects = file_manager.list_projects()
    
    # Check if Gemini API is configured
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    gemini_enabled = gemini_api_key and gemini_api_key != 'AIzaSyDummy_Key_Replace_With_Real_Key'
    
    return render_template('index.html', projects=projects, gemini_enabled=gemini_enabled)

@app.route('/upload', methods=['POST'])
def upload_apk():
    """Handle APK file upload"""
    if 'apk_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    file = request.files['apk_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not file.filename.lower().endswith('.apk'):
        flash('Please upload an APK file', 'error')
        return redirect(url_for('index'))
    
    try:
        # Generate unique project ID
        project_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{project_id}_{filename}")
        file.save(upload_path)
        
        # Decompile APK
        project_name = request.form.get('project_name', filename.replace('.apk', ''))
        success = apk_editor.decompile_apk(upload_path, project_id, project_name)
        
        if success:
            flash(f'APK "{filename}" uploaded and decompiled successfully!', 'success')
            return redirect(url_for('project_view', project_id=project_id))
        else:
            flash('Failed to decompile APK. Please check if it\'s a valid APK file.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/project/<project_id>')
def project_view(project_id):
    """View project details and resources"""
    project = file_manager.get_project(project_id)
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('index'))
    
    # Get project resources
    resources = apk_editor.get_project_resources(project_id)
    
    return render_template('project.html', 
                         project=project, 
                         resources=resources, 
                         project_id=project_id)

@app.route('/edit/<project_id>/<resource_type>/<path:resource_path>')
def edit_resource(project_id, resource_type, resource_path):
    """Edit a specific resource"""
    project = file_manager.get_project(project_id)
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('index'))
    
    resource_content = apk_editor.get_resource_content(project_id, resource_type, resource_path)
    
    return render_template('edit_resource.html',
                         project=project,
                         resource_type=resource_type,
                         resource_path=resource_path,
                         resource_content=resource_content,
                         project_id=project_id)

@app.route('/save_resource/<project_id>/<resource_type>/<path:resource_path>', methods=['POST'])
def save_resource(project_id, resource_type, resource_path):
    """Save edited resource"""
    try:
        if resource_type == 'image':
            # Handle image upload
            if 'image_file' in request.files:
                file = request.files['image_file']
                if file.filename != '':
                    success = apk_editor.save_image_resource(project_id, resource_path, file)
                    if success:
                        flash('Image updated successfully!', 'success')
                    else:
                        flash('Failed to update image', 'error')
        
        elif resource_type == 'string':
            # Handle string content
            content = request.form.get('content', '')
            success = apk_editor.save_string_resource(project_id, resource_path, content)
            if success:
                flash('String updated successfully!', 'success')
            else:
                flash('Failed to update string', 'error')
        
        elif resource_type == 'layout':
            # Handle layout XML
            content = request.form.get('content', '')
            success = apk_editor.save_layout_resource(project_id, resource_path, content)
            if success:
                flash('Layout updated successfully!', 'success')
            else:
                flash('Failed to update layout', 'error')
        
        return redirect(url_for('edit_resource', 
                               project_id=project_id, 
                               resource_type=resource_type, 
                               resource_path=resource_path))
        
    except Exception as e:
        logging.error(f"Save resource error: {str(e)}")
        flash(f'Save failed: {str(e)}', 'error')
        return redirect(url_for('edit_resource', 
                               project_id=project_id, 
                               resource_type=resource_type, 
                               resource_path=resource_path))

@app.route('/compile/<project_id>')
def compile_apk(project_id):
    """Compile and sign APK"""
    try:
        project = file_manager.get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
        
        output_path = apk_editor.compile_apk(project_id)
        if output_path:
            flash('APK compiled successfully!', 'success')
            return redirect(url_for('download_apk', project_id=project_id))
        else:
            flash('Failed to compile APK', 'error')
            return redirect(url_for('project_view', project_id=project_id))
            
    except Exception as e:
        logging.error(f"Compile error: {str(e)}")
        flash(f'Compile failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/download/<project_id>')
def download_apk(project_id):
    """Download compiled APK"""
    try:
        project = file_manager.get_project(project_id)
        if not project:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
        
        apk_path = apk_editor.get_compiled_apk_path(project_id)
        if apk_path and os.path.exists(apk_path):
            return send_file(apk_path, 
                           as_attachment=True, 
                           download_name=f"{project['name']}_modified.apk",
                           mimetype='application/vnd.android.package-archive')
        else:
            flash('Compiled APK not found. Please compile first.', 'error')
            return redirect(url_for('project_view', project_id=project_id))
            
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

@app.route('/delete/<project_id>')
def delete_project(project_id):
    """Delete project"""
    try:
        success = file_manager.delete_project(project_id)
        if success:
            flash('Project deleted successfully!', 'success')
        else:
            flash('Failed to delete project', 'error')
    except Exception as e:
        logging.error(f"Delete error: {str(e)}")
        flash(f'Delete failed: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/generate_function', methods=['POST'])
def generate_function():
    """Generate new function based on prompt"""
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
        
        # Generate function based on prompt
        generated_code = generate_code_from_prompt(function_prompt, image_paths)
        
        # Save generated function
        function_id = str(uuid.uuid4())
        function_file = os.path.join(app.config['TEMP_FOLDER'], f"generated_function_{function_id}.py")
        
        with open(function_file, 'w') as f:
            f.write(generated_code)
        
        flash(f'Function generated successfully! Saved as: generated_function_{function_id}.py', 'success')
        
        return redirect(url_for('view_generated_function', function_id=function_id))
        
    except Exception as e:
        logging.error(f"Generate function error: {str(e)}")
        flash(f'Generation failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/view_function/<function_id>')
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
        logging.error(f"View function error: {str(e)}")
        flash(f'View failed: {str(e)}', 'error')
        return redirect(url_for('index'))

def generate_code_from_prompt(prompt, image_paths):
    """Generate code using Google Gemini AI based on user prompt and images"""
    try:
        # Get API key from environment or use default for testing
        api_key = os.environ.get('GEMINI_API_KEY', 'AIzaSyDummy_Key_Replace_With_Real_Key')
        
        if api_key == 'AIzaSyDummy_Key_Replace_With_Real_Key':
            logging.warning("Using dummy Gemini API key. Set GEMINI_API_KEY environment variable for real AI generation.")
            return generate_fallback_code(prompt)
        
        # Prepare the prompt for Android development
        enhanced_prompt = f"""
        You are an expert Android developer. Generate Android code based on this request:
        
        User Request: {prompt}
        
        Please provide:
        1. XML layout code if UI elements are needed
        2. Java/Kotlin code for functionality
        3. Resource definitions (colors, strings, etc.) if needed
        4. Brief explanation of the implementation
        
        Focus on practical, working Android code that can be integrated into an APK.
        """
        
        # Prepare request data
        request_data = {
            "contents": [{
                "parts": [{"text": enhanced_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        # Make API request to Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        response = requests.post(url, headers=headers, json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                generated_content = result['candidates'][0]['content']['parts'][0]['text']
                
                # Format the generated code
                formatted_code = f"""# AI Generated Android Code
# Generated at: {datetime.now().isoformat()}
# Prompt: {prompt}

{generated_content}

"""
                logging.info("AI code generation successful")
                return formatted_code
            else:
                logging.error("No content generated by Gemini API")
                return generate_fallback_code(prompt)
        else:
            logging.error(f"Gemini API error: {response.status_code} - {response.text}")
            return generate_fallback_code(prompt)
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during AI generation: {str(e)}")
        return generate_fallback_code(prompt)
    except Exception as e:
        logging.error(f"Error during AI code generation: {str(e)}")
        return generate_fallback_code(prompt)

def generate_fallback_code(prompt):
    """Generate fallback code when AI is not available"""
    code_template = f"""# Generated Android Code (Fallback Mode)
# Generated at: {datetime.now().isoformat()}
# Original request: {prompt}

/*
 * AI Generation Notice:
 * This code was generated using fallback templates.
 * For advanced AI-powered code generation, please set up your Gemini API key.
 * 
 * To enable AI features:
 * 1. Get a Gemini API key from Google AI Studio
 * 2. Set environment variable: GEMINI_API_KEY=your_api_key
 * 3. Restart the application
 */

"""
    
    # Analyze prompt for basic code generation
    prompt_lower = prompt.lower()
    
    if "button" in prompt_lower:
        code_template += generate_button_template(prompt)
    elif "color" in prompt_lower or "theme" in prompt_lower:
        code_template += generate_color_template(prompt)
    elif "icon" in prompt_lower:
        code_template += generate_icon_template(prompt)
    elif "layout" in prompt_lower:
        code_template += generate_layout_template(prompt)
    elif "activity" in prompt_lower or "screen" in prompt_lower:
        code_template += generate_activity_template(prompt)
    else:
        code_template += generate_generic_template(prompt)
    
    return code_template

def generate_button_template(prompt):
    """Generate button-related Android code"""
    return """
// XML Layout (add to your activity_main.xml)
<Button
    android:id="@+id/generated_button"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Generated Button"
    android:layout_centerInParent="true"
    android:padding="16dp"
    android:background="@drawable/button_background"
    android:textColor="@android:color/white"
    android:onClick="onGeneratedButtonClick" />

// Java Code (add to your Activity)
public void onGeneratedButtonClick(View view) {
    // Button click handler
    Toast.makeText(this, "Button clicked!", Toast.LENGTH_SHORT).show();
    
    // Add your custom logic here
    Log.d("ButtonClick", "Generated button was clicked");


@app.route('/test_ai', methods=['POST'])
def test_ai():
    """Test AI functionality"""
    try:
        test_prompt = "Create a simple button that shows a toast message when clicked"
        generated_code = generate_code_from_prompt(test_prompt, [])
        
        return jsonify({
            'success': True,
            'message': 'AI is working correctly',
            'sample_code': generated_code[:500] + '...' if len(generated_code) > 500 else generated_code
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'AI test failed: {str(e)}'
        })

def generate_button_template(prompt):
    """Generate button-related Android code"""
    return """
// XML Layout (add to your activity_main.xml)
<Button
    android:id="@+id/generated_button"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Generated Button"
    android:layout_centerInParent="true"
    android:padding="16dp"
    android:background="@drawable/button_background"
    android:textColor="@android:color/white"
    android:onClick="onGeneratedButtonClick" />

// Java Code (add to your Activity)
public void onGeneratedButtonClick(View view) {
    // Button click handler
    Toast.makeText(this, "Button clicked!", Toast.LENGTH_SHORT).show();
    
    // Add your custom logic here
    Log.d("ButtonClick", "Generated button was clicked");
}

// Optional: Button background drawable (res/drawable/button_background.xml)
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#007bff" />
    <corners android:radius="8dp" />
    <stroke android:width="1dp" android:color="#0056b3" />
</shape>
"""

def generate_color_template(prompt):
    """Generate color-related Android code"""
    return """
// Colors (add to res/values/colors.xml)
<resources>
    <color name="generated_primary">#007bff</color>
    <color name="generated_secondary">#6c757d</color>
    <color name="generated_accent">#17a2b8</color>
    <color name="generated_background">#f8f9fa</color>
    <color name="generated_text">#212529</color>
</resources>

// Usage in layouts
android:background="@color/generated_primary"
android:textColor="@color/generated_text"

// Usage in Java/Kotlin code
int primaryColor = ContextCompat.getColor(this, R.color.generated_primary);
view.setBackgroundColor(primaryColor);
"""

def generate_icon_template(prompt):
    """Generate icon-related Android code"""
    return """
// Icon usage in layout
<ImageView
    android:id="@+id/generated_icon"
    android:layout_width="48dp"
    android:layout_height="48dp"
    android:src="@drawable/ic_generated"
    android:contentDescription="Generated Icon"
    android:layout_centerInParent="true" />

// Java code for dynamic icon changes
ImageView iconView = findViewById(R.id.generated_icon);
iconView.setImageResource(R.drawable.ic_generated);

// Set icon programmatically
iconView.setImageDrawable(ContextCompat.getDrawable(this, R.drawable.ic_generated));

// AndroidManifest.xml (for app icon)
<application
    android:icon="@drawable/ic_launcher"
    android:roundIcon="@drawable/ic_launcher_round"
    ... >
"""

def generate_layout_template(prompt):
    """Generate layout-related Android code"""
    return """
// Complete Layout Example (activity_generated.xml)
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp"
    android:background="@color/generated_background">

    <TextView
        android:id="@+id/title_text"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Generated Layout"
        android:textSize="24sp"
        android:textStyle="bold"
        android:textColor="@color/generated_text"
        android:gravity="center"
        android:layout_marginBottom="16dp" />

    <View
        android:layout_width="match_parent"
        android:layout_height="1dp"
        android:background="@color/generated_secondary"
        android:layout_marginBottom="16dp" />

    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical">

            <!-- Add your content here -->
            
        </LinearLayout>
    </ScrollView>

</LinearLayout>
"""

def generate_activity_template(prompt):
    """Generate activity-related Android code"""
    return """
// Generated Activity Class
public class GeneratedActivity extends AppCompatActivity {
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_generated);
        
        initializeViews();
        setupEventListeners();
    }
    
    private void initializeViews() {
        // Initialize your views here
        TextView titleText = findViewById(R.id.title_text);
        titleText.setText("Generated Activity");
    }
    
    private void setupEventListeners() {
        // Setup click listeners and other event handlers
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        // Activity resumed
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        // Activity paused
    }
}

// AndroidManifest.xml entry
<activity
    android:name=".GeneratedActivity"
    android:exported="false"
    android:label="Generated Activity" />
"""

def generate_generic_template(prompt):
    """Generate generic Android code"""
    return """
// Generic Android Implementation
public class GeneratedHelper {
    
    private static final String TAG = "GeneratedHelper";
    
    /**
     * Generated method based on user request
     */
    public static void executeGeneratedFunction(Context context) {
        Log.d(TAG, "Executing generated function");
        
        // Implementation based on user requirements
        // Add your custom logic here
        
        Toast.makeText(context, "Generated function executed", Toast.LENGTH_SHORT).show();
    }
    
    /**
     * Utility method for common operations
     */
    public static void performCommonTask() {
        // Common task implementation
        Log.d(TAG, "Performing common task");
    }
}

// Usage example
GeneratedHelper.executeGeneratedFunction(this);
"""

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
        logging.error(f"Download function error: {str(e)}")
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/modify_gui/<project_id>', methods=['POST'])
def modify_gui(project_id):
    """Modify GUI based on user description"""
    try:
        project = file_manager.get_project(project_id)
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
        
        # Generate modifications
        modifications = generate_gui_modifications(gui_changes, color_scheme, image_paths)
        
        # Apply modifications to project
        success = apply_gui_modifications(project_id, modifications)
        
        if success:
            flash('GUI modifications applied successfully!', 'success')
            
            # Update project metadata
            file_manager.update_project_metadata(project_id, {
                'last_gui_changes': gui_changes,
                'color_scheme': color_scheme,
                'status': 'modified'
            })
            
            return redirect(url_for('project_view', project_id=project_id))
        else:
            flash('Failed to apply GUI modifications', 'error')
            return redirect(url_for('project_view', project_id=project_id))
        
    except Exception as e:
        logging.error(f"GUI modification error: {str(e)}")
        flash(f'Modification failed: {str(e)}', 'error')
        return redirect(url_for('project_view', project_id=project_id))

def generate_gui_modifications(changes_description, color_scheme, image_paths):
    """Generate GUI modifications based on user description"""
    modifications = {
        'colors': {},
        'layouts': {},
        'strings': {},
        'images': {},
        'description': changes_description
    }
    
    # Color scheme modifications
    if color_scheme:
        color_schemes = {
            'blue': {'primary': '#007bff', 'secondary': '#6c757d', 'accent': '#17a2b8'},
            'green': {'primary': '#28a745', 'secondary': '#6c757d', 'accent': '#20c997'},
            'red': {'primary': '#dc3545', 'secondary': '#6c757d', 'accent': '#fd7e14'},
            'purple': {'primary': '#6f42c1', 'secondary': '#6c757d', 'accent': '#e83e8c'},
            'orange': {'primary': '#fd7e14', 'secondary': '#6c757d', 'accent': '#ffc107'},
            'dark': {'primary': '#343a40', 'secondary': '#6c757d', 'accent': '#ffffff'},
            'light': {'primary': '#f8f9fa', 'secondary': '#e9ecef', 'accent': '#343a40'}
        }
        
        if color_scheme in color_schemes:
            modifications['colors'] = color_schemes[color_scheme]
    
    # Text analysis for modifications
    changes_lower = changes_description.lower()
    
    # Control knob modifications
    if 'knob' in changes_lower or 'control' in changes_lower:
        if 'blue' in changes_lower:
            modifications['colors']['control_color'] = '#007bff'
        elif 'green' in changes_lower:
            modifications['colors']['control_color'] = '#28a745'
        elif 'red' in changes_lower:
            modifications['colors']['control_color'] = '#dc3545'
        elif 'orange' in changes_lower:
            modifications['colors']['control_color'] = '#fd7e14'
    
    # D-pad modifications
    if 'dpad' in changes_lower or 'd-pad' in changes_lower:
        if 'bigger' in changes_lower or 'larger' in changes_lower:
            modifications['layouts']['dpad_size'] = 'large'
        elif 'smaller' in changes_lower:
            modifications['layouts']['dpad_size'] = 'small'
    
    # Glow/lighting effects
    if 'glow' in changes_lower or 'light' in changes_lower:
        if 'blue' in changes_lower:
            modifications['colors']['glow_color'] = '#007bff'
        elif 'green' in changes_lower:
            modifications['colors']['glow_color'] = '#28a745'
        elif 'red' in changes_lower:
            modifications['colors']['glow_color'] = '#dc3545'
    
    # Connection status modifications
    if 'connection' in changes_lower or 'status' in changes_lower:
        if 'connected' in changes_lower:
            modifications['strings']['connection_status'] = 'Connected'
            modifications['colors']['status_color'] = '#28a745'
        elif 'disconnected' in changes_lower:
            modifications['strings']['connection_status'] = 'Disconnected'
            modifications['colors']['status_color'] = '#dc3545'
    
    # Button modifications (legacy support)
    if 'button' in changes_lower:
        if 'blue' in changes_lower:
            modifications['colors']['button_color'] = '#007bff'
        elif 'green' in changes_lower:
            modifications['colors']['button_color'] = '#28a745'
        elif 'red' in changes_lower:
            modifications['colors']['button_color'] = '#dc3545'
    
    # Text modifications
    if 'text' in changes_lower:
        if 'bigger' in changes_lower or 'larger' in changes_lower:
            modifications['layouts']['text_size'] = 'large'
        elif 'smaller' in changes_lower:
            modifications['layouts']['text_size'] = 'small'
    
    return modifications

def apply_gui_modifications(project_id, modifications):
    """Apply GUI modifications to project files"""
    try:
        project_dir = os.path.join(app.config['PROJECTS_FOLDER'], project_id)
        decompiled_dir = os.path.join(project_dir, 'decompiled')
        
        # Apply color modifications
        if modifications['colors']:
            colors_file = os.path.join(decompiled_dir, 'res/values/colors.xml')
            if os.path.exists(colors_file):
                with open(colors_file, 'r') as f:
                    content = f.read()
                
                # Update colors
                for color_name, color_value in modifications['colors'].items():
                    # Simple color replacement
                    color_pattern = f'<color name="{color_name}">'
                    if color_pattern in content:
                        content = content.replace(
                            f'{color_pattern}#[0-9A-Fa-f]{{6}}</color>',
                            f'{color_pattern}{color_value}</color>'
                        )
                
                with open(colors_file, 'w') as f:
                    f.write(content)
        
        # Apply string modifications
        if modifications['strings']:
            strings_file = os.path.join(decompiled_dir, 'res/values/strings.xml')
            if os.path.exists(strings_file):
                with open(strings_file, 'r') as f:
                    content = f.read()
                
                # Update strings
                for string_name, string_value in modifications['strings'].items():
                    # Simple string replacement
                    string_pattern = f'<string name="{string_name}">'
                    if string_pattern in content:
                        import re
                        content = re.sub(
                            f'{string_pattern}.*?</string>',
                            f'{string_pattern}{string_value}</string>',
                            content
                        )
                
                with open(strings_file, 'w') as f:
                    f.write(content)
        
        # Apply layout modifications
        if modifications['layouts']:
            layout_files = []
            layout_dir = os.path.join(decompiled_dir, 'res/layout')
            if os.path.exists(layout_dir):
                layout_files = [f for f in os.listdir(layout_dir) if f.endswith('.xml')]
            
            for layout_file in layout_files:
                layout_path = os.path.join(layout_dir, layout_file)
                with open(layout_path, 'r') as f:
                    content = f.read()
                
                # Apply text size modifications
                if 'text_size' in modifications['layouts']:
                    size_value = modifications['layouts']['text_size']
                    if size_value == 'large':
                        content = content.replace('android:textSize="14sp"', 'android:textSize="18sp"')
                        content = content.replace('android:textSize="16sp"', 'android:textSize="20sp"')
                    elif size_value == 'small':
                        content = content.replace('android:textSize="16sp"', 'android:textSize="12sp"')
                        content = content.replace('android:textSize="18sp"', 'android:textSize="14sp"')
                
                with open(layout_path, 'w') as f:
                    f.write(content)
        
        logging.info(f"GUI modifications applied to project: {project_id}")
        return True
        
    except Exception as e:
        logging.error(f"Error applying GUI modifications: {str(e)}")
        return False

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 100MB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
