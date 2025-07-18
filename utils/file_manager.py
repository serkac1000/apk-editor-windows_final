import os
import json
import shutil
import logging
from datetime import datetime

class FileManager:
    def __init__(self, projects_folder):
        self.projects_folder = projects_folder
        os.makedirs(projects_folder, exist_ok=True)
    
    def list_projects(self):
        """List all projects"""
        projects = []
        
        try:
            for project_id in os.listdir(self.projects_folder):
                project_path = os.path.join(self.projects_folder, project_id)
                if os.path.isdir(project_path):
                    metadata_path = os.path.join(project_path, 'metadata.json')
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        # Add calculated fields
                        metadata['size'] = self._get_directory_size(project_path)
                        metadata['has_compiled'] = os.path.exists(os.path.join(project_path, 'compiled.apk'))
                        metadata['has_signed'] = os.path.exists(os.path.join(project_path, 'signed.apk'))
                        
                        projects.append(metadata)
            
            # Sort by creation date (newest first)
            projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            logging.error(f"Error listing projects: {str(e)}")
        
        return projects
    
    def get_project(self, project_id):
        """Get project metadata"""
        try:
            project_path = os.path.join(self.projects_folder, project_id)
            metadata_path = os.path.join(project_path, 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Add calculated fields
                metadata['size'] = self._get_directory_size(project_path)
                metadata['has_compiled'] = os.path.exists(os.path.join(project_path, 'compiled.apk'))
                metadata['has_signed'] = os.path.exists(os.path.join(project_path, 'signed.apk'))
                
                return metadata
            
        except Exception as e:
            logging.error(f"Error getting project: {str(e)}")
        
        return None
    
    def delete_project(self, project_id):
        """Delete a project"""
        try:
            project_path = os.path.join(self.projects_folder, project_id)
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
                logging.info(f"Project deleted: {project_id}")
                return True
            
        except Exception as e:
            logging.error(f"Error deleting project: {str(e)}")
        
        return False
    
    def update_project_metadata(self, project_id, updates):
        """Update project metadata"""
        try:
            project_path = os.path.join(self.projects_folder, project_id)
            metadata_path = os.path.join(project_path, 'metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Update fields
                metadata.update(updates)
                metadata['updated_at'] = datetime.now().isoformat()
                
                # Save updated metadata
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logging.info(f"Project metadata updated: {project_id}")
                return True
            
        except Exception as e:
            logging.error(f"Error updating project metadata: {str(e)}")
        
        return False
    
    def _get_directory_size(self, directory):
        """Calculate directory size"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logging.error(f"Error calculating directory size: {str(e)}")
        
        return total_size
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
