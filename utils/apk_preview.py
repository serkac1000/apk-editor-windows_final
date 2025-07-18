import os
import logging
import subprocess
import shutil
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import io
import base64

class APKPreview:
    def __init__(self, temp_folder):
        self.temp_folder = temp_folder
        os.makedirs(temp_folder, exist_ok=True)
    
    def is_button_element(self, tag):
        """Return True if the tag represents a button (standard or common custom)."""
        # Normalize tag to ignore namespaces
        tag_name = tag.split('}')[-1] if '}' in tag else tag
        button_like = [
            'Button',
            'AppCompatButton',
            'MaterialButton',
        ]
        if tag_name == 'Button' or tag_name.endswith('Button'):
            return True
        if tag_name in button_like:
            return True
        # Add more custom button class names if needed
        return False
    
    def extract_app_icon(self, apk_path, project_id):
        """Extract the app icon from APK"""
        try:
            # Create temp directory for extraction
            extract_dir = os.path.join(self.temp_folder, f"icon_extract_{project_id}")
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extract AndroidManifest.xml and resources
            with zipfile.ZipFile(apk_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.startswith('res/drawable') and file.endswith('.png'):
                        zip_ref.extract(file, extract_dir)
                    if file == 'AndroidManifest.xml':
                        zip_ref.extract(file, extract_dir)
                    if file.startswith('res/mipmap') and file.endswith('.png'):
                        zip_ref.extract(file, extract_dir)
            
            # Look for icon in common locations
            icon_paths = [
                'res/mipmap-xxxhdpi/ic_launcher.png',
                'res/mipmap-xxhdpi/ic_launcher.png',
                'res/mipmap-xhdpi/ic_launcher.png',
                'res/mipmap-hdpi/ic_launcher.png',
                'res/mipmap-mdpi/ic_launcher.png',
                'res/drawable/ic_launcher.png',
                'res/drawable-xxxhdpi/ic_launcher.png',
                'res/drawable-xxhdpi/ic_launcher.png',
                'res/drawable-xhdpi/ic_launcher.png',
                'res/drawable-hdpi/ic_launcher.png',
                'res/drawable-mdpi/ic_launcher.png'
            ]
            
            for icon_path in icon_paths:
                full_path = os.path.join(extract_dir, icon_path)
                if os.path.exists(full_path):
                    # Save icon to project directory
                    icon_dest = os.path.join(self.temp_folder, f"icon_{project_id}.png")
                    shutil.copy2(full_path, icon_dest)
                    return icon_dest
            
            # If no icon found, create a placeholder
            return self._create_placeholder_icon(project_id)
            
        except Exception as e:
            logging.error(f"Error extracting app icon: {str(e)}")
            return self._create_placeholder_icon(project_id)
        finally:
            # Clean up
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
    
    def _create_placeholder_icon(self, project_id):
        """Create a placeholder icon when extraction fails"""
        try:
            icon_size = 192
            icon = Image.new('RGBA', (icon_size, icon_size), (52, 152, 219))
            draw = ImageDraw.Draw(icon)
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            draw.text((icon_size/2, icon_size/2), "APK", fill=(255, 255, 255), font=font, anchor="mm")
            
            # Save icon
            icon_path = os.path.join(self.temp_folder, f"icon_{project_id}.png")
            icon.save(icon_path)
            return icon_path
            
        except Exception as e:
            logging.error(f"Error creating placeholder icon: {str(e)}")
            return None
    
    def extract_app_name(self, decompiled_dir):
        """Extract app name from strings.xml"""
        try:
            strings_path = os.path.join(decompiled_dir, 'res/values/strings.xml')
            if os.path.exists(strings_path):
                tree = ET.parse(strings_path)
                root = tree.getroot()
                
                # Look for app_name string
                for string in root.findall('.//string'):
                    if string.get('name') == 'app_name':
                        return string.text
            
            # If not found, check AndroidManifest.xml
            manifest_path = os.path.join(decompiled_dir, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()
                
                # Get application label
                app_element = root.find('.//application')
                if app_element is not None:
                    label = app_element.get('{http://schemas.android.com/apk/res/android}label')
                    if label and label.startswith('@string/'):
                        # Try to resolve string reference
                        string_name = label.replace('@string/', '')
                        if os.path.exists(strings_path):
                            tree = ET.parse(strings_path)
                            root = tree.getroot()
                            for string in root.findall('.//string'):
                                if string.get('name') == string_name:
                                    return string.text
                    elif label:
                        return label
            
            return "Unknown App"
            
        except Exception as e:
            logging.error(f"Error extracting app name: {str(e)}")
            return "Unknown App"
    
    def extract_main_activity(self, decompiled_dir):
        """Extract main activity from AndroidManifest.xml"""
        try:
            manifest_path = os.path.join(decompiled_dir, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()
                
                # Find main activity
                for activity in root.findall('.//activity'):
                    for intent_filter in activity.findall('.//intent-filter'):
                        action = intent_filter.find('.//action')
                        category = intent_filter.find('.//category')
                        
                        if (action is not None and 
                            action.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.action.MAIN' and
                            category is not None and
                            category.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.category.LAUNCHER'):
                            
                            return activity.get('{http://schemas.android.com/apk/res/android}name')
            
            return None
            
        except Exception as e:
            logging.error(f"Error extracting main activity: {str(e)}")
            return None
    
    def extract_layout_preview(self, decompiled_dir, project_id):
        """Extract and render layout preview"""
        try:
            # Find main activity layout
            main_activity = self.extract_main_activity(decompiled_dir)
            if not main_activity:
                return self._create_layout_preview(project_id, None)
            
            # Look for layout files
            layout_dir = os.path.join(decompiled_dir, 'res/layout')
            if not os.path.exists(layout_dir):
                return self._create_layout_preview(project_id, None)
            
            # Try to find main layout
            layout_files = os.listdir(layout_dir)
            main_layout = None
            
            # Common layout names
            common_layouts = ['activity_main.xml', 'main.xml', 'main_activity.xml']
            
            for layout in common_layouts:
                if layout in layout_files:
                    main_layout = os.path.join(layout_dir, layout)
                    break
            
            # If not found, use first layout
            if not main_layout and layout_files:
                main_layout = os.path.join(layout_dir, layout_files[0])
            
            return self._create_layout_preview(project_id, main_layout)
            
        except Exception as e:
            logging.error(f"Error extracting layout preview: {str(e)}")
            return self._create_layout_preview(project_id, None)
    
    def _create_layout_preview(self, project_id, layout_path):
        """Create a preview image from layout XML"""
        try:
            # Create a blank image
            width, height = 360, 640
            image = Image.new('RGBA', (width, height), (30, 30, 30))
            draw = ImageDraw.Draw(image)
            
            # Add status bar
            draw.rectangle([(0, 0), (width, 30)], fill=(20, 20, 20))
            
            # Try to load layout
            if layout_path and os.path.exists(layout_path):
                try:
                    tree = ET.parse(layout_path)
                    root = tree.getroot()
                    
                    # Simple layout rendering (very basic)
                    self._render_layout_element(draw, root, 0, 30, width, height-30)
                except Exception as e:
                    logging.error(f"Error parsing layout: {str(e)}")
                    # Add error text
                    draw.text((width/2, height/2), "Layout Preview Error", fill=(255, 100, 100), anchor="mm")
            else:
                # Add placeholder text
                draw.text((width/2, height/2), "No Layout Found", fill=(200, 200, 200), anchor="mm")
            
            # Save preview
            preview_path = os.path.join(self.temp_folder, f"layout_preview_{project_id}.png")
            image.save(preview_path)
            return preview_path
            
        except Exception as e:
            logging.error(f"Error creating layout preview: {str(e)}")
            return None
    
    def _render_layout_element(self, draw, element, x, y, width, height, depth=0):
        """Recursively render layout elements (improved button recognition)"""
        if depth > 5:  # Limit recursion
            return
        tag = element.tag
        if tag.endswith('LinearLayout'):
            orientation = element.get('{http://schemas.android.com/apk/res/android}orientation', 'vertical')
            # Draw background
            draw.rectangle([(x, y), (x+width, y+height)], outline=(100, 100, 100))
            # Process children
            children = list(element)
            if children:
                if orientation == 'vertical':
                    child_height = height / len(children)
                    for i, child in enumerate(children):
                        self._render_layout_element(
                            draw, child, 
                            x, y + i * child_height, 
                            width, child_height, 
                            depth + 1
                        )
                else:  # horizontal
                    child_width = width / len(children)
                    for i, child in enumerate(children):
                        self._render_layout_element(
                            draw, child, 
                            x + i * child_width, y, 
                            child_width, height, 
                            depth + 1
                        )
        elif tag.endswith('TextView'):
            text = element.get('{http://schemas.android.com/apk/res/android}text', 'Text')
            if text.startswith('@string/'):
                text = text.replace('@string/', '')
            # Draw text placeholder
            draw.rectangle([(x, y), (x+width, y+30)], fill=(60, 60, 60))
            draw.text((x + width/2, y + 15), text, fill=(200, 200, 200), anchor="mm")
        elif self.is_button_element(tag):
            # Button rendering is temporarily disabled
            pass
        elif tag.endswith('ImageView'):
            # Draw image placeholder
            draw.rectangle([(x, y), (x+width, y+width)], fill=(80, 80, 80))
            draw.line([(x, y), (x+width, y+width)], fill=(120, 120, 120))
            draw.line([(x+width, y), (x, y+width)], fill=(120, 120, 120))
        elif tag.endswith('FrameLayout'):
            # Draw frame
            draw.rectangle([(x, y), (x+width, y+height)], outline=(100, 100, 100))
            # Process children
            for child in element:
                self._render_layout_element(draw, child, x+5, y+5, width-10, height-10, depth+1)
        else:
            # Generic element
            draw.rectangle([(x, y), (x+width, y+height)], outline=(80, 80, 80))
    
    def generate_app_preview(self, project_id, decompiled_dir, apk_path):
        """Generate complete app preview"""
        try:
            # Extract app icon
            icon_path = self.extract_app_icon(apk_path, project_id)
            
            # Extract app name
            app_name = self.extract_app_name(decompiled_dir)
            
            # Generate layout preview
            layout_preview = self.extract_layout_preview(decompiled_dir, project_id)
            
            # Create preview data
            preview_data = {
                'icon': icon_path,
                'name': app_name,
                'layout': layout_preview
            }
            
            return preview_data
            
        except Exception as e:
            logging.error(f"Error generating app preview: {str(e)}")
            return None
    
    def get_image_base64(self, image_path):
        """Convert image to base64 for embedding in HTML"""
        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    return base64.b64encode(img_file.read()).decode('utf-8')
            return None
        except Exception as e:
            logging.error(f"Error converting image to base64: {str(e)}")
            return None