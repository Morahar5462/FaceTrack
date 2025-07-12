import os
import json
import logging
import csv
from datetime import datetime, date, time
from functools import wraps
from io import StringIO

from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

from app import app, db
from models import User, Course, Enrollment, AttendanceSession, AttendanceRecord
from face_utils import extract_face_encoding, compare_faces, is_duplicate_face

logger = logging.getLogger(__name__)

# Custom decorators for role-based access
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Access restricted. Teacher privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access restricted. Student privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Basic Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            
            if user.role == 'teacher':
                return redirect(next_page or url_for('teacher_dashboard'))
            else:
                return redirect(next_page or url_for('student_dashboard'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        # Validate form data
        if not all([username, email, password, confirm_password, role]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if role not in ['teacher', 'student']:
            flash('Invalid role selected', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Teacher Routes
@app.route('/teacher/dashboard')
@login_required
@teacher_required
def teacher_dashboard():
    # Get courses taught by this teacher
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # Calculate statistics
    total_courses = len(courses)
    total_students = 0
    recent_sessions = []
    
    for course in courses:
        # Count enrolled students
        enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
        total_students += enrollment_count
        
        # Get recent attendance sessions
        recent_course_sessions = AttendanceSession.query.filter_by(course_id=course.id).order_by(
            AttendanceSession.date.desc()).limit(3).all()
        
        for session in recent_course_sessions:
            # Calculate attendance rate for this session
            total_records = AttendanceRecord.query.filter_by(session_id=session.id).count()
            present_records = AttendanceRecord.query.filter_by(
                session_id=session.id, status='present').count()
            
            attendance_rate = 0
            if total_records > 0:
                attendance_rate = (present_records / total_records) * 100
            
            recent_sessions.append({
                'course_name': course.name,
                'date': session.date,
                'attendance_rate': round(attendance_rate, 1)
            })
    
    # Sort recent sessions by date (newest first)
    recent_sessions.sort(key=lambda x: x['date'], reverse=True)
    recent_sessions = recent_sessions[:5]  # Limit to 5 most recent
    
    return render_template('teacher/dashboard.html', 
                          courses=courses,
                          total_courses=total_courses,
                          total_students=total_students,
                          recent_sessions=recent_sessions,
                          now=datetime.now())

@app.route('/teacher/courses', methods=['GET', 'POST'])
@login_required
@teacher_required
def course_management():
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        
        # Validate form data
        if not all([name, code]):
            flash('Course name and code are required', 'danger')
        else:
            # Check if course code already exists
            existing_course = Course.query.filter_by(code=code).first()
            if existing_course:
                flash('Course code already exists', 'danger')
            else:
                # Create new course
                new_course = Course(
                    name=name,
                    code=code,
                    description=description,
                    teacher_id=current_user.id
                )
                
                db.session.add(new_course)
                db.session.commit()
                
                flash('Course created successfully!', 'success')
                return redirect(url_for('course_management'))
    
    # Get all courses taught by this teacher
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    
    # Get enrollment counts for each course
    course_data = []
    for course in courses:
        enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
        session_count = AttendanceSession.query.filter_by(course_id=course.id).count()
        
        course_data.append({
            'course': course,
            'enrollment_count': enrollment_count,
            'session_count': session_count
        })
    
    return render_template('teacher/course_management.html', course_data=course_data)

@app.route('/teacher/course/<int:course_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to delete this course', 'danger')
        return redirect(url_for('course_management'))
    
    # Delete the course
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully', 'success')
    return redirect(url_for('course_management'))

@app.route('/teacher/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to edit this course', 'danger')
        return redirect(url_for('course_management'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description')
        
        # Validate form data
        if not all([name, code]):
            flash('Course name and code are required', 'danger')
        else:
            # Check if updated code already exists for another course
            existing_course = Course.query.filter(
                Course.code == code, 
                Course.id != course_id
            ).first()
            
            if existing_course:
                flash('Course code already exists', 'danger')
            else:
                # Update course
                course.name = name
                course.code = code
                course.description = description
                
                db.session.commit()
                
                flash('Course updated successfully!', 'success')
                return redirect(url_for('course_management'))
    
    return render_template('teacher/course_management.html', 
                          edit_course=course,
                          course_data=[])

@app.route('/teacher/course/<int:course_id>/students')
@login_required
@teacher_required
def course_students(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to view this course', 'danger')
        return redirect(url_for('course_management'))
    
    # Get all enrolled students
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    
    students_data = []
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        
        # Calculate attendance percentage
        attendance_percentage = course.get_attendance_percentage(student.id)
        
        students_data.append({
            'student': student,
            'enrollment_date': enrollment.enrolled_at,
            'attendance_percentage': attendance_percentage,
            'face_registered': student.has_face_registered()
        })
    
    return render_template('teacher/students.html', 
                          course=course,
                          students_data=students_data)

@app.route('/teacher/course/<int:course_id>/student/<int:student_id>/remove', methods=['POST'])
@login_required
@teacher_required
def remove_student(course_id, student_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to modify this course', 'danger')
        return redirect(url_for('course_management'))
    
    # Find the enrollment
    enrollment = Enrollment.query.filter_by(
        course_id=course_id,
        student_id=student_id
    ).first_or_404()
    
    # Delete the enrollment
    db.session.delete(enrollment)
    db.session.commit()
    
    flash('Student removed from course successfully', 'success')
    return redirect(url_for('course_students', course_id=course_id))

@app.route('/teacher/course/<int:course_id>/attendance')
@login_required
@teacher_required
def course_attendance(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to view this course', 'danger')
        return redirect(url_for('course_management'))
    
    # Get all attendance sessions
    sessions = AttendanceSession.query.filter_by(course_id=course_id).order_by(
        AttendanceSession.date.desc()).all()
    
    # Get attendance statistics for each session
    sessions_data = []
    for session in sessions:
        total_students = Enrollment.query.filter_by(course_id=course_id).count()
        present_count = AttendanceRecord.query.filter_by(
            session_id=session.id, 
            status='present'
        ).count()
        
        attendance_rate = 0
        if total_students > 0:
            attendance_rate = (present_count / total_students) * 100
        
        sessions_data.append({
            'session': session,
            'present_count': present_count,
            'total_students': total_students,
            'attendance_rate': round(attendance_rate, 1)
        })
    
    return render_template('teacher/attendance.html', 
                          course=course,
                          sessions_data=sessions_data)

@app.route('/teacher/course/<int:course_id>/new-session', methods=['POST'])
@login_required
@teacher_required
def new_attendance_session(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to modify this course', 'danger')
        return redirect(url_for('course_management'))
    
    session_date = request.form.get('date')
    
    try:
        # Parse date
        session_date = datetime.strptime(session_date, '%Y-%m-%d').date()
        
        # Check if a session already exists for this date
        existing_session = AttendanceSession.query.filter_by(
            course_id=course_id,
            date=session_date
        ).first()
        
        if existing_session:
            flash('An attendance session already exists for this date', 'warning')
            return redirect(url_for('course_attendance', course_id=course_id))
        
        # Create new session
        new_session = AttendanceSession(
            course_id=course_id,
            date=session_date,
            start_time=datetime.now().time()
        )
        
        db.session.add(new_session)
        db.session.commit()
        
        # Initialize attendance records for all enrolled students (as absent by default)
        enrollments = Enrollment.query.filter_by(course_id=course_id).all()
        for enrollment in enrollments:
            record = AttendanceRecord(
                session_id=new_session.id,
                student_id=enrollment.student_id,
                status='absent'
            )
            db.session.add(record)
        
        db.session.commit()
        
        flash('New attendance session created', 'success')
        return redirect(url_for('take_attendance', session_id=new_session.id))
        
    except Exception as e:
        logger.error(f"Error creating attendance session: {str(e)}")
        flash('Error creating attendance session', 'danger')
        return redirect(url_for('course_attendance', course_id=course_id))

@app.route('/teacher/session/<int:session_id>/take-attendance')
@login_required
@teacher_required
def take_attendance(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    course = Course.query.get_or_404(session.course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to access this session', 'danger')
        return redirect(url_for('course_management'))
    
    # Get all enrolled students
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    
    # Get existing attendance records
    records = AttendanceRecord.query.filter_by(session_id=session_id).all()
    records_dict = {record.student_id: record for record in records}
    
    # Prepare students data
    students_data = []
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        record = records_dict.get(student.id)
        
        students_data.append({
            'student': student,
            'record': record,
            'has_face': student.has_face_registered()
        })
    
    return render_template('teacher/attendance.html', 
                          course=course,
                          session=session,
                          students_data=students_data,
                          take_attendance=True)

@app.route('/teacher/session/<int:session_id>/mark-attendance', methods=['POST'])
@login_required
@teacher_required
def mark_attendance(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    course = Course.query.get_or_404(session.course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    student_id = data.get('student_id')
    status = data.get('status')
    
    if not student_id or status not in ['present', 'absent', 'late']:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    # Verify student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        course_id=course.id,
        student_id=student_id
    ).first()
    
    if not enrollment:
        return jsonify({'success': False, 'message': 'Student not enrolled in this course'}), 400
    
    # Update or create attendance record
    record = AttendanceRecord.query.filter_by(
        session_id=session_id,
        student_id=student_id
    ).first()
    
    if record:
        record.status = status
        record.marked_by = 'manual'
        record.marked_at = datetime.now()
    else:
        record = AttendanceRecord(
            session_id=session_id,
            student_id=student_id,
            status=status,
            marked_by='manual'
        )
        db.session.add(record)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Attendance marked as {status}'})

@app.route('/teacher/session/<int:session_id>/face-recognition', methods=['POST'])
@login_required
@teacher_required
def face_recognition_attendance(session_id):
    session = AttendanceSession.query.get_or_404(session_id)
    course = Course.query.get_or_404(session.course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'success': False, 'message': 'No image data provided'}), 400
    
    # Extract face encoding from image
    face_encoding = extract_face_encoding(image_data)
    
    if face_encoding is None:
        return jsonify({'success': False, 'message': 'No face detected in the image'}), 400
    
    # Get all enrolled students in this course
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    
    matched_student = None
    
    # Compare with each student's face encoding
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        
        if not student.has_face_registered():
            continue
        
        student_encoding = student.get_face_encoding()
        
        if compare_faces(student_encoding, face_encoding):
            matched_student = student
            break
    
    if not matched_student:
        return jsonify({'success': False, 'message': 'No matching student found'}), 404
    
    # Mark attendance for matched student
    record = AttendanceRecord.query.filter_by(
        session_id=session_id,
        student_id=matched_student.id
    ).first()
    
    if record:
        record.status = 'present'
        record.marked_by = 'system'
        record.marked_at = datetime.now()
    else:
        record = AttendanceRecord(
            session_id=session_id,
            student_id=matched_student.id,
            status='present',
            marked_by='system'
        )
        db.session.add(record)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Student recognized and marked present',
        'student': {
            'id': matched_student.id,
            'name': matched_student.username
        }
    })

@app.route('/teacher/course/<int:course_id>/reports')
@login_required
@teacher_required
def course_reports(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to view this course', 'danger')
        return redirect(url_for('course_management'))
    
    # Get all enrolled students
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    
    # Get all attendance sessions
    sessions = AttendanceSession.query.filter_by(course_id=course_id).order_by(
        AttendanceSession.date).all()
    
    # Prepare data for report
    students_data = []
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        
        # Get attendance records for this student
        records = AttendanceRecord.query.join(AttendanceSession).filter(
            AttendanceSession.course_id == course_id,
            AttendanceRecord.student_id == student.id
        ).all()
        
        # Count present, absent, late
        present_count = sum(1 for r in records if r.status == 'present')
        absent_count = sum(1 for r in records if r.status == 'absent')
        late_count = sum(1 for r in records if r.status == 'late')
        
        # Calculate attendance percentage
        total_sessions = len(sessions)
        attendance_percentage = 0
        if total_sessions > 0:
            attendance_percentage = (present_count / total_sessions) * 100
        
        students_data.append({
            'student': student,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'total_sessions': total_sessions,
            'attendance_percentage': round(attendance_percentage, 1)
        })
    
    # Sort by attendance percentage (descending)
    students_data.sort(key=lambda x: x['attendance_percentage'], reverse=True)
    
    return render_template('teacher/reports.html', 
                          course=course,
                          students_data=students_data,
                          sessions=sessions)

@app.route('/teacher/course/<int:course_id>/export-report')
@login_required
@teacher_required
def export_attendance_report(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Ensure the teacher owns this course
    if course.teacher_id != current_user.id:
        flash('You are not authorized to access this course', 'danger')
        return redirect(url_for('course_management'))
    
    # Get all enrolled students
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    
    # Get all attendance sessions
    sessions = AttendanceSession.query.filter_by(course_id=course_id).order_by(
        AttendanceSession.date).all()
    
    # Create CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header row
    header = ['Student ID', 'Student Name', 'Email']
    for session in sessions:
        header.append(f'Session {session.date}')
    header.extend(['Present', 'Absent', 'Late', 'Attendance %'])
    
    writer.writerow(header)
    
    # Write data rows
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        row = [student.id, student.username, student.email]
        
        # Get attendance status for each session
        present_count = 0
        absent_count = 0
        late_count = 0
        
        for session in sessions:
            record = AttendanceRecord.query.filter_by(
                session_id=session.id,
                student_id=student.id
            ).first()
            
            status = 'N/A'
            if record:
                status = record.status
                if status == 'present':
                    present_count += 1
                elif status == 'absent':
                    absent_count += 1
                elif status == 'late':
                    late_count += 1
            
            row.append(status)
        
        # Calculate attendance percentage
        total_sessions = len(sessions)
        attendance_percentage = 0
        if total_sessions > 0:
            attendance_percentage = (present_count / total_sessions) * 100
        
        row.extend([present_count, absent_count, late_count, f"{round(attendance_percentage, 1)}%"])
        writer.writerow(row)
    
    # Prepare response
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"{course.code}_attendance_report.csv",
        mimetype='text/csv'
    )

# Student Routes
@app.route('/student/dashboard')
@login_required
@student_required
def student_dashboard():
    # Get courses enrolled by this student
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    
    # Calculate statistics
    total_courses = len(enrollments)
    face_registered = current_user.has_face_registered()
    
    courses_data = []
    overall_attendance = 0
    
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        
        # Calculate attendance percentage
        attendance_percentage = course.get_attendance_percentage(current_user.id)
        
        courses_data.append({
            'course': course,
            'enrolled_at': enrollment.enrolled_at,
            'attendance_percentage': attendance_percentage
        })
        
        # Add to overall attendance
        overall_attendance += attendance_percentage
    
    # Calculate average attendance
    average_attendance = 0
    if total_courses > 0:
        average_attendance = overall_attendance / total_courses
    
    return render_template('student/dashboard.html', 
                          courses_data=courses_data,
                          total_courses=total_courses,
                          face_registered=face_registered,
                          average_attendance=round(average_attendance, 1),
                          now=datetime.now())

@app.route('/student/enroll', methods=['GET', 'POST'])
@login_required
@student_required
def enroll_courses():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        
        if not course_id:
            flash('Please select a course', 'danger')
        else:
            # Check if already enrolled
            existing_enrollment = Enrollment.query.filter_by(
                course_id=course_id,
                student_id=current_user.id
            ).first()
            
            if existing_enrollment:
                flash('You are already enrolled in this course', 'warning')
            else:
                # Create new enrollment
                new_enrollment = Enrollment(
                    course_id=course_id,
                    student_id=current_user.id
                )
                
                db.session.add(new_enrollment)
                db.session.commit()
                
                flash('Successfully enrolled in the course!', 'success')
                return redirect(url_for('student_dashboard'))
    
    # Get courses I'm enrolled in
    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    
    # Get all available courses
    available_courses = Course.query.filter(~Course.id.in_(enrolled_course_ids) if enrolled_course_ids else True).all()
    
    return render_template('student/enrollment.html', available_courses=available_courses)

@app.route('/student/face-registration', methods=['GET', 'POST'])
@login_required
@student_required
def face_registration():
    if request.method == 'POST':
        image_data = request.form.get('image_data')
        
        if not image_data:
            flash('No image data provided', 'danger')
        else:
            # Extract face encoding
            face_encoding = extract_face_encoding(image_data)
            
            if face_encoding is None:
                flash('No face detected in the image. Please try again.', 'danger')
            else:
                # Check for duplicate faces
                students_with_faces = User.query.filter(User.face_encoding != None).all()
                existing_encodings = [s.get_face_encoding() for s in students_with_faces if s.id != current_user.id]
                
                if is_duplicate_face(face_encoding, existing_encodings):
                    flash('This face has already been registered by another user', 'danger')
                else:
                    # Save face encoding
                    current_user.set_face_encoding(face_encoding)
                    db.session.commit()
                    
                    flash('Face registered successfully!', 'success')
                    return redirect(url_for('student_dashboard'))
    
    face_registered = current_user.has_face_registered()
    
    return render_template('student/face_registration.html', face_registered=face_registered)

@app.route('/student/update-face', methods=['POST'])
@login_required
@student_required
def update_face():
    # Delete existing face encoding
    current_user.face_encoding = None
    db.session.commit()
    
    flash('Face registration removed. You can register a new face now.', 'info')
    return redirect(url_for('face_registration'))

@app.route('/student/attendance')
@login_required
@student_required
def student_attendance():
    # Get courses enrolled by this student
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    
    attendance_data = []
    
    for enrollment in enrollments:
        course = Course.query.get(enrollment.course_id)
        
        # Get attendance sessions for this course
        sessions = AttendanceSession.query.filter_by(course_id=course.id).order_by(
            AttendanceSession.date.desc()).all()
        
        sessions_data = []
        for session in sessions:
            # Get attendance record for this session
            record = AttendanceRecord.query.filter_by(
                session_id=session.id,
                student_id=current_user.id
            ).first()
            
            status = 'N/A'
            if record:
                status = record.status
            
            sessions_data.append({
                'date': session.date,
                'status': status
            })
        
        # Calculate attendance percentage
        attendance_percentage = course.get_attendance_percentage(current_user.id)
        
        attendance_data.append({
            'course': course,
            'sessions': sessions_data,
            'attendance_percentage': attendance_percentage
        })
    
    return render_template('student/attendance.html', attendance_data=attendance_data)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
