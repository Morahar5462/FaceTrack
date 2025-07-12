import logging
import base64
import json
import numpy as np
import cv2
from io import BytesIO

logger = logging.getLogger(__name__)

# Load OpenCV face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def preprocess_base64_image(base64_string):
    """Convert base64 image to numpy array for face detection"""
    try:
        # Remove data URL prefix if present
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        # Decode base64 image
        img_data = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return gray
    except Exception as e:
        logger.error(f"Error processing base64 image: {str(e)}")
        return None

def extract_face_encoding(image_data):
    """Extract face features from image data (either base64 string or numpy array)"""
    try:
        # If image_data is a base64 string, preprocess it
        if isinstance(image_data, str):
            img = preprocess_base64_image(image_data)
        else:
            img = image_data
            
        if img is None:
            logger.error("Failed to preprocess image")
            return None
            
        # Detect faces
        faces = face_cascade.detectMultiScale(img, 1.1, 4)
        
        if len(faces) == 0:
            logger.warning("No faces detected in the image")
            return None
            
        # Get the largest face (assuming it's the most prominent one)
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        # Extract face region
        face_region = img[y:y+h, x:x+w]
        
        # Resize to a standard size for consistency
        face_resized = cv2.resize(face_region, (100, 100))
        
        # Flatten the face image to create a feature vector
        face_encoding = face_resized.flatten().tolist()
        
        return face_encoding
    except Exception as e:
        logger.error(f"Error extracting face encoding: {str(e)}")
        return None

def compare_faces(known_encoding, unknown_encoding, tolerance=5000):
    """Compare face encodings and return True if they match"""
    try:
        if known_encoding is None or unknown_encoding is None:
            return False
            
        # Convert to numpy arrays if needed
        if isinstance(known_encoding, list):
            known_encoding = np.array(known_encoding)
        if isinstance(unknown_encoding, list):
            unknown_encoding = np.array(unknown_encoding)
            
        # Calculate Euclidean distance between encodings
        distance = np.linalg.norm(known_encoding - unknown_encoding)
        
        # Return True if distance is below tolerance threshold
        logger.info(f"Face comparison distance: {distance}")
        return distance < tolerance
    except Exception as e:
        logger.error(f"Error comparing faces: {str(e)}")
        return False

def is_duplicate_face(new_encoding, existing_encodings, tolerance=5000):
    """Check if a face encoding already exists in the database"""
    if not new_encoding or not existing_encodings:
        return False
    
    for encoding in existing_encodings:
        if compare_faces(new_encoding, encoding, tolerance):
            return True
    
    return False
