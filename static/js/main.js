// APK Editor JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('APK Editor initialized');

    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // File upload handling
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                console.log(`Selected file: ${fileName} (${fileSize} MB)`);

                // Update UI to show selected file
                const button = document.querySelector('.file-upload-button');
                if (button) {
                    button.textContent = fileName;
                    button.classList.add('file-selected');
                }
            }
        });
    }

    // Form submission handling
    const uploadForm = document.querySelector('#upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = uploadForm.querySelector('input[type="file"]');
            const projectName = uploadForm.querySelector('input[name="project_name"]');

            if (!fileInput.files[0]) {
                e.preventDefault();
                alert('Please select an APK file to upload.');
                return;
            }

            if (!projectName.value.trim()) {
                e.preventDefault();
                alert('Please enter a project name.');
                return;
            }

            // Show loading state
            const submitButton = uploadForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.textContent = 'Uploading...';
                submitButton.disabled = true;
            }
        });
    }

    // AI Function Generator form handling
    const aiForm = document.querySelector('#ai-function-form');
    if (aiForm) {
        aiForm.addEventListener('submit', function(e) {
            const promptInput = aiForm.querySelector('textarea[name="function_prompt"]');

            if (!promptInput.value.trim()) {
                e.preventDefault();
                alert('Please describe the function you want to generate.');
                return;
            }

            // Show loading state
            const submitButton = aiForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.textContent = 'Generating...';
                submitButton.disabled = true;
            }
        });
    }

    // GUI Changes form handling
    const guiForm = document.querySelector('#gui-changes-form');
    if (guiForm) {
        guiForm.addEventListener('submit', function(e) {
            const changesInput = guiForm.querySelector('textarea[name="gui_changes"]');

            if (!changesInput.value.trim()) {
                e.preventDefault();
                alert('Please describe the GUI changes you want.');
                return;
            }

            // Show loading state
            const submitButton = guiForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.textContent = 'Applying Changes...';
                submitButton.disabled = true;
            }
        });
    }

    // Project action buttons
    const actionButtons = document.querySelectorAll('.action-button');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.dataset.action;

            if (action === 'delete') {
                if (!confirm('Are you sure you want to delete this project?')) {
                    e.preventDefault();
                    return;
                }
            }

            if (action === 'compile') {
                this.textContent = 'Compiling...';
                this.disabled = true;
            }
        });
    });

    // Image preview functionality
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create or update preview
                    let preview = input.parentNode.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'image-preview';
                        preview.style.maxWidth = '200px';
                        preview.style.maxHeight = '200px';
                        preview.style.marginTop = '10px';
                        input.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
    });
});

// APKEditor object for backwards compatibility
const APKEditor = {
    init: function() {
        console.log('APK Editor initialized via APKEditor.init()');
    },

    uploadFile: function(file) {
        console.log('File upload requested:', file);
    },

    generateFunction: function(prompt) {
        console.log('Function generation requested:', prompt);
    },

    modifyGUI: function(changes) {
        console.log('GUI modification requested:', changes);
    }
};

// Auto-initialize APKEditor
APKEditor.init();