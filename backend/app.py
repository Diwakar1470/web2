import os
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
import bcrypt
import secrets

load_dotenv()

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(APP_DIR)
WEB_DIR = os.path.join(PARENT_DIR, 'web')

app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Secret key for sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Database Configuration from environment variables
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', '1234')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'school_db')

database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Password Hashing Utilities
def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_temp_password(prefix="TEMP"):
    """Generate temporary password"""
    return f"{prefix}{secrets.token_hex(4).upper()}@123"

# RBAC Decorator
def require_role(*allowed_roles):
    """Decorator to require specific roles for endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"error": "Unauthorized - Please login"}), 401
            
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({"error": "User not found or inactive"}), 401
            
            # Get role name
            role = Role.query.get(user.role_id)
            if not role or role.name not in allowed_roles:
                return jsonify({"error": "Forbidden - Insufficient permissions"}), 403
            
            # Check profile completion for non-creator roles
            if role.name != 'CREATOR' and not user.profile_completed:
                return jsonify({"error": "Profile incomplete", "requiresProfileCompletion": True}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Database Models

# New unified user system
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    code = db.Column(db.String(50))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    employee_id = db.Column(db.String(100), unique=True)
    
    # Department/Activity assignment
    assigned_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    assigned_activity_name = db.Column(db.String(255))
    
    # Profile information
    phone = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    blood_group = db.Column(db.String(10))
    address = db.Column(db.Text)
    profile_photo = db.Column(db.String(500))
    
    # Profile completion tracking
    profile_completed = db.Column(db.Boolean, default=False)
    is_temp_password = db.Column(db.Boolean, default=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    role = db.relationship('Role', backref='users')
    department = db.relationship('Department', backref='users')
    
    def to_dict(self, include_sensitive=False):
        role = Role.query.get(self.role_id)
        department = Department.query.get(self.assigned_department_id) if self.assigned_department_id else None
        
        data = {
            'id': self.id,
            'email': self.email,
            'fullName': self.full_name,
            'employeeId': self.employee_id,
            'role': role.name if role else None,
            'roleId': self.role_id,
            'assignedDepartment': department.name if department else None,
            'assignedDepartmentId': self.assigned_department_id,
            'assignedActivity': self.assigned_activity_name,
            'phone': self.phone,
            'age': self.age,
            'gender': self.gender,
            'bloodGroup': self.blood_group,
            'address': self.address,
            'profilePhoto': self.profile_photo,
            'profileCompleted': self.profile_completed,
            'isTempPassword': self.is_temp_password,
            'isActive': self.is_active,
            'lastLogin': self.last_login.isoformat() if self.last_login else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_sensitive:
            data['passwordHash'] = self.password_hash
        
        return data

class ActivityUser(db.Model):
    """Many-to-many mapping for coordinators assigned to multiple activities"""
    __tablename__ = 'activity_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    activity_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Legacy models (keep for backward compatibility)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    # We store the calculated key (rollNo or email) to maintain the uniqueness logic
    lookup_key = db.Column(db.String, unique=True, index=True)
    department = db.Column(db.String(255))  # For HOD filtering
    profile = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        # Merge metadata with the profile data for the API response
        data = self.profile.copy() if self.profile else {}
        data['createdAt'] = self.created_at.isoformat() if self.created_at else None
        data['updatedAt'] = self.updated_at.isoformat() if self.updated_at else None
        data['department'] = self.department
        return data

class HOD(db.Model):
    __tablename__ = 'hods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    employee_id = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.employee_id,
            'dbId': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class Coordinator(db.Model):
    __tablename__ = 'coordinators'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    coordinator_id = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(255), nullable=False)  # Activity role: NCC, NSS, Sports, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'dbId': self.id,
            'name': self.name,
            'email': self.email,
            'id': self.coordinator_id,
            'role': self.role,
            'activity': self.role,  # Frontend uses 'activity' field
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(255), index=True)  # Track student
    admission_id = db.Column(db.String(100), index=True)
    student_name = db.Column(db.String(255))
    department = db.Column(db.String(255))  # Student's department for HOD approval
    activity_name = db.Column(db.String(255), index=True)  # Activity applied for
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activities.id'))  # Link to sub-activity
    status = db.Column(db.String(50), default='pending')  # pending, coordinator_approved, hod_approved, rejected
    coordinator_status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    hod_status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    rejection_reason = db.Column(db.Text)  # Why rejected
    data = db.Column(JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        result = {**self.data} if self.data else {}
        result.update({
            "id": self.id,
            "studentEmail": self.student_email,
            "admissionId": self.admission_id,
            "studentName": self.student_name,
            "department": self.department,
            "activityName": self.activity_name,
            "subActivityId": self.sub_activity_id,
            "status": self.status,
            "coordinatorStatus": self.coordinator_status,
            "hodStatus": self.hod_status,
            "rejectionReason": self.rejection_reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        })
        return result

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    data = db.Column(JSON)  # Stores students, events, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'data': self.data or {},
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class SubActivity(db.Model):
    __tablename__ = 'sub_activities'
    id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(255), nullable=False)
    sub_activity_name = db.Column(db.String(255), nullable=False)
    coordinator_email = db.Column(db.String(255))  # Track who created this sub-activity
    total_slots = db.Column(db.Integer, default=0)  # Total available slots
    filled_slots = db.Column(db.Integer, default=0)  # Number of filled slots
    is_active = db.Column(db.Boolean, default=True)  # Whether accepting applications
    data = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        available_slots = self.total_slots - self.filled_slots
        is_full = available_slots <= 0
        return {
            'id': self.id,
            'activityName': self.activity_name,
            'subActivityName': self.sub_activity_name,
            'coordinatorEmail': self.coordinator_email,
            'totalSlots': self.total_slots,
            'filledSlots': self.filled_slots,
            'availableSlots': available_slots,
            'isFull': is_full,
            'isActive': self.is_active and not is_full,  # Active only if not full
            'data': self.data or {},
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class CourseRegistration(db.Model):
    __tablename__ = 'course_registrations'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(255))
    admission_id = db.Column(db.String(255))
    course = db.Column(db.String(255))
    department = db.Column(db.String(255))  # Student's department for HOD filtering
    activity_name = db.Column(db.String(255))
    activity_category = db.Column(db.String(255))
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activities.id'))  # Link to sub-activity
    status = db.Column(db.String(100), default='Pending Coordinator')
    data = db.Column(JSON)  # Store all registration data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        result = self.data.copy() if self.data else {}
        result.update({
            'id': self.id,
            'studentName': self.student_name,
            'admissionId': self.admission_id,
            'course': self.course,
            'department': self.department,
            'activityName': self.activity_name,
            'activityCategory': self.activity_category,
            'subActivityId': self.sub_activity_id,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastUpdated': self.last_updated.isoformat() if self.last_updated else None
        })
        return result

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(255), nullable=False)
    activity_name = db.Column(db.String(255), nullable=False)
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activities.id'))
    coordinator_email = db.Column(db.String(255))  # Event creator
    event_date = db.Column(db.DateTime, nullable=False)
    event_time = db.Column(db.String(50))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    assigned_students = db.Column(JSON)  # List of student admission IDs assigned to this event
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'eventName': self.event_name,
            'activityName': self.activity_name,
            'subActivityId': self.sub_activity_id,
            'coordinatorEmail': self.coordinator_email,
            'eventDate': self.event_date.isoformat() if self.event_date else None,
            'eventTime': self.event_time,
            'location': self.location,
            'description': self.description,
            'assignedStudents': self.assigned_students or [],
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_admission_id = db.Column(db.String(255), nullable=False, index=True)
    student_name = db.Column(db.String(255))
    activity_name = db.Column(db.String(255), nullable=False)
    sub_activity_id = db.Column(db.Integer, db.ForeignKey('sub_activities.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))  # Optional: for event attendance
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    attendance_type = db.Column(db.String(50), default='daily')  # 'daily' or 'event'
    status = db.Column(db.String(20), default='present')  # 'present', 'absent', 'late'
    coordinator_email = db.Column(db.String(255))  # Who marked attendance
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'studentAdmissionId': self.student_admission_id,
            'studentName': self.student_name,
            'activityName': self.activity_name,
            'subActivityId': self.sub_activity_id,
            'eventId': self.event_id,
            'attendanceDate': self.attendance_date.isoformat() if self.attendance_date else None,
            'attendanceType': self.attendance_type,
            'status': self.status,
            'coordinatorEmail': self.coordinator_email,
            'remarks': self.remarks,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(WEB_DIR, 'index.html')


@app.route('/<path:filename>', methods=['GET'])
def serve_static(filename):
    return send_from_directory(WEB_DIR, filename)


@app.route('/api/health', methods=['GET'])
def health():
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "error", "details": str(e)}), 500


# Authentication Endpoints
@app.route('/api/auth/student', methods=['POST'])
def auth_student():
    """Student authentication endpoint - fetch from unified users table"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    admission_id = payload.get('admissionId', '').strip()
    
    if not email or not admission_id:
        return jsonify({"error": "Email and admission ID are required"}), 400
    
    # Find student in new users table by role and verify both email and admission ID
    user = User.query.filter(
        User.email.ilike(email),
        User.employee_id == admission_id,
        User.is_active == True
    ).first()
    
    if user:
        role = Role.query.get(user.role_id)
        if role and role.name == 'STUDENT':
            return jsonify({
                "success": True,
                "student": {
                    "name": user.full_name,
                    "email": user.email,
                    "admissionId": user.employee_id,
                    "role": role.name
                }
            })
    
    return jsonify({"error": "Student not found"}), 404


