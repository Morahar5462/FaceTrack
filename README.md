#FaceTrack – Face Recognition Attendance System
FaceTrack is a web-based facial recognition attendance system built to automate and modernize the attendance process in educational institutions.
By leveraging deep learning models for face detection and recognition, it provides a fast, secure, and reliable alternative to traditional attendance methods.

✨ Features
Student & Teacher Modules

Students: Face registration & attendance marking

Teachers: Attendance session control, reporting, and CSV export

Accurate Face Recognition

MTCNN for face detection & alignment

FaceNet for generating unique face embeddings

Robust Under Different Lighting

OpenCV preprocessing (brightness/contrast adjustment, histogram equalization)

Secure by Design

Role-based access control

No raw image storage – only embeddings

Encrypted communications (HTTPS-ready)

Data Export

Downloadable CSV attendance reports

🛠 Tech Stack
Frontend
HTML, CSS, JavaScript

Backend
Python (Flask)

SQLAlchemy ORM

Database
PostgreSQL

Face Recognition
MTCNN – Face Detection

FaceNet – Face Embedding

OpenCV – Image Processing

Other Tools
Docker (Optional for deployment)

Replit (for cloud-based development)

Virtual Environment for dependency isolation

