/**
 * Face recognition functionality for attendance system
 */

class FaceRecognition {
    constructor(options = {}) {
        this.webcamHandler = options.webcamHandler || null;
        this.sessionId = options.sessionId || null;
        this.recognitionEndpoint = options.recognitionEndpoint || null;
        this.recognitionCallback = options.recognitionCallback || null;
        this.recognitionResultElement = options.recognitionResultElement || document.getElementById('recognition-result');
        this.studentNameElement = options.studentNameElement || document.getElementById('student-name');
        this.processingDelay = options.processingDelay || 3000; // Delay after successful recognition
        this.isProcessing = false;
        
        // Bind methods
        this.processImage = this.processImage.bind(this);
        this.showRecognitionResult = this.showRecognitionResult.bind(this);
        this.hideRecognitionResult = this.hideRecognitionResult.bind(this);
        
        // Initialize if all required options are present
        if (this.webcamHandler && this.recognitionEndpoint) {
            this.init();
        }
    }
    
    /**
     * Initialize the face recognition system
     */
    init() {
        // Set up webcam handler callback
        this.webcamHandler.captureCallback = this.processImage;
    }
    
    /**
     * Process captured image for face recognition
     * @param {string} imageData - Base64 encoded image data
     */
    async processImage(imageData) {
        // Skip if already processing an image
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        
        try {
            // Show loading indicator
            this.webcamHandler.showLoading();
            
            // Send to recognition endpoint
            const response = await fetch(this.recognitionEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData }),
            });
            
            const data = await response.json();
            
            // Hide loading indicator
            this.webcamHandler.hideLoading();
            
            if (data.success) {
                // Student recognized
                this.showRecognitionResult(data.student);
                
                // Pause capture for a few seconds
                this.webcamHandler.stopCaptureInterval();
                setTimeout(() => {
                    this.hideRecognitionResult();
                    this.webcamHandler.startCaptureInterval();
                    this.isProcessing = false;
                }, this.processingDelay);
                
                // Call recognition callback if provided
                if (this.recognitionCallback) {
                    this.recognitionCallback(data);
                }
            } else {
                // No student recognized or error
                console.log('Recognition result:', data.message);
                this.isProcessing = false;
            }
        } catch (error) {
            console.error('Error during face recognition:', error);
            this.webcamHandler.hideLoading();
            this.isProcessing = false;
        }
    }
    
    /**
     * Show recognition result
     * @param {Object} student - Student information
     */
    showRecognitionResult(student) {
        if (this.recognitionResultElement) {
            this.recognitionResultElement.classList.remove('d-none');
        }
        
        if (this.studentNameElement) {
            this.studentNameElement.textContent = student.name;
        }
    }
    
    /**
     * Hide recognition result
     */
    hideRecognitionResult() {
        if (this.recognitionResultElement) {
            this.recognitionResultElement.classList.add('d-none');
        }
    }
}

// Example usage:
// document.addEventListener('DOMContentLoaded', function() {
//     const webcamHandler = new WebcamHandler();
//     
//     const faceRecognition = new FaceRecognition({
//         webcamHandler: webcamHandler,
//         sessionId: '123',
//         recognitionEndpoint: '/api/recognize',
//         recognitionCallback: (data) => {
//             console.log('Student recognized:', data.student.name);
//         }
//     });
// });