@app.route('/api/auth/coordinator', methods=['POST'])
def auth_coordinator():
    """Coordinator authentication endpoint - fetch from unified users table"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    coordinator_id = payload.get('id', '').strip()
    
    if not email or not coordinator_id:
        return jsonify({"error": "Email and ID are required"}), 400
    
    # Find coordinator in new users table by role
    user = User.query.filter(
        User.email.ilike(email),
        User.employee_id == coordinator_id,
        User.is_active == True
    ).first()
    
    if user:
        role = Role.query.get(user.role_id)
        if role and role.name == 'COORDINATOR':
            return jsonify({
                "success": True,
                "coordinator": {
                    "name": user.full_name,
                    "email": user.email,
                    "id": user.employee_id,
                    "role": role.name,
                    "activity": user.assigned_activity_name or 'NCC'
                }
            })
    
    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/auth/hod', methods=['POST'])
def auth_hod():
    """HOD authentication endpoint - fetch from unified users table"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    employee_id = payload.get('id', '').strip()
    
    if not email or not employee_id:
        return jsonify({"error": "Email and employee ID are required"}), 400
    
    # Find HOD in new users table by role
    user = User.query.filter(
        User.email.ilike(email),
        User.employee_id == employee_id,
        User.is_active == True
    ).first()
    
    if user:
        role = Role.query.get(user.role_id)
        if role and role.name == 'HOD':
            return jsonify({
                "success": True,
                "hod": {
                    "name": user.full_name,
                    "email": user.email,
                    "id": user.employee_id,
                    "role": role.name
                }
            })
    
    return jsonify({"error": "Invalid credentials"}), 401


# NEW UNIFIED USER AUTHENTICATION ENDPOINTS

@app.route('/api/auth/login', methods=['POST'])
def unified_login():
    """Unified login endpoint for all users (Creator, HOD, Coordinator)"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip()
    password = payload.get('password', '').strip()
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user by email - case insensitive search
    users = User.query.filter(User.is_active == True).all()
    user = None
    for u in users:
        if u.email.lower() == email.lower():
            user = u
            break
    
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Verify password
    if not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create session
    session.permanent = True
    session['user_id'] = user.id
    session['role'] = Role.query.get(user.role_id).name if user.role_id else None
    
    return jsonify({
        "success": True,
        "user": user.to_dict(),
        "requiresProfileCompletion": not user.profile_completed and session.get('role') != 'CREATOR',
        "isTempPassword": user.is_temp_password
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user info"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(user_id)
    if not user or not user.is_active:
        session.clear()
        return jsonify({"error": "User not found"}), 401
    
    return jsonify({
        "success": True,
        "user": user.to_dict()
    })


@app.route('/api/profile/update', methods=['PUT'])
def update_profile():
    """Update user profile (for first-time login completion)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    payload = request.get_json(silent=True) or {}
    
    # Update profile fields
    if 'phone' in payload:
        user.phone = payload['phone'].strip()
    if 'age' in payload:
        user.age = int(payload['age'])
    if 'gender' in payload:
        user.gender = payload['gender'].strip()
    if 'bloodGroup' in payload:
        user.blood_group = payload['bloodGroup'].strip()
    if 'address' in payload:
        user.address = payload['address'].strip()
    if 'profilePhoto' in payload:
        user.profile_photo = payload['profilePhoto'].strip()
    
    # Update password if provided
    if 'newPassword' in payload and payload['newPassword']:
        new_password = payload['newPassword'].strip()
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        user.password_hash = hash_password(new_password)
        user.is_temp_password = False
    
    # Mark profile as completed
    user.profile_completed = True
    user.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500


