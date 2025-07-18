import os
import logging
import json
import base64
import io
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter, ImageEnhance

logger = logging.getLogger("APKEditor")

class AIHelper:
    """Helper class for AI-based GUI modifications"""
    
    def __init__(self, temp_folder="temp"):
        """Initialize the AI helper"""
        self.temp_folder = temp_folder
        os.makedirs(temp_folder, exist_ok=True)
        
        # Load color schemes
        self.color_schemes = {
            "blue": {
                "primary": "#1976D2",
                "secondary": "#2196F3",
                "accent": "#BBDEFB",
                "text": "#FFFFFF",
                "background": "#0D47A1"
            },
            "green": {
                "primary": "#388E3C",
                "secondary": "#4CAF50",
                "accent": "#C8E6C9",
                "text": "#FFFFFF",
                "background": "#1B5E20"
            },
            "red": {
                "primary": "#D32F2F",
                "secondary": "#F44336",
                "accent": "#FFCDD2",
                "text": "#FFFFFF",
                "background": "#B71C1C"
            },
            "purple": {
                "primary": "#7B1FA2",
                "secondary": "#9C27B0",
                "accent": "#E1BEE7",
                "text": "#FFFFFF",
                "background": "#4A148C"
            },
            "orange": {
                "primary": "#F57C00",
                "secondary": "#FF9800",
                "accent": "#FFE0B2",
                "text": "#FFFFFF",
                "background": "#E65100"
            },
            "dark": {
                "primary": "#212121",
                "secondary": "#424242",
                "accent": "#757575",
                "text": "#FFFFFF",
                "background": "#000000"
            },
            "light": {
                "primary": "#FAFAFA",
                "secondary": "#F5F5F5",
                "accent": "#EEEEEE",
                "text": "#212121",
                "background": "#FFFFFF"
            }
        }
    
    def analyze_gui_changes(self, description):
        """Analyze GUI change description and extract key modifications"""
        description = description.lower()
        changes = {
            "colors": [],
            "sizes": [],
            "effects": [],
            "layout": []
        }
        
        # Extract color changes
        color_keywords = ["blue", "green", "red", "yellow", "orange", "purple", "pink", "black", "white", "gray", "grey", "dark", "light"]
        for color in color_keywords:
            if color in description:
                changes["colors"].append(color)
        
        # Extract size changes
        size_keywords = ["bigger", "larger", "smaller", "wider", "taller", "thinner", "resize"]
        for size in size_keywords:
            if size in description:
                changes["sizes"].append(size)
        
        # Extract effect changes
        effect_keywords = ["glow", "shadow", "gradient", "transparent", "opacity", "blur", "sharp", "bold", "italic"]
        for effect in effect_keywords:
            if effect in description:
                changes["effects"].append(effect)
        
        # Extract layout changes
        layout_keywords = ["move", "position", "align", "center", "left", "right", "top", "bottom", "margin", "padding"]
        for layout in layout_keywords:
            if layout in description:
                changes["layout"].append(layout)
        
        return changes
    
    def generate_app_preview(self, project_name, color_scheme=None, gui_changes=None):
        """Generate a simple app preview based on project name and optional color scheme"""
        try:
            # Set default dimensions for the preview
            width, height = 300, 600
            
            # Choose color scheme
            colors = self.color_schemes.get(color_scheme, self.color_schemes["blue"])
            if not color_scheme and gui_changes:
                # Try to extract color scheme from GUI changes
                for color in self.color_schemes.keys():
                    if color in gui_changes.lower():
                        colors = self.color_schemes[color]
                        break
            
            # Create base image
            img = Image.new('RGB', (width, height), colors["background"])
            draw = ImageDraw.Draw(img)
            
            # Add status bar
            draw.rectangle([(0, 0), (width, 30)], fill="#000000")
            
            # Add app header
            draw.rectangle([(0, 30), (width, 90)], fill=colors["primary"])
            
            # Try to load a font, fall back to default if not available
            try:
                font_title = ImageFont.truetype("arial.ttf", 20)
                font_normal = ImageFont.truetype("arial.ttf", 14)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except IOError:
                font_title = ImageFont.load_default()
                font_normal = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Add app title
            title_text = project_name
            draw.text((width//2, 60), title_text, fill=colors["text"], font=font_title, anchor="mm")
            
            # Add status icons
            draw.text((width-50, 15), "100%", fill="#FFFFFF", font=font_small, anchor="mm")
            draw.text((20, 15), "9:41", fill="#FFFFFF", font=font_small, anchor="mm")
            
            # Add main content area
            content_top = 100
            content_height = height - content_top - 70  # Leave space for bottom nav
            draw.rectangle([(10, content_top), (width-10, content_top+content_height)], fill=colors["secondary"])
            
            # Add some UI elements based on GUI changes
            if gui_changes:
                changes = self.analyze_gui_changes(gui_changes)
                
                # Add controller elements
                self._add_controller_elements(draw, width, content_top, content_height, colors, changes)
            else:
                # Add placeholder text
                draw.text((width//2, height//2), "App Preview", fill=colors["text"], font=font_title, anchor="mm")
                draw.text((width//2, height//2 + 30), "Based on your modifications", fill=colors["text"], font=font_normal, anchor="mm")
            
            # Add bottom navigation bar
            draw.rectangle([(0, height-70), (width, height)], fill=colors["primary"])
            
            # Add nav buttons
            button_width = width // 4
            for i in range(4):
                x = i * button_width + button_width // 2
                draw.rectangle([(x-20, height-50), (x+20, height-10)], fill=colors["accent"])
            
            # Apply effects if specified in GUI changes
            if gui_changes and "glow" in gui_changes.lower():
                img = self._apply_glow_effect(img)
            
            if gui_changes and "blur" in gui_changes.lower():
                img = img.filter(ImageFilter.GaussianBlur(radius=1))
            
            # Save the preview image
            preview_id = datetime.now().strftime("%Y%m%d%H%M%S")
            preview_path = os.path.join(self.temp_folder, f"preview_{preview_id}.png")
            img.save(preview_path)
            
            # Convert to base64 for embedding in HTML
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                "preview_path": preview_path,
                "preview_base64": img_str,
                "color_scheme": color_scheme or "blue"
            }
            
        except Exception as e:
            logger.error(f"Error generating app preview: {str(e)}")
            return None
    
    def _add_controller_elements(self, draw, width, content_top, content_height, colors, changes):
        """Add controller UI elements based on changes"""
        center_x = width // 2
        center_y = content_top + content_height // 2
        
        # Add joystick/d-pad
        d_pad_size = 80
        if "bigger" in changes["sizes"] or "larger" in changes["sizes"]:
            d_pad_size = 100
        elif "smaller" in changes["sizes"]:
            d_pad_size = 60
            
        # D-pad background
        draw.ellipse(
            [(center_x - d_pad_size//2, center_y - d_pad_size//2), 
             (center_x + d_pad_size//2, center_y + d_pad_size//2)], 
            fill=colors["accent"]
        )
        
        # D-pad center
        draw.ellipse(
            [(center_x - d_pad_size//4, center_y - d_pad_size//4), 
             (center_x + d_pad_size//4, center_y + d_pad_size//4)], 
            fill=colors["primary"]
        )
        
        # Add control buttons
        button_size = 30
        button_spacing = 70
        
        # A button
        draw.ellipse(
            [(center_x + button_spacing - button_size//2, center_y - button_size//2), 
             (center_x + button_spacing + button_size//2, center_y + button_size//2)], 
            fill=colors["primary"]
        )
        
        # B button
        draw.ellipse(
            [(center_x + button_spacing*2 - button_size//2, center_y - button_size//2), 
             (center_x + button_spacing*2 + button_size//2, center_y + button_size//2)], 
            fill=colors["primary"]
        )
        
        # Add connection status
        status_y = content_top + 30
        draw.text((center_x, status_y), "Bluetooth Connected", fill=colors["text"], anchor="mm")
        
        # Add signal indicator
        signal_x = center_x + 80
        signal_y = status_y
        for i in range(3):
            draw.rectangle(
                [(signal_x + i*10, signal_y - i*3 - 5), 
                 (signal_x + i*10 + 5, signal_y)], 
                fill=colors["text"]
            )
    
    def _apply_glow_effect(self, img):
        """Apply a glow effect to the image"""
        # Create a blurred version for the glow
        glow = img.filter(ImageFilter.GaussianBlur(radius=10))
        glow = ImageEnhance.Brightness(glow).enhance(1.2)
        
        # Blend with original
        return Image.blend(glow, img, 0.7)
    
    def apply_gui_changes(self, project_id, project_dir, gui_changes, color_scheme):
        """Apply GUI changes to the project files"""
        try:
            decompiled_dir = os.path.join(project_dir, 'decompiled')
            
            # Track modified files
            modified_files = []
            
            # Apply color scheme changes to XML files
            if color_scheme and color_scheme != "Keep Current":
                colors = self.color_schemes.get(color_scheme, self.color_schemes["blue"])
                
                # Update colors.xml if it exists
                colors_xml_path = os.path.join(decompiled_dir, 'res/values/colors.xml')
                if os.path.exists(colors_xml_path):
                    with open(colors_xml_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace primary color
                    content = self._replace_color_in_xml(content, "colorPrimary", colors["primary"])
                    content = self._replace_color_in_xml(content, "colorPrimaryDark", colors["background"])
                    content = self._replace_color_in_xml(content, "colorAccent", colors["accent"])
                    
                    with open(colors_xml_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    modified_files.append(colors_xml_path)
                else:
                    # Create colors.xml if it doesn't exist
                    os.makedirs(os.path.join(decompiled_dir, 'res/values'), exist_ok=True)
                    with open(colors_xml_path, 'w', encoding='utf-8') as f:
                        f.write(f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">{colors["primary"]}</color>
    <color name="colorPrimaryDark">{colors["background"]}</color>
    <color name="colorAccent">{colors["accent"]}</color>
    <color name="textColor">{colors["text"]}</color>
</resources>''')
                    
                    modified_files.append(colors_xml_path)
            
            # Apply specific GUI changes based on description
            if gui_changes:
                changes = self.analyze_gui_changes(gui_changes)
                
                # Update layout files
                layout_dir = os.path.join(decompiled_dir, 'res/layout')
                if os.path.exists(layout_dir):
                    for layout_file in os.listdir(layout_dir):
                        if layout_file.endswith('.xml'):
                            layout_path = os.path.join(layout_dir, layout_file)
                            with open(layout_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Apply size changes
                            if any(size in changes["sizes"] for size in ["bigger", "larger"]):
                                content = self._increase_element_sizes(content)
                            
                            # Apply effect changes
                            if "glow" in changes["effects"]:
                                content = self._add_glow_effect_to_xml(content)
                            
                            with open(layout_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            modified_files.append(layout_path)
            
            # Generate a preview of the changes
            preview_info = self.generate_app_preview(
                project_name=project_id, 
                color_scheme=color_scheme, 
                gui_changes=gui_changes
            )
            
            return {
                "modified_files": modified_files,
                "preview": preview_info
            }
            
        except Exception as e:
            logger.error(f"Error applying GUI changes: {str(e)}")
            return {
                "modified_files": [],
                "preview": None,
                "error": str(e)
            }
    
    def _replace_color_in_xml(self, content, color_name, new_color):
        """Replace a color value in XML content"""
        import re
        pattern = f'<color name="{color_name}">.*?</color>'
        replacement = f'<color name="{color_name}">{new_color}</color>'
        
        # Check if the color exists
        if re.search(pattern, content):
            return re.sub(pattern, replacement, content)
        else:
            # Add the color if it doesn't exist
            insert_point = content.find('</resources>')
            if insert_point > 0:
                return content[:insert_point] + f'    {replacement}\n' + content[insert_point:]
            else:
                return content
    
    def _increase_element_sizes(self, content):
        """Increase the size of elements in XML layout"""
        import re
        
        # Increase width and height attributes
        content = re.sub(r'android:layout_width="(\d+)dp"', 
                        lambda m: f'android:layout_width="{int(m.group(1)) * 1.2:.0f}dp"', 
                        content)
        
        content = re.sub(r'android:layout_height="(\d+)dp"', 
                        lambda m: f'android:layout_height="{int(m.group(1)) * 1.2:.0f}dp"', 
                        content)
        
        # Increase text sizes
        content = re.sub(r'android:textSize="(\d+)sp"', 
                        lambda m: f'android:textSize="{int(m.group(1)) * 1.2:.0f}sp"', 
                        content)
        
        return content
    
    def _add_glow_effect_to_xml(self, content):
        """Add glow effect to elements in XML layout"""
        import re
        
        # Add shadow to buttons and text views
        button_pattern = r'<Button\s+([^>]*)>'
        textview_pattern = r'<TextView\s+([^>]*)>'
        
        shadow_props = 'android:elevation="8dp" android:stateListAnimator="@android:anim/button_state_list_anim"'
        
        content = re.sub(button_pattern, f'<Button \\1 {shadow_props}>', content)
        content = re.sub(textview_pattern, f'<TextView \\1 android:shadowColor="#80000000" android:shadowDx="2" android:shadowDy="2" android:shadowRadius="4">', content)
        
        return content