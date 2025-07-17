/**
 * Main JavaScript file for FaceAttend
 * Contains utility functions and initialization code
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Current date for forms
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Alert auto-dismiss
    const alertList = document.querySelectorAll('.alert-dismissible.auto-dismiss');
    alertList.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000); // Dismiss after 5 seconds
    });
    
    // Search functionality
    const searchInputs = document.querySelectorAll('.table-search');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.dataset.tableTarget;
            const table = document.getElementById(tableId);
            
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });
    
    // Toggle password visibility
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const passwordInput = document.getElementById(targetId);
            
            if (passwordInput) {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                
                // Toggle icon
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-eye');
                    icon.classList.toggle('fa-eye-slash');
                }
            }
        });
    });
    
    // Initialize webcam on attendance pages if needed
    if (document.getElementById('webcam')) {
        initializeWebcam();
    }
});

/**
 * Initializes webcam functionality for attendance pages
 */
function initializeWebcam() {
    // Get session ID from data attribute or URL
    const sessionElement = document.querySelector('[data-session-id]');
    const sessionId = sessionElement ? sessionElement.dataset.sessionId : null;
    
    // Get recognition endpoint
    const recognitionEndpoint = sessionId ? 
        `/teacher/session/${sessionId}/face-recognition` : 
        null;
    
    if (recognitionEndpoint) {
        // Create webcam handler
        const webcamHandler = new WebcamHandler();
        
        // Create face recognition handler
        const faceRecognition = new FaceRecognition({
            webcamHandler: webcamHandler,
            recognitionEndpoint: recognitionEndpoint,
            recognitionCallback: updateAttendanceTable
        });
    }
}

/**
 * Updates the attendance table when a student is recognized
 * @param {Object} data - Recognition result data
 */
function updateAttendanceTable(data) {
    if (!data || !data.success) return;
    
    const studentId = data.student.id;
    const studentRow = document.getElementById(`student-row-${studentId}`);
    
    if (studentRow) {
        const statusBadge = studentRow.querySelector('.attendance-status');
        
        if (statusBadge) {
            statusBadge.textContent = 'Present';
            statusBadge.classList.remove('bg-danger', 'bg-warning');
            statusBadge.classList.add('bg-success');
        }
    }
}

/**
 * Formats a date as a readable string
 * @param {Date|string} dateInput - Date to format
 * @param {string} format - Format string ('short', 'medium', 'long')
 * @returns {string} Formatted date string
 */
function formatDate(dateInput, format = 'medium') {
    const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
    
    if (isNaN(date.getTime())) {
        return 'Invalid date';
    }
    
    const options = {
        short: { month: 'short', day: 'numeric' },
        medium: { month: 'short', day: 'numeric', year: 'numeric' },
        long: { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' }
    };
    
    return date.toLocaleDateString('en-US', options[format] || options.medium);
}

/**
 * Formats a percentage with specified precision
 * @param {number} value - Percentage value
 * @param {number} precision - Number of decimal places
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, precision = 1) {
    return value.toFixed(precision) + '%';
}
