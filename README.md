## FaceTrack: A Face Recognition-Based Attendance System 🧑‍🏫

**FaceTrack** is a modern, automated attendance system designed to simplify and secure the process of recording attendance in educational institutions using facial recognition technology. Built as a web application, it replaces traditional, time-consuming manual methods with a fast, efficient, and accurate solution.

-----

### Key Features ⚡

  * **Automated Attendance:** Students can mark their attendance by simply looking into a webcam.
  * **Secure & Private:** The system stores only **face embeddings** (numerical vectors), not raw images, ensuring user privacy. All communication is secured via HTTPS.
  * **Role-Based Access Control:** Differentiates between **Student** and **Teacher** roles, providing appropriate access to features.
  * **Detailed Reporting:** Teachers can generate and view attendance reports for their classes, with the option to export them as CSV files.
  * **Intuitive UI:** A user-friendly interface built with HTML, CSS, and JavaScript.
  * **Robust Backend:** Powered by **Python** and the **Flask** framework.
  * **Scalable Architecture:** The system is containerized, making it easy to deploy and scale.

-----

### Architecture 🏗️

The system is designed with a multi-layered architecture to ensure a clear separation of concerns and maintainability.

  * **Frontend Layer:** The user interface, built with HTML, CSS, and JavaScript, handles user interactions for student registration, attendance marking, and report viewing.
  * **Backend Layer:** A Python-based Flask application manages all server-side logic, including API requests, user authentication, and data processing.
  * **Face Recognition Module:**
      * **Face Detection:** Uses the **MTCNN** (Multi-task Cascaded Convolutional Neural Network) model to efficiently detect and align faces in images or webcam feeds.
      * **Face Recognition:** Leverages **FaceNet** to generate unique numerical vectors (embeddings) for each detected face.
  * **Database Layer:** A **PostgreSQL** database, managed via **SQLAlchemy ORM**, securely stores user data, face embeddings, and attendance records.
  * **Security Layer:** Implements **user authentication** and **role-based access control** to protect sensitive information. Communication is secured, and raw images are not stored.

-----

### How It Works 🤖

1.  **Registration:** A student registers by capturing their face through the webcam. The system uses MTCNN to detect and crop the face, then FaceNet generates a unique embedding. This embedding is securely stored in the PostgreSQL database.
2.  **Attendance Marking:** When a student attempts to mark attendance, the system captures their face in real-time and generates a new embedding.
3.  **Face Matching:** This new embedding is compared against the stored embeddings in the database using **cosine similarity** or **Euclidean distance**.
4.  **Verification:** If the similarity score exceeds a predefined threshold, the faces are considered a match, and attendance is marked as "Present." If not, the user is prompted to try again.

-----

### Overcoming Challenges 💡

During development, a key challenge was ensuring **face recognition accuracy in diverse lighting conditions**. To address this, the system incorporates several robust strategies:

  * **Image Preprocessing:** Uses **OpenCV** to apply real-time image preprocessing techniques like brightness/contrast adjustment, grayscale conversion, and histogram equalization. This enhances facial features, making them easier for MTCNN to detect.
  * **Robust Models:** Both MTCNN and FaceNet are deep learning models trained on diverse datasets, making them inherently more resilient to lighting variations.
  * **Threshold Tuning:** The similarity threshold is carefully tuned to balance accuracy and reliability across various environmental conditions.

-----

### Technologies Used 💻

  * **Backend:** Python, Flask, SQLAlchemy
  * **Frontend:** HTML, CSS, JavaScript
  * **Database:** PostgreSQL
  * **Face Recognition:** MTCNN, FaceNet, OpenCV
  * **Containerization:** Docker (for potential future deployment)

-----

### Setup and Installation 🛠️

To get a local copy up and running, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Morahar5462/FaceTrack.git
    cd FaceTrack
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the database:**

      * Set up a PostgreSQL database.
      * Update the database connection string in your configuration file (`config.py` or similar).

5.  **Run the application:**

    ```bash
    python app.py
    ```

    The application should now be running at `http://127.0.0.1:5000`.

-----

### Contact ✉️

For any questions or suggestions, please feel free to open an issue or contact the repository owner.

**Morahar** - [https://github.com/Morahar5462](https://www.google.com/search?q=https://github.com/Morahar5462)
