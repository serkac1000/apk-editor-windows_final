// APK Editor JavaScript functionality
const APKEditor = {
    init: function () {
        console.log('APK Editor initialized');

        // Initialize feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }

        this.initFileUpload();
        this.initFormValidation();
        this.initAlerts();
        this.initGUIModification();
    },

    initFileUpload: function () {
        const fileInput = document.querySelector('input[type="file"]');
        const fileLabel = document.querySelector('.file-upload-label');

        if (fileInput && fileLabel) {
            fileInput.addEventListener('change', function (e) {
                const fileName = e.target.files[0]?.name || 'Choose File';
                fileLabel.textContent = fileName;
            });
        }
    },

    initFormValidation: function () {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function (e) {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.classList.add('is-invalid');
                    } else {
                        field.classList.remove('is-invalid');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    alert('Please fill in all required fields');
                }
            });
        });
    },

    initAlerts: function () {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        });
    },

    initGUIModification: function () {
        const guiForm = document.getElementById('gui-modification-form');
        if (guiForm) {
            guiForm.addEventListener('submit', function (e) {
                const guiChanges = document.getElementById('gui_changes');
                if (guiChanges && !guiChanges.value.trim()) {
                    e.preventDefault();
                    alert('Please describe the GUI changes you want to make');
                    guiChanges.focus();
                }
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', function () {
    APKEditor.init();
});