@app.route('/api/creator/create-hod', methods=['POST'])
@require_role('CREATOR')
def create_hod_user():
    """Creator endpoint to create HOD account"""
    payload = request.get_json(silent=True) or {}
    
    email = payload.get('email', '').strip().lower()
    full_name = payload.get('fullName', '').strip()
    employee_id = payload.get('employeeId', '').strip()
    department_id = payload.get('departmentId')
    temp_password = payload.get('tempPassword', '').strip()
    
    if not all([email, full_name, employee_id, department_id]):
        return jsonify({"error": "All fields are required (email, fullName, employeeId, departmentId)"}), 400
    
    # Check if user already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "User with this email already exists"}), 409
    
    # Check if department exists
    department = Department.query.get(department_id)
    if not department:
        return jsonify({"error": "Invalid department"}), 400
    
    # Check one HOD per department
    existing_hod = User.query.filter_by(assigned_department_id=department_id).join(Role).filter(Role.name == 'HOD').first()
    if existing_hod:
        return jsonify({"error": f"Department {department.name} already has an HOD assigned"}), 409
    
    # Get HOD role
    hod_role = Role.query.filter_by(name='HOD').first()
    if not hod_role:
        return jsonify({"error": "HOD role not found in database"}), 500
    
    # Generate or use provided temp password
    if not temp_password:
        temp_password = generate_temp_password(f"HOD{employee_id}")
    
    password_hash = hash_password(temp_password)
    
    # Create user
    new_user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role_id=hod_role.id,
        employee_id=employee_id,
        assigned_department_id=department_id,
        profile_completed=False,
        is_temp_password=True
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Also create in legacy HOD table for backward compatibility
        legacy_hod = HOD(
            name=full_name,
            email=email,
            employee_id=employee_id,
            department=department.name
        )
        db.session.add(legacy_hod)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "HOD created successfully",
            "user": new_user.to_dict(),
            "tempPassword": temp_password
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create HOD: {str(e)}"}), 500


@app.route('/api/creator/create-faculty', methods=['POST'])
@require_role('CREATOR')
def create_faculty_coordinator():
    """Creator endpoint to create Faculty Coordinator account"""
    payload = request.get_json(silent=True) or {}
    
    email = payload.get('email', '').strip().lower()
    full_name = payload.get('fullName', '').strip()
    employee_id = payload.get('employeeId', '').strip()
    activity_name = payload.get('activityName', '').strip()
    temp_password = payload.get('tempPassword', '').strip()
    
    if not all([email, full_name, employee_id, activity_name]):
        return jsonify({"error": "All fields are required (email, fullName, employeeId, activityName)"}), 400
    
    # Check if user already exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "User with this email already exists"}), 409
    
    # Get Faculty Coordinator role
    coord_role = Role.query.filter_by(name='FACULTY_COORDINATOR').first()
    if not coord_role:
        return jsonify({"error": "FACULTY_COORDINATOR role not found in database"}), 500
    
    # Generate or use provided temp password
    if not temp_password:
        temp_password = generate_temp_password(f"COORD{employee_id}")
    
    password_hash = hash_password(temp_password)
    
    # Create user
    new_user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role_id=coord_role.id,
        employee_id=employee_id,
        assigned_activity_name=activity_name,
        profile_completed=False,
        is_temp_password=True
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Also create in legacy Coordinator table for backward compatibility
        legacy_coord = Coordinator(
            name=full_name,
            email=email,
            coordinator_id=employee_id,
            role=activity_name
        )
        db.session.add(legacy_coord)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Faculty Coordinator created successfully",
            "user": new_user.to_dict(),
            "tempPassword": temp_password
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create coordinator: {str(e)}"}), 500


# HELPER ENDPOINTS

@app.route('/api/roles', methods=['GET'])
def get_roles():
    """Get all roles"""
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles])


@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get all departments"""
    departments = Department.query.all()
    return jsonify([dept.to_dict() for dept in departments])


@app.route('/api/departments/<int:dept_id>/classes', methods=['GET'])
def get_department_classes(dept_id):
    """Get all classes for a specific department"""
    try:
        dept = Department.query.get(dept_id)
        if not dept:
            return jsonify({"error": "Department not found"}), 404
        
        # Create mapping of department codes to activity department names
        # Removed CSE and ECE - now using AIDT (AI and Data Science) only
        dept_code_map = {
            'BA': 'B.A.',
            'BCom': 'B.Com.',
            'BBA': 'B.B.A.',
            'BCA': 'B.C.A.',
            'BSc': 'B.Sc.',
            'AIDT': 'AI and Data Science'
        }
        
        # Get the activity department name for this code
        activity_dept_name = dept_code_map.get(dept.code)
        
        # Get activities related to this department
        activities = Activity.query.all()
        department_classes = []
        
        for activity in activities:
            activity_dept = activity.data.get('department') if activity.data else None
            # Match by either code or activity department name
            if activity_dept == activity_dept_name or activity_dept == dept.code:
                department_classes.append({
                    'id': activity.id,
                    'name': activity.name,
                    'description': activity.data.get('description', ''),
                    'programName': activity.data.get('programName', ''),
                    'programCode': activity.data.get('programCode', ''),
                    'batch': activity.data.get('batch', ''),
                    'status': activity.data.get('status', 'Running')
                })
        
        return jsonify({
            'department': dept.to_dict(),
            'classes': department_classes,
            'total': len(department_classes)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/departments-with-classes', methods=['GET'])
def get_all_departments_with_classes():
    """Get all departments with their classes in a single response"""
    try:
        # Create mapping of department codes to activity department names
        # Removed CSE and ECE - now using AIDT (AI and Data Science) only
        dept_code_map = {
            'BA': 'B.A.',
            'BCom': 'B.Com.',
            'BBA': 'B.B.A.',
            'BCA': 'B.C.A.',
            'BSc': 'B.Sc.',
            'AIDT': 'AI and Data Science'
        }
        
        departments = Department.query.all()
        result = []
        
        for dept in departments:
            # Get the activity department name for this code
            activity_dept_name = dept_code_map.get(dept.code)
            
            # Get activities related to this department
            activities = Activity.query.all()
            classes = []
            
            for activity in activities:
                activity_dept = activity.data.get('department') if activity.data else None
                # Match by either code or activity department name
                if activity_dept == activity_dept_name or activity_dept == dept.code:
                    classes.append({
                        'id': activity.id,
                        'name': activity.name,
                        'description': activity.data.get('description', ''),
                        'programName': activity.data.get('programName', ''),
                        'programCode': activity.data.get('programCode', ''),
                        'batch': activity.data.get('batch', ''),
                        'status': activity.data.get('status', 'Running')
                    })
            
            result.append({
                'department': dept.to_dict(),
                'classes': classes,
                'totalClasses': len(classes)
            })
        
        return jsonify({
            'data': result,
            'totalDepartments': len(result),
            'totalClasses': sum(d['totalClasses'] for d in result)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/classes', methods=['GET'])
def get_all_classes():
    """Get all classes with their details"""
    try:
        activities = Activity.query.all()
        classes = []
        
        for activity in activities:
            classes.append({
                'id': activity.id,
                'name': activity.name,
                'description': activity.data.get('description', '') if activity.data else '',
                'programName': activity.data.get('programName', '') if activity.data else '',
                'programCode': activity.data.get('programCode', '') if activity.data else '',
                'department': activity.data.get('department', '') if activity.data else '',
                'batch': activity.data.get('batch', '') if activity.data else '',
                'status': activity.data.get('status', 'Running') if activity.data else 'Running'
            })
        
        return jsonify({
            'data': classes,
            'total': len(classes)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/students', methods=['POST'])
def register_student():
    """Student registration endpoint - saves student to database"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    admission_id = payload.get('admissionId', '').strip()
    student_name = payload.get('studentName', '').strip()
    department = payload.get('department', '').strip()
    
    if not email or not admission_id or not student_name:
        return jsonify({"error": "Email, admission ID, and name are required"}), 400
    
    # Generate lookup key (same logic as import)
    key = email  # Use email as primary lookup key
    
    # Check if student already exists
    existing_student = Student.query.filter_by(lookup_key=key).first()
    
    if existing_student:
        return jsonify({"error": "Student already registered with this email"}), 409
    
    try:
        # Create new student with profile data
        new_student = Student(
            lookup_key=key,
            department=department,
            profile=payload  # Store all payload data
        )
        db.session.add(new_student)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Student registered successfully",
            "student": new_student.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/students/application-status', methods=['POST'])
