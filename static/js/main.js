// Main JavaScript for APK Editor
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // File upload validation
    const fileInput = document.getElementById('apk_file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (!file.name.toLowerCase().endsWith('.apk')) {
                    showAlert('Please select a valid APK file', 'error');
                    this.value = '';
                    return;
                }
                
                if (file.size > 100 * 1024 * 1024) { // 100MB
                    showAlert('File size must be less than 100MB', 'error');
                    this.value = '';
                    return;
                }
                
                // Auto-fill project name if empty
                const projectNameInput = document.getElementById('project_name');
                if (projectNameInput && !projectNameInput.value) {
                    projectNameInput.value = file.name.replace('.apk', '');
                }
            }
        });
    }

    // Form submission with loading state
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                
                // Re-enable button after 30 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
                }, 30000);
            }
        });
    });

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Code editor enhancements
    const codeEditors = document.querySelectorAll('.code-editor');
    codeEditors.forEach(editor => {
        // Add line numbers (simple implementation)
        editor.addEventListener('scroll', function() {
            // Sync line numbers if they exist
            const lineNumbers = this.parentElement.querySelector('.line-numbers');
            if (lineNumbers) {
                lineNumbers.scrollTop = this.scrollTop;
            }
        });

        // Add tab support
        editor.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                
                // Insert tab character
                this.value = this.value.substring(0, start) + '\t' + this.value.substring(end);
                
                // Move cursor
                this.selectionStart = this.selectionEnd = start + 1;
            }
        });
    });

    // Confirmation dialogs
    const deleteLinks = document.querySelectorAll('a[href*="/delete/"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Image preview for image uploads
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create or update image preview
                    let preview = document.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('div');
                        preview.className = 'image-preview mt-3';
                        input.parentElement.appendChild(preview);
                    }
                    
                    preview.innerHTML = `
                        <img src="${e.target.result}" class="img-fluid rounded" style="max-width: 200px; max-height: 200px;">
                        <p class="text-muted mt-2">Preview: ${file.name}</p>
                    `;
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Progress tracking for long operations
    function trackProgress(operation, callback) {
        const progressModal = document.getElementById('progressModal');
        if (progressModal) {
            const modal = new bootstrap.Modal(progressModal);
            modal.show();
            
            // Simulate progress (in real implementation, use WebSockets or polling)
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 20;
                if (progress > 90) progress = 90;
                
                const progressBar = progressModal.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = progress + '%';
                }
                
                if (progress >= 90) {
                    clearInterval(interval);
                    if (callback) callback();
                }
            }, 500);
        }
    }
});

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showAlert('Failed to copy to clipboard', 'error');
    });
}

// Export functions for global use
window.APKEditor = {
    showAlert,
    formatFileSize,
    copyToClipboard
};
