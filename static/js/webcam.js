/**
 * Webcam utility functions for the attendance system
 */

class WebcamHandler {
    constructor(options = {}) {
        this.videoElement = options.videoElement || document.getElementById('webcam');
        this.canvasElement = options.canvasElement || document.getElementById('canvas');
        this.startButton = options.startButton || document.getElementById('start-btn');
        this.captureButton = options.captureButton || document.getElementById('capture-btn');
        this.stopButton = options.stopButton || document.getElementById('stop-btn');
        this.loadingIndicator = options.loadingIndicator || document.getElementById('loading-indicator');
        this.facingMode = options.facingMode || 'user'; // 'user' for front camera, 'environment' for back camera
        this.width = options.width || 640;
        this.height = options.height || 480;
        this.stream = null;
        this.isStreaming = false;
        this.captureInterval = null;
        this.captureCallback = options.captureCallback || null;
        this.captureIntervalTime = options.captureIntervalTime || 1000;
        this.autoStart = options.autoStart !== undefined ? options.autoStart : true;
        this.autoCapture = options.autoCapture !== undefined ? options.autoCapture : true;
        
        // Set up canvas
        this.context = this.canvasElement.getContext('2d');
        
        // Bind methods to this
        this.startCamera = this.startCamera.bind(this);
        this.stopCamera = this.stopCamera.bind(this);
        this.captureImage = this.captureImage.bind(this);
        this.startCaptureInterval = this.startCaptureInterval.bind(this);
        this.stopCaptureInterval = this.stopCaptureInterval.bind(this);
        
        // Initialize if all elements are present
        if (this.videoElement && this.canvasElement) {
            this.init();
        }
    }
    
    /**
     * Initialize event listeners
     */
    init() {
        // Set up button event listeners
        if (this.startButton) {
            this.startButton.addEventListener('click', this.startCamera);
            // Hide the start button as we'll start automatically
            if (this.autoStart) {
                this.startButton.style.display = 'none';
            }
        }
        
        if (this.captureButton) {
            this.captureButton.addEventListener('click', this.startCaptureInterval);
            // Hide the capture button if auto-capturing
            if (this.autoCapture) {
                this.captureButton.style.display = 'none';
            }
        }
        
        if (this.stopButton) {
            this.stopButton.addEventListener('click', this.stopCamera);
        }
        
        // Set up video event listeners
        this.videoElement.addEventListener('loadedmetadata', () => {
            this.canvasElement.width = this.videoElement.videoWidth;
            this.canvasElement.height = this.videoElement.videoHeight;
        });
        
        // Auto-start camera when page loads
        if (this.autoStart) {
            // Use setTimeout to ensure DOM is fully loaded
            setTimeout(() => {
                this.startCamera().then(success => {
                    // Start auto-capturing if enabled and camera started successfully
                    if (success && this.autoCapture) {
                        setTimeout(() => {
                            this.startCaptureInterval();
                        }, 500);
                    }
                });
            }, 500);
        }
    }
    
    /**
     * Start the webcam
     */
    async startCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: this.width },
                    height: { ideal: this.height },
                    facingMode: this.facingMode
                }
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.videoElement.srcObject = this.stream;
            this.isStreaming = true;
            
            // Update UI
            if (this.captureButton) this.captureButton.disabled = false;
            if (this.stopButton) this.stopButton.disabled = false;
            if (this.startButton) this.startButton.disabled = true;
            
            return true;
        } catch (err) {
            console.error('Error accessing webcam:', err);
            alert('Could not access webcam. Please ensure you have webcam permissions enabled.');
            return false;
        }
    }
    
    /**
     * Stop the webcam
     */
    stopCamera() {
        if (this.isStreaming && this.stream) {
            const tracks = this.stream.getTracks();
            
            tracks.forEach(track => track.stop());
            
            this.videoElement.srcObject = null;
            this.isStreaming = false;
            
            // Stop capture interval if active
            this.stopCaptureInterval();
            
            // Update UI
            if (this.captureButton) {
                this.captureButton.disabled = true;
                this.captureButton.innerHTML = '<i class="fas fa-camera me-1"></i> Capture';
            }
            if (this.stopButton) this.stopButton.disabled = true;
            if (this.startButton) this.startButton.disabled = false;
            
            return true;
        }
        return false;
    }
    
    /**
     * Capture a single image from the webcam
     * @returns {string|null} Base64 encoded image or null if not streaming
     */
    captureImage() {
        if (!this.isStreaming) return null;
        
        // Draw video frame to canvas
        this.context.drawImage(this.videoElement, 0, 0, this.canvasElement.width, this.canvasElement.height);
        
        // Get base64 image data
        return this.canvasElement.toDataURL('image/jpeg');
    }
    
    /**
     * Start capturing images at intervals
     */
    startCaptureInterval() {
        if (!this.isStreaming) return;
        
        if (!this.captureInterval) {
            // Start capture interval
            this.captureInterval = setInterval(() => {
                const imageData = this.captureImage();
                if (imageData && this.captureCallback) {
                    this.captureCallback(imageData);
                }
            }, this.captureIntervalTime);
            
            // Update UI
            if (this.captureButton) {
                this.captureButton.innerHTML = '<i class="fas fa-pause me-1"></i> Pause';
            }
        } else {
            // Stop capture interval
            this.stopCaptureInterval();
        }
    }
    
    /**
     * Stop the capture interval
     */
    stopCaptureInterval() {
        if (this.captureInterval) {
            clearInterval(this.captureInterval);
            this.captureInterval = null;
            
            // Update UI
            if (this.captureButton) {
                this.captureButton.innerHTML = '<i class="fas fa-play me-1"></i> Resume';
            }
        }
    }
    
    /**
     * Show loading indicator
     */
    showLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.classList.remove('d-none');
        }
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.classList.add('d-none');
        }
    }
}

// Example usage:
// const webcam = new WebcamHandler({
//     captureCallback: (imageData) => {
//         // Process the captured image
//         console.log('Image captured!', imageData.substring(0, 50) + '...');
//     }
// });