def check_application_status():
    """Check if student can apply for activities (no pending/accepted applications)"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    admission_id = payload.get('admissionId', '').strip()
    
    if not email or not admission_id:
        return jsonify({"error": "Email and admission ID are required"}), 400
    
    # Check for existing applications that are pending or approved
    existing_app = Registration.query.filter_by(
        student_email=email,
        admission_id=admission_id
    ).filter(
        Registration.status.in_(['pending', 'coordinator_approved', 'hod_approved'])
    ).first()
    
    if existing_app:
        return jsonify({
            "canApply": False,
            "reason": f"You already have a {existing_app.status} application for {existing_app.activity_name}",
            "existingApplication": existing_app.to_dict()
        })
    else:
        return jsonify({
            "canApply": True,
            "message": "You can apply for an activity"
        })


@app.route('/api/student-profiles', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([s.to_dict() for s in students])


@app.route('/api/student-profiles/import', methods=['POST'])
def import_students():
    payload = request.get_json(silent=True) or {}
    students = payload.get('students') or []
    if not isinstance(students, list):
        return jsonify({"error": "Invalid payload: 'students' must be a list"}), 400

    added = 0
    updated = 0

    for s in students:
        # Replicate the original key generation logic
        key = (str(s.get('rollNo') or s.get('email') or '')).strip().lower()
        if not key:
            continue
        
        # Check if student exists in DB
        existing_student = Student.query.filter_by(lookup_key=key).first()
        
        if existing_student:
            # Merge new data into existing profile
            current_profile = existing_student.profile or {}
            merged_profile = {**current_profile, **s}
            existing_student.profile = merged_profile
            updated += 1
        else:
            # Create new student
            new_student = Student(lookup_key=key, profile=s)
            db.session.add(new_student)
            added += 1

    db.session.commit()
    
    total = Student.query.count()
    return jsonify({"added": added, "updated": updated, "total": total})


@app.route('/api/registrations', methods=['GET', 'POST'])
def registrations():
    if request.method == 'GET':
        # Query parameters for filtering
        status = request.args.get('status')
        activity = request.args.get('activity')
        coordinator_email = request.args.get('coordinatorEmail')
        department = request.args.get('department')
        
        query = Registration.query
        
        if status:
            query = query.filter_by(status=status)
        if activity:
            query = query.filter_by(activity_name=activity)
        if department:
            query = query.filter_by(department=department)
        
        # If coordinator_email provided, filter by their activity role
        if coordinator_email:
            coordinator = Coordinator.query.filter_by(email=coordinator_email).first()
            if coordinator:
                query = query.filter(Registration.activity_name == coordinator.role)
        
        regs = query.order_by(Registration.timestamp.desc()).all()
        return jsonify([r.to_dict() for r in regs])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        email = payload.get('email', '').strip().lower()
        admission_id = payload.get('admissionId', '').strip()
        student_name = payload.get('studentName', '').strip()
        department = payload.get('department', '').strip()
        activity_name = payload.get('activityName', '').strip()
        sub_activity_id = payload.get('subActivityId')
        
        if not email or not admission_id or not activity_name:
            return jsonify({"error": "Email, admission ID, and activity name are required"}), 400
        
        # Check if sub-activity exists and has available slots
        if sub_activity_id:
            sub_activity = SubActivity.query.get(sub_activity_id)
            if not sub_activity:
                return jsonify({"error": "Sub-activity not found"}), 404
            
            available_slots = sub_activity.total_slots - sub_activity.filled_slots
            if available_slots <= 0:
                return jsonify({"error": "This sub-activity is full. No slots available."}), 400
            
            if not sub_activity.is_active:
                return jsonify({"error": "This sub-activity is not accepting applications."}), 400
        
        # Check if student can apply (no pending/accepted applications)
        existing = Registration.query.filter_by(
            student_email=email,
            admission_id=admission_id
        ).filter(
            Registration.status.in_(['pending', 'coordinator_approved', 'hod_approved'])
        ).first()
        
        if existing:
            return jsonify({
                "error": f"You already have a {existing.status} application for {existing.activity_name}. You can only apply for one activity at a time."
            }), 409
        
        try:
            # Create new registration with status tracking
            new_reg = Registration(
                student_email=email,
                admission_id=admission_id,
                student_name=student_name,
                department=department,
                activity_name=activity_name,
                sub_activity_id=sub_activity_id,
                status='pending',
                coordinator_status='pending',
                hod_status='pending',
                data=payload
            )
            db.session.add(new_reg)
            db.session.commit()
            
            return jsonify({"success": True, "registration": new_reg.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Coordinator Management Endpoints
@app.route('/api/coordinators', methods=['GET', 'POST'])
def coordinators():
    if request.method == 'GET':
        all_coordinators = Coordinator.query.all()
        return jsonify([c.to_dict() for c in all_coordinators])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        name = payload.get('name', '').strip()
        email = payload.get('email', '').strip().lower()
        coordinator_id = payload.get('id', '').strip()
        role = payload.get('role', '').strip()
        
        # Validation
        if not all([name, email, coordinator_id, role]):
            return jsonify({"error": "All fields (name, email, id, role) are required"}), 400
        
        # Check for duplicates
        if Coordinator.query.filter_by(email=email).first():
            return jsonify({"error": f"Coordinator with email '{email}' already exists"}), 409
        
        if Coordinator.query.filter_by(coordinator_id=coordinator_id).first():
            return jsonify({"error": f"Coordinator with ID '{coordinator_id}' already exists"}), 409
        
        try:
            new_coordinator = Coordinator(name=name, email=email, coordinator_id=coordinator_id, role=role)
            db.session.add(new_coordinator)
            db.session.commit()
            return jsonify(new_coordinator.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/coordinators/<int:coordinator_id>', methods=['GET', 'PUT', 'DELETE'])
def coordinator_detail(coordinator_id):
    coordinator = Coordinator.query.get(coordinator_id)
    if not coordinator:
        return jsonify({"error": "Coordinator not found"}), 404
    
    if request.method == 'GET':
        return jsonify(coordinator.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        # Update fields if provided
        if 'name' in payload:
            coordinator.name = payload['name'].strip()
        if 'email' in payload:
            new_email = payload['email'].strip().lower()
            if new_email != coordinator.email and Coordinator.query.filter_by(email=new_email).first():
                return jsonify({"error": "Email already in use"}), 409
            coordinator.email = new_email
        if 'id' in payload:
            new_id = payload['id'].strip()
            if new_id != coordinator.coordinator_id and Coordinator.query.filter_by(coordinator_id=new_id).first():
                return jsonify({"error": "ID already in use"}), 409
            coordinator.coordinator_id = new_id
        if 'role' in payload:
            coordinator.role = payload['role'].strip()
        
        try:
            db.session.commit()
            return jsonify(coordinator.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(coordinator)
            db.session.commit()
            return jsonify({"success": True, "message": f"Coordinator '{coordinator.name}' deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# HOD Management Endpoints
@app.route('/api/hods', methods=['GET', 'POST'])
def hods():
    if request.method == 'GET':
        all_hods = HOD.query.all()
        return jsonify([h.to_dict() for h in all_hods])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        name = payload.get('name', '').strip()
        email = payload.get('email', '').strip().lower()
        employee_id = payload.get('id', '').strip()
        department = payload.get('department', '').strip()
        
        # Validation
        if not all([name, email, employee_id, department]):
            return jsonify({"error": "All fields (name, email, id, department) are required"}), 400
        
        # Check for duplicates
        if HOD.query.filter_by(email=email).first():
            return jsonify({"error": f"HOD with email '{email}' already exists"}), 409
        
        if HOD.query.filter_by(employee_id=employee_id).first():
            return jsonify({"error": f"HOD with ID '{employee_id}' already exists"}), 409
        
        try:
            new_hod = HOD(name=name, email=email, employee_id=employee_id, department=department)
            db.session.add(new_hod)
            db.session.commit()
            return jsonify(new_hod.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/hods/<int:hod_id>', methods=['GET', 'PUT', 'DELETE'])
def hod_detail(hod_id):
    hod = HOD.query.get(hod_id)
    if not hod:
        return jsonify({"error": "HOD not found"}), 404
    
    if request.method == 'GET':
        return jsonify(hod.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        # Update fields if provided
        if 'name' in payload:
            hod.name = payload['name'].strip()
        if 'email' in payload:
            new_email = payload['email'].strip().lower()
            if new_email != hod.email and HOD.query.filter_by(email=new_email).first():
                return jsonify({"error": "Email already in use"}), 409
            hod.email = new_email
        if 'id' in payload:
            new_id = payload['id'].strip()
            if new_id != hod.employee_id and HOD.query.filter_by(employee_id=new_id).first():
                return jsonify({"error": "ID already in use"}), 409
            hod.employee_id = new_id
        if 'department' in payload:
            hod.department = payload['department'].strip()
        
        try:
            db.session.commit()
            return jsonify(hod.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(hod)
            db.session.commit()
            return jsonify({"success": True, "message": f"HOD '{hod.name}' deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Activity Management Endpoints
@app.route('/api/activities', methods=['GET', 'POST'])
def activities():
    if request.method == 'GET':
        all_activities = Activity.query.all()
        return jsonify([a.to_dict() for a in all_activities])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        name = payload.get('name', '').strip()
        data = payload.get('data', {})
        
        if not name:
            return jsonify({"error": "Activity name is required"}), 400
        
        # Check for duplicates
        if Activity.query.filter_by(name=name).first():
            return jsonify({"error": f"Activity '{name}' already exists"}), 409
        
        try:
            new_activity = Activity(name=name, data=data)
            db.session.add(new_activity)
            db.session.commit()
            return jsonify(new_activity.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/activities/<int:activity_id>', methods=['GET', 'PUT', 'DELETE'])
def activity_detail(activity_id):
    activity = Activity.query.get(activity_id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404
    
    if request.method == 'GET':
        return jsonify(activity.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        if 'name' in payload:
            activity.name = payload['name'].strip()
        if 'data' in payload:
            activity.data = payload['data']
        
        try:
            db.session.commit()
            return jsonify(activity.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(activity)
            db.session.commit()
            return jsonify({"success": True, "message": f"Activity '{activity.name}' deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Sub-Activity Management Endpoints
@app.route('/api/sub-activities', methods=['GET', 'POST'])
def sub_activities():
    if request.method == 'GET':
        activity_name = request.args.get('activity')
        coordinator_email = request.args.get('coordinatorEmail')
        show_available_only = request.args.get('availableOnly', '').lower() == 'true'
        
        query = SubActivity.query
        
        if activity_name:
            query = query.filter_by(activity_name=activity_name)
        if coordinator_email:
            query = query.filter_by(coordinator_email=coordinator_email)
        if show_available_only:
            # Only show active sub-activities with available slots
            query = query.filter(SubActivity.is_active == True)
        
        subs = query.all()
        
        # Filter out full activities if showing available only
        if show_available_only:
            subs = [s for s in subs if (s.total_slots - s.filled_slots) > 0]
        
        return jsonify([s.to_dict() for s in subs])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        activity_name = payload.get('activityName', '').strip()
        sub_activity_name = payload.get('subActivityName', '').strip()
        coordinator_email = payload.get('coordinatorEmail', '').strip()
        total_slots = payload.get('totalSlots', 0)
        is_active = payload.get('isActive', True)
        data = payload.get('data', {})
        
        if not all([activity_name, sub_activity_name]):
            return jsonify({"error": "Activity name and sub-activity name are required"}), 400
        
        try:
            new_sub = SubActivity(
                activity_name=activity_name, 
                sub_activity_name=sub_activity_name, 
                coordinator_email=coordinator_email,
                total_slots=total_slots,
                filled_slots=0,
                is_active=is_active,
                data=data
            )
            db.session.add(new_sub)
            db.session.commit()
            return jsonify(new_sub.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/sub-activities/<int:sub_id>', methods=['GET', 'PUT', 'DELETE'])
def sub_activity_detail(sub_id):
    sub = SubActivity.query.get(sub_id)
    if not sub:
        return jsonify({"error": "Sub-activity not found"}), 404
    
    if request.method == 'GET':
        return jsonify(sub.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        if 'activityName' in payload:
            sub.activity_name = payload['activityName'].strip()
        if 'subActivityName' in payload:
            sub.sub_activity_name = payload['subActivityName'].strip()
        if 'totalSlots' in payload:
            sub.total_slots = payload['totalSlots']
        if 'isActive' in payload:
            sub.is_active = payload['isActive']
        if 'data' in payload:
            sub.data = payload['data']
        
        try:
            db.session.commit()
            return jsonify(sub.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(sub)
            db.session.commit()
            return jsonify({"success": True, "message": "Sub-activity deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Course Registration Endpoints
@app.route('/api/course-registrations', methods=['GET', 'POST'])
def course_registrations():
    if request.method == 'GET':
        status = request.args.get('status')
        activity = request.args.get('activity')
        sub_activity = request.args.get('subActivity')
        coordinator_email = request.args.get('coordinatorEmail')
        department = request.args.get('department')
        branch = request.args.get('branch')
        course = request.args.get('course')
        
        query = CourseRegistration.query
        if status:
            query = query.filter_by(status=status)
        if activity:
            query = query.filter(
                (CourseRegistration.activity_name == activity) | 
                (CourseRegistration.activity_category == activity)
            )
        if sub_activity:
            query = query.filter(CourseRegistration.activity_name == sub_activity)
        if department:
            query = query.filter_by(department=department)
        if branch:
            query = query.filter(CourseRegistration.data['branch'].astext == branch)
        if course:
            query = query.filter(CourseRegistration.course == course)
        
        # If coordinator_email provided, filter by their activity
        if coordinator_email:
            coordinator = Coordinator.query.filter_by(email=coordinator_email).first()
            if coordinator:
                query = query.filter(
                    (CourseRegistration.activity_category == coordinator.role) |
                    (CourseRegistration.activity_name.contains(coordinator.role))
                )
        
        regs = query.order_by(CourseRegistration.created_at.desc()).all()
        return jsonify([r.to_dict() for r in regs])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        
        try:
            new_reg = CourseRegistration(
                student_name=payload.get('studentName', ''),
                admission_id=payload.get('admissionId', ''),
                course=payload.get('course', ''),
                department=payload.get('department', ''),
                activity_name=payload.get('activityName', ''),
                activity_category=payload.get('activityCategory', ''),
                sub_activity_id=payload.get('subActivityId'),
                status=payload.get('status', 'Pending Coordinator'),
                data=payload
            )
            db.session.add(new_reg)
            db.session.commit()
            return jsonify(new_reg.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/registrations/<int:reg_id>/coordinator-approve', methods=['POST'])
def coordinator_approve_registration(reg_id):
    """Coordinator approves/rejects a registration"""
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({"error": "Registration not found"}), 404
    
    payload = request.get_json(silent=True) or {}
    action = payload.get('action', '').lower()  # 'approve' or 'reject'
    reason = payload.get('reason', '')
    
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Action must be 'approve' or 'reject'"}), 400
    
    try:
        if action == 'approve':
            reg.coordinator_status = 'approved'
            reg.status = 'coordinator_approved'  # Now pending HOD approval
        else:
            reg.coordinator_status = 'rejected'
            reg.status = 'rejected'
            reg.rejection_reason = reason or 'Rejected by coordinator'
        
        db.session.commit()
        return jsonify({"success": True, "registration": reg.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/registrations/<int:reg_id>/hod-approve', methods=['POST'])
def hod_approve_registration(reg_id):
    """HOD approves/rejects a registration (only if coordinator approved)"""
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({"error": "Registration not found"}), 404
    
    if reg.coordinator_status != 'approved':
        return jsonify({"error": "Registration must be approved by coordinator first"}), 400
    
    payload = request.get_json(silent=True) or {}
    action = payload.get('action', '').lower()  # 'approve' or 'reject'
    reason = payload.get('reason', '')
    
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Action must be 'approve' or 'reject'"}), 400
    
    try:
        if action == 'approve':
            reg.hod_status = 'approved'
            reg.status = 'hod_approved'  # Fully approved
            
            # Update sub-activity slot count if linked
            if reg.sub_activity_id:
                sub_activity = SubActivity.query.get(reg.sub_activity_id)
                if sub_activity:
                    sub_activity.filled_slots += 1
                    # Deactivate if full
                    if sub_activity.filled_slots >= sub_activity.total_slots:
                        sub_activity.is_active = False
        else:
            reg.hod_status = 'rejected'
            reg.status = 'rejected'
            reg.rejection_reason = reason or 'Rejected by HOD'
        
        db.session.commit()
        return jsonify({"success": True, "registration": reg.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/course-registrations/<int:reg_id>', methods=['GET', 'PUT', 'DELETE'])
def course_registration_detail(reg_id):
    reg = CourseRegistration.query.get(reg_id)
    if not reg:
        return jsonify({"error": "Registration not found"}), 404
    
    if request.method == 'GET':
        return jsonify(reg.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        if 'status' in payload:
            reg.status = payload['status']
        if 'studentName' in payload:
            reg.student_name = payload['studentName']
        if 'admissionId' in payload:
            reg.admission_id = payload['admissionId']
        if 'course' in payload:
            reg.course = payload['course']
        if 'activityName' in payload:
            reg.activity_name = payload['activityName']
        if 'activityCategory' in payload:
            reg.activity_category = payload['activityCategory']
        
        # Update the data JSON field with full payload
        reg.data = {**reg.data, **payload} if reg.data else payload
        reg.last_updated = datetime.utcnow()
        
        try:
            db.session.commit()
            return jsonify(reg.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(reg)
            db.session.commit()
            return jsonify({"success": True, "message": "Registration deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Event Management Endpoints
@app.route('/api/events', methods=['GET', 'POST'])
def events():
    if request.method == 'GET':
        activity_name = request.args.get('activity')
        sub_activity_id = request.args.get('subActivityId')
        coordinator_email = request.args.get('coordinatorEmail')
        is_active = request.args.get('isActive')
        
        query = Event.query
        
        if activity_name:
            query = query.filter_by(activity_name=activity_name)
        if sub_activity_id:
            query = query.filter_by(sub_activity_id=int(sub_activity_id))
        if coordinator_email:
            query = query.filter_by(coordinator_email=coordinator_email)
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        events = query.order_by(Event.event_date.desc()).all()
        return jsonify([e.to_dict() for e in events])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        event_name = payload.get('eventName', '').strip()
        activity_name = payload.get('activityName', '').strip()
        event_date = payload.get('eventDate')
        
        if not all([event_name, activity_name, event_date]):
            return jsonify({"error": "Event name, activity name, and date are required"}), 400
        
        try:
            from dateutil import parser
            event_date_obj = parser.parse(event_date)
        except:
            return jsonify({"error": "Invalid date format"}), 400
        
        try:
            new_event = Event(
                event_name=event_name,
                activity_name=activity_name,
                sub_activity_id=payload.get('subActivityId'),
                coordinator_email=payload.get('coordinatorEmail', '').strip(),
                event_date=event_date_obj,
                event_time=payload.get('eventTime', ''),
                location=payload.get('location', ''),
                description=payload.get('description', ''),
                assigned_students=payload.get('assignedStudents', []),
                is_active=payload.get('isActive', True)
            )
            db.session.add(new_event)
            db.session.commit()
            return jsonify(new_event.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/events/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
def event_detail(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    if request.method == 'GET':
        return jsonify(event.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        if 'eventName' in payload:
            event.event_name = payload['eventName'].strip()
        if 'activityName' in payload:
            event.activity_name = payload['activityName'].strip()
        if 'eventDate' in payload:
            try:
                from dateutil import parser
                event.event_date = parser.parse(payload['eventDate'])
            except:
                return jsonify({"error": "Invalid date format"}), 400
        if 'eventTime' in payload:
            event.event_time = payload['eventTime']
        if 'location' in payload:
            event.location = payload['location']
        if 'description' in payload:
            event.description = payload['description']
        if 'assignedStudents' in payload:
            event.assigned_students = payload['assignedStudents']
        if 'isActive' in payload:
            event.is_active = payload['isActive']
        
        try:
            db.session.commit()
            return jsonify(event.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(event)
            db.session.commit()
            return jsonify({"success": True, "message": "Event deleted successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Attendance Management Endpoints
@app.route('/api/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'GET':
        student_admission_id = request.args.get('studentAdmissionId')
        activity_name = request.args.get('activity')
        sub_activity_id = request.args.get('subActivityId')
        event_id = request.args.get('eventId')
        attendance_type = request.args.get('type')
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        query = Attendance.query
        
        if student_admission_id:
            query = query.filter_by(student_admission_id=student_admission_id)
        if activity_name:
            query = query.filter_by(activity_name=activity_name)
        if sub_activity_id:
            query = query.filter_by(sub_activity_id=int(sub_activity_id))
        if event_id:
            query = query.filter_by(event_id=int(event_id))
        if attendance_type:
            query = query.filter_by(attendance_type=attendance_type)
        if date_from:
            try:
                from dateutil import parser
                query = query.filter(Attendance.attendance_date >= parser.parse(date_from).date())
            except:
                pass
        if date_to:
            try:
                from dateutil import parser
                query = query.filter(Attendance.attendance_date <= parser.parse(date_to).date())
            except:
                pass
        
        records = query.order_by(Attendance.attendance_date.desc()).all()
        return jsonify([a.to_dict() for a in records])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        
        # Handle bulk attendance marking
        if 'attendanceRecords' in payload:
            records = payload['attendanceRecords']
            try:
                for record in records:
                    new_attendance = Attendance(
                        student_admission_id=record.get('studentAdmissionId', '').strip(),
                        student_name=record.get('studentName', '').strip(),
                        activity_name=record.get('activityName', '').strip(),
                        sub_activity_id=record.get('subActivityId'),
                        event_id=record.get('eventId'),
                        attendance_date=datetime.strptime(record.get('attendanceDate'), '%Y-%m-%d').date(),
                        attendance_type=record.get('attendanceType', 'daily'),
                        status=record.get('status', 'present'),
                        coordinator_email=record.get('coordinatorEmail', '').strip(),
                        remarks=record.get('remarks', '')
                    )
                    db.session.add(new_attendance)
                db.session.commit()
                return jsonify({"success": True, "message": f"Added {len(records)} attendance records"}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Database error: {str(e)}"}), 500
        
        # Handle single attendance record
        else:
            student_admission_id = payload.get('studentAdmissionId', '').strip()
            activity_name = payload.get('activityName', '').strip()
            attendance_date = payload.get('attendanceDate')
            
            if not all([student_admission_id, activity_name, attendance_date]):
                return jsonify({"error": "Student ID, activity name, and date are required"}), 400
            
            try:
                new_attendance = Attendance(
                    student_admission_id=student_admission_id,
                    student_name=payload.get('studentName', '').strip(),
                    activity_name=activity_name,
                    sub_activity_id=payload.get('subActivityId'),
                    event_id=payload.get('eventId'),
                    attendance_date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                    attendance_type=payload.get('attendanceType', 'daily'),
                    status=payload.get('status', 'present'),
                    coordinator_email=payload.get('coordinatorEmail', '').strip(),
                    remarks=payload.get('remarks', '')
                )
                db.session.add(new_attendance)
                db.session.commit()
                return jsonify(new_attendance.to_dict()), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/attendance/<int:attendance_id>', methods=['GET', 'PUT', 'DELETE'])
def attendance_detail(attendance_id):
    attendance_record = Attendance.query.get(attendance_id)
    if not attendance_record:
        return jsonify({"error": "Attendance record not found"}), 404
    
    if request.method == 'GET':
        return jsonify(attendance_record.to_dict())
    
    elif request.method == 'PUT':
        payload = request.get_json(silent=True) or {}
        
        if 'status' in payload:
            attendance_record.status = payload['status']
        if 'remarks' in payload:
            attendance_record.remarks = payload['remarks']
        
        try:
            db.session.commit()
            return jsonify(attendance_record.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(attendance_record)
            db.session.commit()
            return jsonify({"success": True, "message": "Attendance record deleted"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


# Analytics Endpoints
@app.route('/api/analytics/student/<admission_id>', methods=['GET'])
def student_analytics(admission_id):
    """Get analytics for a specific student"""
    # Get all attendance records
    attendance_records = Attendance.query.filter_by(student_admission_id=admission_id).all()
    
    total_days = len(attendance_records)
    present_days = len([a for a in attendance_records if a.status == 'present'])
    absent_days = len([a for a in attendance_records if a.status == 'absent'])
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Get registration info
    registration = Registration.query.filter_by(admission_id=admission_id, status='hod_approved').first()
    
    return jsonify({
        "studentAdmissionId": admission_id,
        "totalDays": total_days,
        "presentDays": present_days,
        "absentDays": absent_days,
        "attendanceRate": round(attendance_rate, 2),
        "registration": registration.to_dict() if registration else None
    })


@app.route('/api/analytics/activity/<activity_name>', methods=['GET'])
def activity_analytics(activity_name):
    """Get analytics for a specific activity"""
    # Get all approved registrations for this activity
    registrations = Registration.query.filter_by(activity_name=activity_name, status='hod_approved').all()
    
    # Get sub-activities
    sub_activities = SubActivity.query.filter_by(activity_name=activity_name).all()
    
    # Get attendance stats
    attendance_records = Attendance.query.filter_by(activity_name=activity_name).all()
    total_attendance_days = len(attendance_records)
    present_count = len([a for a in attendance_records if a.status == 'present'])
    
    return jsonify({
        "activityName": activity_name,
        "totalEnrolled": len(registrations),
        "subActivities": [s.to_dict() for s in sub_activities],
        "totalAttendanceDays": total_attendance_days,
        "presentCount": present_count,
        "overallAttendanceRate": round((present_count / total_attendance_days * 100) if total_attendance_days > 0 else 0, 2)
    })


@app.route('/api/analytics/department/<department>', methods=['GET'])
def department_analytics(department):
    """Get analytics for a specific department (HOD view)"""
    # Get all students from this department
    students = Student.query.filter_by(department=department).all()
    
    # Get registrations from this department
    registrations = Registration.query.filter_by(department=department).all()
    approved_regs = [r for r in registrations if r.status == 'hod_approved']
    pending_regs = [r for r in registrations if r.status in ['pending', 'coordinator_approved']]
    
    # Count by activity
    activity_distribution = {}
    for reg in approved_regs:
        activity_distribution[reg.activity_name] = activity_distribution.get(reg.activity_name, 0) + 1
    
    return jsonify({
        "department": department,
        "totalStudents": len(students),
        "totalRegistrations": len(registrations),
        "approvedRegistrations": len(approved_regs),
        "pendingRegistrations": len(pending_regs),
        "activityDistribution": activity_distribution
    })


@app.route('/api/students/by-activity', methods=['GET'])
def students_by_activity():
    """Get students filtered by activity, sub-activity, year, branch, etc. (for coordinators)"""
    activity_name = request.args.get('activity')
    sub_activity_id = request.args.get('subActivityId')
    year = request.args.get('year')
    branch = request.args.get('branch')
    section = request.args.get('section')
    coordinator_email = request.args.get('coordinatorEmail')
    
    # Start with approved registrations
    query = Registration.query.filter_by(status='hod_approved')
    
    if activity_name:
        query = query.filter_by(activity_name=activity_name)
    elif coordinator_email:
        # Filter by coordinator's activity
        coordinator = Coordinator.query.filter_by(email=coordinator_email).first()
        if coordinator:
            query = query.filter_by(activity_name=coordinator.role)
    
    if sub_activity_id:
        query = query.filter_by(sub_activity_id=int(sub_activity_id))
    
    registrations = query.all()
    
    # Filter by student details from data JSON
    students_data = []
    for reg in registrations:
        data = reg.data or {}
        
        # Apply filters
        if year and data.get('year') != year:
            continue
        if branch and data.get('branch') != branch:
            continue
        if section and data.get('section') != section:
            continue
        
        students_data.append({
            **data,
            "registrationId": reg.id,
            "admissionId": reg.admission_id,
            "studentName": reg.student_name,
            "department": reg.department,
            "activityName": reg.activity_name,
            "status": reg.status
        })
    
    return jsonify(students_data)


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all() # Creates tables if they don't exist
            print("✅ Successfully connected to the database and created tables.")
            
            # Ensure all roles exist
            roles_to_create = [
                ('CREATOR', 'System Administrator'),
                ('STUDENT', 'Student'),
                ('HOD', 'Head of Department'),
                ('COORDINATOR', 'Faculty Coordinator')
            ]
            
            for role_name, description in roles_to_create:
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    role = Role(name=role_name, description=description)
                    db.session.add(role)
            db.session.commit()
            
            # Ensure all default users exist
            users_to_create = [
                {
                    'email': 'admin@pbsiddhartha.ac.in',
                    'password': 'admin123',
                    'name': 'System Administrator',
                    'role': 'CREATOR',
                    'employee_id': 'ADMIN001'
                },
                {
                    'email': 'student@pbsiddhartha.ac.in',
                    'password': 'student123',
                    'name': 'Test Student',
                    'role': 'STUDENT',
                    'employee_id': '22B91A05L6'
                },
                {
                    'email': 'hod@pbsiddhartha.ac.in',
                    'password': 'hod123',
                    'name': 'Dr. K Uday Sri',
                    'role': 'HOD',
                    'employee_id': '12345'
                },
                {
                    'email': 'ruhi@pbsiddhartha.ac.in',
                    'password': 'ruhi123',
                    'name': 'Ruhi - NCC Coordinator',
                    'role': 'COORDINATOR',
                    'employee_id': '123'
                }
            ]
            
            for user_data in users_to_create:
                # Check if user exists by email OR employee_id
                user = User.query.filter(
                    (User.email == user_data['email']) | (User.employee_id == user_data['employee_id'])
                ).first()
                if not user:
                    role = Role.query.filter_by(name=user_data['role']).first()
                    password_hash = hash_password(user_data['password'])
                    
                    user = User(
                        email=user_data['email'],
                        password_hash=password_hash,
                        full_name=user_data['name'],
                        role_id=role.id,
                        employee_id=user_data['employee_id'],
                        assigned_activity_name='NCC' if user_data['role'] == 'COORDINATOR' else None,
                        is_temp_password=False,
                        profile_completed=True,
                        is_active=True
                    )
                    db.session.add(user)
            db.session.commit()
            
            # Print all available credentials
            print("\n✅ All default users are ready!")
            print("\n📋 Available Login Credentials:")
            print("=" * 80)
            print("Creator/Admin:   admin@pbsiddhartha.ac.in / admin123")
            print("Student:         student@pbsiddhartha.ac.in / student123")
            print("HOD:             hod@pbsiddhartha.ac.in / hod123")
            print("Coordinator:     ruhi@pbsiddhartha.ac.in / ruhi123")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Database Error: {e}")
            print("💡 Hint: Run 'python backend/create_db.py' to create the database first.")
            exit(1)
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=True)
