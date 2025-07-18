
// APK Editor JavaScript functionality
const APKEditor = {
    init: function() {
        console.log('APK Editor initialized');
        this.setupEventListeners();
        this.initializeFeatherIcons();
    },

    setupEventListeners: function() {
        // File upload validation
        const fileInput = document.getElementById('apk_file');
        if (fileInput) {
            fileInput.addEventListener('change', this.validateFileUpload);
        }

        // Project form validation
        const projectForm = document.getElementById('uploadForm');
        if (projectForm) {
            projectForm.addEventListener('submit', this.validateProjectForm);
        }

        // GUI modification form
        const guiForm = document.querySelector('form[action*="modify_gui"]');
        if (guiForm) {
            guiForm.addEventListener('submit', this.validateGuiForm);
        }

        // Function generator form
        const functionForm = document.querySelector('form[action*="generate_function"]');
        if (functionForm) {
            functionForm.addEventListener('submit', this.validateFunctionForm);
        }

        // Image preview for uploads
        const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
        imageInputs.forEach(input => {
            input.addEventListener('change', this.previewImages);
        });
    },

    initializeFeatherIcons: function() {
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    },

    validateFileUpload: function(event) {
        const file = event.target.files[0];
        const errorDiv = document.getElementById('file-error');
        
        if (errorDiv) {
            errorDiv.textContent = '';
        }

        if (file) {
            // Check file size (100MB limit)
            if (file.size > 100 * 1024 * 1024) {
                if (errorDiv) {
                    errorDiv.textContent = 'File size must be less than 100MB';
                    errorDiv.className = 'alert alert-danger mt-2';
                }
                event.target.value = '';
                return false;
            }

            // Check file extension
            if (!file.name.toLowerCase().endsWith('.apk')) {
                if (errorDiv) {
                    errorDiv.textContent = 'Please select an APK file';
                    errorDiv.className = 'alert alert-danger mt-2';
                }
                event.target.value = '';
                return false;
            }

            // Show file info
            const fileInfo = document.getElementById('file-info');
            if (fileInfo) {
                fileInfo.innerHTML = `
                    <div class="alert alert-info mt-2">
                        <strong>Selected:</strong> ${file.name} (${APKEditor.formatFileSize(file.size)})
                    </div>
                `;
            }
        }

        return true;
    },

    validateProjectForm: function(event) {
        const projectName = document.getElementById('project_name');
        const fileInput = document.getElementById('apk_file');

        if (!projectName || !projectName.value.trim()) {
            alert('Please enter a project name');
            event.preventDefault();
            return false;
        }

        if (!fileInput || !fileInput.files[0]) {
            alert('Please select an APK file');
            event.preventDefault();
            return false;
        }

        // Show loading state
        const submitBtn = event.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading...';
        }

        return true;
    },

    validateGuiForm: function(event) {
        const guiChanges = document.getElementById('gui_changes');
        
        if (!guiChanges || !guiChanges.value.trim()) {
            alert('Please describe the GUI changes you want');
            event.preventDefault();
            return false;
        }

        // Show loading state
        const submitBtn = event.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Applying Changes...';
        }

        return true;
    },

    validateFunctionForm: function(event) {
        const functionPrompt = document.getElementById('function_prompt');
        
        if (!functionPrompt || !functionPrompt.value.trim()) {
            alert('Please describe the function you want to generate');
            event.preventDefault();
            return false;
        }

        // Show loading state
        const submitBtn = event.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';
        }

        return true;
    },

    previewImages: function(event) {
        const files = event.target.files;
        const previewContainer = event.target.closest('.mb-3').querySelector('.image-preview');
        
        if (!previewContainer) {
            const preview = document.createElement('div');
            preview.className = 'image-preview mt-2';
            event.target.closest('.mb-3').appendChild(preview);
        }

        const container = event.target.closest('.mb-3').querySelector('.image-preview');
        container.innerHTML = '';

        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'img-thumbnail me-2 mb-2';
                    img.style.maxWidth = '100px';
                    img.style.maxHeight = '100px';
                    container.appendChild(img);
                };
                reader.readAsDataURL(file);
            }
        });
    },

    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    showAlert: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    APKEditor.init();
});

// Handle form submissions with progress
document.addEventListener('submit', function(event) {
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (submitBtn && !submitBtn.disabled) {
        const originalText = submitBtn.innerHTML;
        
        // Add progress indicator
        setTimeout(() => {
            if (submitBtn.disabled) {
                submitBtn.innerHTML = originalText.replace('Processing...', 'Processing...') || 
                                    '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            }
        }, 100);
    }
});
