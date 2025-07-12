from app import db
from flask_login import UserMixin
from datetime import datetime
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'teacher' or 'student'
    face_encoding = db.Column(db.Text, nullable=True)  # Store face encoding as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    courses_teaching = db.relationship('Course', backref='teacher', lazy=True, 
                                      foreign_keys='Course.teacher_id')
    enrollments = db.relationship('Enrollment', backref='student', lazy=True,
                                 foreign_keys='Enrollment.student_id')
    
    def has_face_registered(self):
        return self.face_encoding is not None
    
    def set_face_encoding(self, encoding):
        """Save face encoding as JSON string"""
        if encoding is not None:
            # Handle both numpy arrays (with tolist()) and regular Python lists
            if hasattr(encoding, 'tolist'):
                self.face_encoding = json.dumps(encoding.tolist())
            else:
                self.face_encoding = json.dumps(encoding)
        else:
            self.face_encoding = None
            
    def get_face_encoding(self):
        """Get face encoding as numpy array"""
        if self.face_encoding:
            import numpy as np
            return np.array(json.loads(self.face_encoding))
        return None

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True,
                                cascade='all, delete-orphan')
    attendance_sessions = db.relationship('AttendanceSession', backref='course', lazy=True,
                                        cascade='all, delete-orphan')
    
    def get_attendance_percentage(self, student_id):
        """Calculate attendance percentage for a student in this course"""
        from sqlalchemy import func
        
        # Count all sessions for this course
        total_sessions = AttendanceSession.query.filter_by(course_id=self.id).count()
        
        if total_sessions == 0:
            return 0
            
        # Count sessions where student was present
        present_count = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceSession.course_id == self.id,
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == 'present'
        ).count()
        
        return round((present_count / total_sessions) * 100, 2)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define a unique constraint to prevent duplicate enrollment
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id'),)

class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    records = db.relationship('AttendanceRecord', backref='session', lazy=True,
                            cascade='all, delete-orphan')
    
    # Define a unique constraint for course_id and date to prevent duplicate sessions
    __table_args__ = (db.UniqueConstraint('course_id', 'date'),)

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='absent')  # 'present', 'absent', 'late'
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    marked_by = db.Column(db.String(20), default='system')  # 'system', 'manual'
    
    # Define a unique constraint to prevent duplicate records
    __table_args__ = (db.UniqueConstraint('session_id', 'student_id'),)
    
    # Relationship with student
    student = db.relationship('User', foreign_keys=[student_id], backref='attendance_records')
