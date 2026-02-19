import os
import logging
import traceback
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON, func
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from werkzeug.utils import secure_filename
import bcrypt
import secrets

load_dotenv()

# ============================================================================
# LOGGING SETUP
# Writes WARNING+ to errors.log (rotates at 5MB, keeps 3 backups)
# Writes INFO+ to console
# ============================================================================
APP_DIR_FOR_LOG = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_DIR_FOR_LOG, 'errors.log')

_file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
_file_handler.setLevel(logging.WARNING)
_file_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _console_handler])
logger = logging.getLogger(__name__)

# ============================================================================
# TELEGRAM ALERT
# Sends instant phone notification when server crashes
# ============================================================================
def send_telegram_alert(message: str):
    """Send an alert message to Telegram. Fails silently so it never breaks the app."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return  # Not configured, skip silently
    try:
        import urllib.request, urllib.parse, json as _json
        payload = _json.dumps({
            'chat_id': chat_id,
            'text': message[:4000],  # Telegram max message length
            'parse_mode': 'HTML'
        }).encode('utf-8')
        req = urllib.request.Request(
            f'https://api.telegram.org/bot{token}/sendMessage',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Never let Telegram failure break the app


APP_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(APP_DIR)
WEB_DIR = os.path.join(PARENT_DIR, 'web')
UPLOAD_FOLDER = os.path.join(APP_DIR, 'uploads')

app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Secret key for sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database Configuration from environment variables
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '1234')
db_host = os.getenv('DB_HOST', '127.0.0.1')  # Use 127.0.0.1 instead of localhost to avoid IPv6 issues
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'school_db')

database_url = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
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
    
    # HOD/Faculty Professional Information
    specialization = db.Column(db.String(255))
    qualifications = db.Column(db.String(255))
    bio = db.Column(db.Text)
    
    # Profile completion tracking
    profile_completed = db.Column(db.Boolean, default=False)
    is_temp_password = db.Column(db.Boolean, default=True)
    registration_status = db.Column(db.String(20), default='PENDING') # 'PENDING', 'APPROVED', 'REJECTED'
    
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
            'specialization': self.specialization,
            'qualifications': self.qualifications,
            'bio': self.bio,
            'profileCompleted': self.profile_completed,
            'isTempPassword': self.is_temp_password,
            'registrationStatus': self.registration_status,
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
    lookup_key = db.Column(db.String(255), unique=True, index=True)
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
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.employee_id,
            'dbId': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


class ProgramDepartmentMapping(db.Model):
    """Maps program names to department names for HOD lookup"""
    __tablename__ = 'program_department_mappings'
    id = db.Column(db.Integer, primary_key=True)
    program_name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    department_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'programName': self.program_name,
            'departmentName': self.department_name,
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
    sub_activity_lead_name = db.Column(db.String(255))  # Sub-activity lead/coordinator name
    sub_activity_lead_phone = db.Column(db.String(20))  # Sub-activity lead phone
    activity_head_name = db.Column(db.String(255))  # Main activity head/incharge name
    activity_head_phone = db.Column(db.String(20))  # Main activity head phone
    total_slots = db.Column(db.Integer, default=0)  # Total available slots
    filled_slots = db.Column(db.Integer, default=0)  # Number of filled slots
    is_active = db.Column(db.Boolean, default=True)  # Whether accepting applications
    data = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        total = self.total_slots if self.total_slots is not None else 0
        filled = self.filled_slots if self.filled_slots is not None else 0
        available_slots = (total if total is not None else 0) - (filled if filled is not None else 0)
        is_full = available_slots <= 0
        is_active = self.is_active if self.is_active is not None else True
        return {
            'id': self.id,
            'activityName': (self.activity_name or '').upper(),  # Ensure UPPERCASE
            'subActivityName': self.sub_activity_name,
            'coordinatorEmail': self.coordinator_email,
            'subActivityLeadName': self.sub_activity_lead_name,
            'subActivityLeadPhone': self.sub_activity_lead_phone,
            'activityHeadName': self.activity_head_name,
            'activityHeadPhone': self.activity_head_phone,
            'totalSlots': total,
            'filledSlots': filled,
            'availableSlots': available_slots,
            'isFull': is_full,
            'isActive': is_active,
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
            'branch': self.department,  # Alias for frontend compatibility
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
    event_end_date = db.Column(db.DateTime)  # For multi-day events
    event_time = db.Column(db.String(50))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    assigned_students = db.Column(JSON)  # List of student admission IDs assigned to this event
    is_active = db.Column(db.Boolean, default=True)
    # New fields for event types and approval workflow
    event_type = db.Column(db.String(50), default='college')  # government, college, practice, competition, other
    event_status = db.Column(db.String(50), default='approved')  # draft, pending_approval, approved, completed, cancelled
    created_by_role = db.Column(db.String(50), default='faculty_coordinator')  # faculty_coordinator, student_coordinator
    requires_approval = db.Column(db.Boolean, default=False)  # True if created by student coordinator
    approved_by = db.Column(db.String(255))  # Faculty who approved (for student coordinator events)
    approved_at = db.Column(db.DateTime)  # When approved
    required_students = db.Column(db.Integer)  # Target number of students needed
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
            'eventEndDate': self.event_end_date.isoformat() if self.event_end_date else None,
            'eventTime': self.event_time,
            'location': self.location,
            'description': self.description,
            'assignedStudents': self.assigned_students or [],
            'isActive': self.is_active,
            'eventType': self.event_type or 'college',
            'eventStatus': self.event_status or 'approved',
            'createdByRole': self.created_by_role or 'faculty_coordinator',
            'requiresApproval': self.requires_approval or False,
            'approvedBy': self.approved_by,
            'approvedAt': self.approved_at.isoformat() if self.approved_at else None,
            'requiredStudents': self.required_students,
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
    # Approval workflow fields
    approval_status = db.Column(db.String(20), default='approved')  # 'pending', 'approved', 'rejected'
    submitted_by = db.Column(db.String(255))  # Student coordinator who submitted
    approved_by = db.Column(db.String(255))  # Faculty coordinator who approved
    approved_at = db.Column(db.DateTime)  # When it was approved
    batch_id = db.Column(db.String(100))  # Group attendance submissions together
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
            'approvalStatus': self.approval_status,
            'submittedBy': self.submitted_by,
            'approvedBy': self.approved_by,
            'approvedAt': self.approved_at.isoformat() if self.approved_at else None,
            'batchId': self.batch_id,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    """In-app notifications for students and coordinators"""
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.String(255), nullable=False, index=True)  # admission_id for students, email for coordinators
    recipient_type = db.Column(db.String(50), default='student')  # student, coordinator, faculty
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='general')  # event_assignment, event_reminder, event_update, approval_request, general
    related_event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'recipientId': self.recipient_id,
            'recipientType': self.recipient_type,
            'title': self.title,
            'message': self.message,
            'notificationType': self.notification_type,
            'relatedEventId': self.related_event_id,
            'isRead': self.is_read,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


class EventParticipant(db.Model):
    """Track students assigned to events with their status"""
    __tablename__ = 'event_participants'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    student_admission_id = db.Column(db.String(255), nullable=False, index=True)
    student_name = db.Column(db.String(255))
    student_department = db.Column(db.String(255))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.String(255))  # Coordinator who assigned
    notification_sent = db.Column(db.Boolean, default=False)
    attendance_status = db.Column(db.String(20))  # present, absent, null (not yet taken)
    attended_at = db.Column(db.DateTime)  # When attendance was marked
    remarks = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'eventId': self.event_id,
            'studentAdmissionId': self.student_admission_id,
            'studentName': self.student_name,
            'studentDepartment': self.student_department,
            'assignedAt': self.assigned_at.isoformat() if self.assigned_at else None,
            'assignedBy': self.assigned_by,
            'notificationSent': self.notification_sent,
            'attendanceStatus': self.attendance_status,
            'attendedAt': self.attended_at.isoformat() if self.attended_at else None,
            'remarks': self.remarks
        }


@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory(WEB_DIR, 'index.html')


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
    """Student authentication endpoint - fetch from students table using roll number"""
    payload = request.get_json(silent=True) or {}
    roll_number = payload.get('rollNumber', '').strip().lower()
    
    # Fallback for old requests or those passing email as roll number
    if not roll_number:
        email = payload.get('email', '').strip().lower()
        if email:
            roll_number = email.split('@')[0]
            
    if not roll_number:
        return jsonify({"error": "Roll number is required"}), 400
    
    # Check in students table (where we imported CSV data)
    student = Student.query.filter_by(lookup_key=roll_number).first()
    if student:
        # Extract student name from profile or use roll number
        profile = student.profile or {}
        student_name = profile.get('studentName', roll_number)
        
        return jsonify({
            "success": True,
            "student": {
                "name": student_name,
                "rollNo": roll_number,
                "email": f"{roll_number}@pbsiddhartha.ac.in",
                "department": student.department,
                "role": "STUDENT",
                "profile": profile
            }
        })
    
    # Second check: Look in unified users table (case-insensitive for employee_id/roll_no)
    user = User.query.filter(
        (func.lower(User.employee_id) == func.lower(roll_number)),
        User.is_active == True
    ).first()
    
    if user:
        role = Role.query.get(user.role_id)
        if role and role.name == 'STUDENT':
            return jsonify({
                "success": True,
                "student": {
                    "name": user.full_name,
                    "rollNo": user.employee_id,
                    "email": user.email,
                    "role": "STUDENT"
                }
            })
    
    return jsonify({"error": "Student not found with this roll number"}), 404


@app.route('/api/student/profile/<string:roll_number>', methods=['GET'])
def get_student_profile(roll_number):
    """Get complete student profile by roll number for auto-fill"""
    roll_number = roll_number.strip().lower()
    
    student = Student.query.filter_by(lookup_key=roll_number).first()
    if not student:
        return jsonify({"error": "Student not found", "rollNumber": roll_number}), 404
    
    profile = student.profile or {}
    
    # Get department info - first try profile, then fall back to student.department column
    dept_code = profile.get('departmentCode', '')
    dept_id = profile.get('departmentId')
    program = profile.get('program', '')
    dept_name = profile.get('departmentName', '') or student.department
    
    # If no department but we have program, use the program-to-department mapping table
    if not dept_name and program:
        dept_name = get_program_to_department_mapping(program)
    
    # Final fallback to program name
    if not dept_name:
        dept_name = program
    
    # If no departmentCode but we have department name, try to find the department
    if not dept_code and dept_name:
        # First try the mapped department name
        dept = Department.query.filter_by(name=dept_name).first()
        if not dept:
            # Try using program-to-department mapping
            mapped_dept = get_program_to_department_mapping(dept_name)
            dept = Department.query.filter_by(name=mapped_dept).first()
        if not dept:
            # Try matching by program name
            dept = Department.query.filter(func.lower(Department.name).like(func.lower(f'%{dept_name}%'))).first()
        if dept:
            dept_code = dept.code
            dept_id = dept.id
            # Update dept_name to the actual department name
            dept_name = dept.name
    
    # Get HOD info for student's department - check both User table AND hods table
    hod_info = None
    
    # DSAI umbrella variants for matching
    dsai_variants = ['data science & ai', 'data science and ai', 'ds & ai', 'ds&ai', 'dsai', 
                     'artificial intelligence', 'b.sc.-honours(ai)', 'ai']
    def is_dsai(name):
        name_lower = (name or '').lower()
        return any(v in name_lower or name_lower in v for v in dsai_variants)
    
    # First try direct lookup in hods table by department name
    hod = HOD.query.filter(
        (func.lower(HOD.department) == func.lower(dept_name)) |
        (func.lower(HOD.department) == func.lower(dept_code if dept_code else ''))
    ).first()
    
    # If not found and this looks like DSAI, try DSAI variants
    if not hod and is_dsai(dept_name):
        hod = HOD.query.filter(
            (func.lower(HOD.department) == 'dsai') |
            (func.lower(HOD.department).like('%data science%'))
        ).first()
    
    if hod:
        hod_info = {
            'name': hod.name,
            'email': hod.email,
            'phone': hod.phone,
            'departmentId': dept_id,
            'department': hod.department,
            'available': True
        }
    
    # Fallback: check User table for HOD
    if not hod_info:
        # If dept_id is null, try to find it by department name first
        lookup_dept_id = dept_id
        if not lookup_dept_id and dept_name:
            # Try direct match
            dept_lookup = Department.query.filter(
                (func.lower(Department.name) == func.lower(dept_name)) |
                (func.lower(Department.code) == func.lower(dept_name))
            ).first()
            # If DSAI variant, try broader match
            if not dept_lookup and is_dsai(dept_name):
                dept_lookup = Department.query.filter(
                    (func.lower(Department.name).like('%data science%')) |
                    (func.lower(Department.code) == 'dsai')
                ).first()
            if dept_lookup:
                lookup_dept_id = dept_lookup.id
        
        if lookup_dept_id:
            hod_user = User.query.filter_by(assigned_department_id=lookup_dept_id).first()
            if hod_user:
                hod_info = {
                    'name': hod_user.full_name,
                    'email': hod_user.email,
                    'phone': hod_user.phone,
                    'departmentId': lookup_dept_id,
                    'available': True
                }
    
    if not hod_info:
        hod_info = {'available': False, 'message': 'HOD not assigned for this department'}
    
    return jsonify({
        "success": True,
        "student": {
            "rollNo": roll_number.upper(),
            "name": profile.get('studentName', ''),
            "fatherName": profile.get('fatherName', ''),
            "motherName": profile.get('motherName', ''),
            "email": f"{roll_number}@pbsiddhartha.ac.in",
            "mobileNo": profile.get('mobileNo', ''),
            "gender": profile.get('gender', ''),
            "dob": profile.get('dob', ''),
            "aadharNo": profile.get('aadharNo', ''),
            "caste": profile.get('caste', ''),
            "joiningYear": profile.get('joiningYear', ''),
            "currentSem": profile.get('currentSem', ''),
            "section": profile.get('section', ''),
            "program": profile.get('program', ''),
            "pcode": profile.get('pcode', ''),
            "departmentCode": dept_code,
            "departmentId": dept_id,
            "departmentName": dept_name,
            "department": dept_name,
            "profileImage": profile.get('profileImage', ''),
            "address": profile.get('address', ''),
            "bloodGroup": profile.get('bloodGroup', ''),
        },
        "hod": hod_info,
        "fieldsFromDb": list(profile.keys())
    })


@app.route('/api/student/profile/<string:roll_number>', methods=['PUT'])
def update_student_profile(roll_number):
    """Update student profile with new/modified data"""
    roll_number = roll_number.strip().lower()
    payload = request.get_json(silent=True) or {}
    
    student = Student.query.filter_by(lookup_key=roll_number).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    current_profile = student.profile or {}
    
    # Fields that can be updated by student
    updatable_fields = [
        'mobileNo', 'address', 'bloodGroup', 'parentMobile',
        'presentAddress', 'permanentAddress', 'email'
    ]
    
    for field in updatable_fields:
        if field in payload and payload[field]:
            current_profile[field] = payload[field]
    
    # Update any missing fields
    for key, value in payload.items():
        if key not in current_profile or not current_profile[key]:
            current_profile[key] = value
    
    student.profile = current_profile
    student.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Profile updated successfully",
        "profile": current_profile
    })


@app.route('/api/activity-lead/<string:activity_name>', methods=['GET'])
def get_activity_lead(activity_name):
    """Get main activity lead and sub-lead for an activity"""
    activity_name = activity_name.strip()
    
    # Find main activity coordinator
    main_lead = User.query.filter(
        func.lower(User.assigned_activity_name) == func.lower(activity_name),
        User.is_active == True
    ).first()
    
    main_lead_info = None
    if main_lead:
        main_lead_info = {
            'name': main_lead.full_name,
            'email': main_lead.email,
            'phone': main_lead.phone,
            'role': 'Main Activity Lead',
            'activity': main_lead.assigned_activity_name,
            'available': True
        }
    else:
        main_lead_info = {'available': False, 'message': f'Activity lead not assigned for {activity_name}'}
    
    # Find sub-activity leads from SubActivity table
    sub_leads = []
    sub_activities = SubActivity.query.filter(
        func.lower(SubActivity.activity_name) == func.lower(activity_name),
        SubActivity.is_active == True
    ).all()
    
    for sub in sub_activities:
        if sub.sub_activity_lead_name:
            total_slots = sub.total_slots if sub.total_slots is not None else 0
            filled_slots = sub.filled_slots if sub.filled_slots is not None else 0
            sub_leads.append({
                'subActivityId': sub.id,
                'subActivityName': sub.sub_activity_name,
                'leadName': sub.sub_activity_lead_name,
                'leadPhone': sub.sub_activity_lead_phone,
                'activityHeadName': sub.activity_head_name,
                'activityHeadPhone': sub.activity_head_phone,
                'totalSlots': total_slots,
                'availableSlots': total_slots - filled_slots
            })
    
    return jsonify({
        "success": True,
        "mainLead": main_lead_info,
        "subLeads": sub_leads,
        "activityName": activity_name
    })


@app.route('/api/hod/by-department/<string:dept_code>', methods=['GET'])
def get_hod_by_department_code(dept_code):
    """Get HOD details by department code"""
    dept = Department.query.filter(func.lower(Department.code) == func.lower(dept_code)).first()
    
    if not dept:
        return jsonify({
            "available": False,
            "error": "Department not found",
            "departmentCode": dept_code
        }), 404
    
    hod_user = User.query.filter_by(assigned_department_id=dept.id).first()
    
    if not hod_user:
        return jsonify({
            "available": False,
            "departmentId": dept.id,
            "departmentName": dept.name,
            "departmentCode": dept.code,
            "message": "HOD not assigned for this department"
        })
    
    return jsonify({
        "available": True,
        "hod": {
            "name": hod_user.full_name,
            "email": hod_user.email,
            "phone": hod_user.phone,
            "employeeId": hod_user.employee_id
        },
        "department": {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code
        }
    })


@app.route('/api/registration/validate', methods=['POST'])
def validate_registration_data():
    """Validate registration data before submission"""
    payload = request.get_json(silent=True) or {}
    errors = []
    warnings = []
    
    roll_number = payload.get('rollNumber', '').strip().lower()
    
    # Validate roll number exists
    if not roll_number:
        errors.append({'field': 'rollNumber', 'message': 'Roll number is required'})
    else:
        student = Student.query.filter_by(lookup_key=roll_number).first()
        if not student:
            errors.append({'field': 'rollNumber', 'message': 'Invalid roll number - not found in database'})
    
    # Validate required fields
    required_fields = ['studentName', 'mobileNo', 'department']
    for field in required_fields:
        if not payload.get(field):
            errors.append({'field': field, 'message': f'{field} is required'})
    
    # Validate mobile number format
    mobile = payload.get('mobileNo', '')
    if mobile and (len(mobile) != 10 or not mobile.isdigit()):
        errors.append({'field': 'mobileNo', 'message': 'Mobile number must be 10 digits'})
    
    # Check HOD assignment for department
    dept_id = payload.get('departmentId')
    if dept_id:
        hod = User.query.filter_by(assigned_department_id=dept_id).first()
        if not hod:
            warnings.append({'field': 'department', 'message': 'HOD not assigned for selected department'})
    
    # Check activity lead if activity selected
    activity_name = payload.get('activityName')
    if activity_name:
        lead = User.query.filter(
            func.lower(User.assigned_activity_name) == func.lower(activity_name),
            User.is_active == True
        ).first()
        if not lead:
            warnings.append({'field': 'activityName', 'message': f'Activity lead not assigned for {activity_name}'})
    
    return jsonify({
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    })


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
        func.lower(User.email) == func.lower(email),
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
        func.lower(User.email) == func.lower(email),
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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/profile/upload-photo', methods=['POST'])
def upload_profile_photo():
    """Endpoint to upload a profile photo"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    if 'photo' not in request.files:
        return jsonify({"error": "No photo file provided"}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"profile_{user_id}_{int(datetime.utcnow().timestamp())}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Update user profile_photo in DB
        relative_path = f"/uploads/{filename}"
        user = User.query.get(user_id)
        user.profile_photo = relative_path
        db.session.commit()
        
        return jsonify({
            "success": True,
            "profilePhoto": relative_path
        })
    
    return jsonify({"error": "File type not allowed"}), 400


@app.route('/api/auth/login', methods=['POST'])
def unified_login():
    """Unified login endpoint for all users (Creator, HOD, Coordinator)"""
    try:
        payload = request.get_json(silent=True) or {}
        email = payload.get('email', '').strip()
        password = payload.get('password', '').strip()
        
        print(f"DEBUG: Login attempt for email='{email}'")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Find user by email - case insensitive search
        # Using func.lower() is better than fetching all users
        user = User.query.filter(func.lower(User.email) == func.lower(email), User.is_active == True).first()
        
        if not user:
            print(f"DEBUG: User '{email}' not found")
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Verify password
        if not verify_password(password, user.password_hash):
            print(f"DEBUG: Password verification failed for user '{email}'")
            return jsonify({"error": "Invalid email or password"}), 401
        
        print(f"DEBUG: Login successful for user '{email}' (Role ID: {user.role_id})")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create session
        session.permanent = True
        session['user_id'] = user.id
        role = Role.query.get(user.role_id)
        role_name = role.name if role else None
        session['role'] = role_name
        
        # Set HOD specific session for backward compatibility
        if role_name == 'HOD':
            dept = Department.query.get(user.assigned_department_id)
            session['hod_session'] = {
                'hod_id': user.id,
                'employee_id': user.employee_id,
                'hod_name': user.full_name,
                'dept_code': dept.code if dept else 'UNK',
                'dept_name': dept.name if dept else 'Unknown Department',
                'phone': user.phone,
                'email': user.email,
                'status': 'active',
                'permissions': [{
                    'dept_code': dept.code if dept else 'UNK',
                    'can_view_students': True,
                    'can_approve_requests': True,
                    'can_view_reports': True,
                    'can_manage_courses': True
                }]
            }
        
        return jsonify({
            "success": True,
            "user": user.to_dict(),
            "requiresProfileCompletion": not user.profile_completed and role_name != 'CREATOR',
            "registrationStatus": user.registration_status,
            "isTempPassword": user.is_temp_password
        })
    except Exception as e:
        print(f"ERROR in unified_login: {str(e)}")
        return jsonify({"error": "An internal server error occurred"}), 500


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
    if 'specialization' in payload:
        user.specialization = payload['specialization'].strip()
    if 'qualifications' in payload:
        user.qualifications = payload['qualifications'].strip()
    if 'bio' in payload:
        user.bio = payload['bio'].strip()
    
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
        is_temp_password=True,
        registration_status='APPROVED' # Creator created users are auto-approved
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
        is_temp_password=True,
        registration_status='APPROVED' # Creator created users are auto-approved
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


# NEW UNIFIED MANAGEMENT ENDPOINTS for Creator

@app.route('/api/creator/hods', methods=['GET'])
@require_role('CREATOR')
def list_hod_users():
    """List all HOD users from the unified system"""
    try:
        # Join User, Department, and Role where Role is HOD
        hods = db.session.query(User, Department).join(
            Department, User.assigned_department_id == Department.id
        ).join(
            Role, User.role_id == Role.id
        ).filter(
            Role.name == 'HOD',
            User.is_active == True
        ).all()
        
        result = []
        for user, dept in hods:
            d = user.to_dict()
            d['departmentName'] = dept.name
            d['departmentCode'] = dept.code
            result.append(d)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/creator/update-hod/<int:user_id>', methods=['PUT'])
@require_role('CREATOR')
def update_hod_user(user_id):
    """Update HOD account details"""
    payload = request.get_json(silent=True) or {}
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    full_name = payload.get('fullName')
    email = payload.get('email')
    employee_id = payload.get('employeeId')
    department_id = payload.get('departmentId')
    
    if full_name: user.full_name = full_name
    if email: user.email = email.strip().lower()
    if employee_id: user.employee_id = employee_id
    if department_id: user.assigned_department_id = department_id
    
    try:
        db.session.commit()
        
        # Sync with legacy table if exists
        legacy_hod = HOD.query.filter_by(email=user.email).first() or HOD.query.filter_by(employee_id=user.employee_id).first()
        if legacy_hod:
            if full_name: legacy_hod.name = full_name
            if email: legacy_hod.email = email
            if employee_id: legacy_hod.employee_id = employee_id
            if department_id:
                dept = Department.query.get(department_id)
                if dept: legacy_hod.department = dept.name
            db.session.commit()
            
        return jsonify({"success": True, "message": "HOD updated successfully", "user": user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/creator/delete-hod/<int:user_id>', methods=['DELETE'])
@require_role('CREATOR')
def delete_hod_user(user_id):
    """Delete (deactivate) HOD account"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        # Also handle legacy table
        legacy_hod = HOD.query.filter_by(email=user.email).first() or HOD.query.filter_by(employee_id=user.employee_id).first()
        if legacy_hod:
            db.session.delete(legacy_hod)
            
        # Deactivate instead of hard delete for history
        user.is_active = False 
        db.session.commit()
        return jsonify({"success": True, "message": "HOD deactivated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/activities/search', methods=['GET'])
def search_activities():
    """Search activities by name or pcode"""
    name = request.args.get('name')
    pcode = request.args.get('pcode')
    
    if pcode:
        # Search in the JSON data field for programCode
        activity = Activity.query.filter(Activity.data['programCode'] == str(pcode)).first()
        if activity:
            return jsonify(activity.to_dict())
            
    if not name:
        return jsonify({"error": "Name or pcode parameter required"}), 400
    
    # Fuzzy search or exact Match
    activity = Activity.query.filter(func.lower(Activity.name) == func.lower(name)).first()
    if not activity:
        # Try searching by pshort in data
        activity = Activity.query.filter(func.lower(Activity.data['pshort']) == func.lower(name)).first()
        
    if not activity:
        return jsonify({"error": "Activity not found"}), 404
        
    return jsonify(activity.to_dict())


@app.route('/api/creator/faculty', methods=['GET'])
@require_role('CREATOR')
def list_faculty_users():
    """List all Faculty Coordinators"""
    try:
        coordinators = User.query.join(Role).filter(Role.name == 'FACULTY_COORDINATOR', User.is_active == True).all()
        return jsonify([c.to_dict() for c in coordinators]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/creator/update-faculty/<int:user_id>', methods=['PUT'])
@require_role('CREATOR')
def update_faculty_user(user_id):
    """Update Faculty Coordinator details"""
    payload = request.get_json(silent=True) or {}
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    full_name = payload.get('fullName')
    email = payload.get('email')
    employee_id = payload.get('employeeId')
    activity_name = payload.get('activityName')
    
    if full_name: user.full_name = full_name
    if email: user.email = email.strip().lower()
    if employee_id: user.employee_id = employee_id
    if activity_name: user.assigned_activity_name = activity_name
    
    try:
        db.session.commit()
        
        # Sync legacy
        legacy_coord = Coordinator.query.filter_by(email=user.email).first() or Coordinator.query.filter_by(coordinator_id=user.employee_id).first()
        if legacy_coord:
            if full_name: legacy_coord.name = full_name
            if email: legacy_coord.email = email
            if employee_id: legacy_coord.coordinator_id = employee_id
            if activity_name: legacy_coord.role = activity_name
            db.session.commit()
            
        return jsonify({"success": True, "message": "Coordinator updated successfully", "user": user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/creator/delete-faculty/<int:user_id>', methods=['DELETE'])
@require_role('CREATOR')
def delete_faculty_user(user_id):
    """Delete Faculty Coordinator"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    try:
        legacy_coord = Coordinator.query.filter_by(email=user.email).first() or Coordinator.query.filter_by(coordinator_id=user.employee_id).first()
        if legacy_coord:
            db.session.delete(legacy_coord)
            
        user.is_active = False
        db.session.commit()
        return jsonify({"success": True, "message": "Coordinator deactivated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# NEW: Creator Dashboard - All Registrations View
@app.route('/api/creator/all-registrations', methods=['GET'])
@require_role('CREATOR')
def creator_get_all_registrations():
    """
    Get all student registrations with status for Creator Dashboard.
    Shows activity name, student details, and status (pending/accepted/rejected)
    """
    try:
        # Get all course registrations with full details
        registrations = CourseRegistration.query.order_by(
            CourseRegistration.created_at.desc()
        ).all()
        
        result = []
        for reg in registrations:
            # Get sub-activity details
            sub_activity = SubActivity.query.get(reg.sub_activity_id) if reg.sub_activity_id else None
            
            registration_data = {
                'id': reg.id,
                'studentName': reg.student_name,
                'admissionId': reg.admission_id,
                'department': reg.department,
                'course': reg.course,
                'activityName': reg.activity_name,
                'activityCategory': reg.activity_category,
                'subActivity': sub_activity.sub_activity_name if sub_activity else None,
                'status': reg.status,
                'statusLabel': get_status_label(reg.status),
                'statusColor': get_status_color(reg.status),
                'createdAt': reg.created_at.isoformat() if reg.created_at else None,
                'lastUpdated': reg.last_updated.isoformat() if reg.last_updated else None,
                # Include approval details from data
                'coordinatorApproved': reg.data.get('coordinatorApprovedAt') if reg.data else None,
                'hodApproved': reg.data.get('hodApprovedAt') if reg.data else None,
                'rejectionReason': reg.data.get('rejectionReason') if reg.data else None,
            }
            result.append(registration_data)
        
        # Summary stats
        summary = {
            'total': len(result),
            'pending': len([r for r in result if 'Pending' in r['status']]),
            'accepted': len([r for r in result if r['status'] in ['Accepted', 'Approved', 'hod_approved']]),
            'rejected': len([r for r in result if r['status'] in ['Rejected', 'rejected']]),
        }
        
        return jsonify({
            'registrations': result,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_status_label(status):
    """Get human-readable status label"""
    labels = {
        'Pending Coordinator': 'Waiting for Coordinator',
        'Pending HOD': 'Waiting for HOD',
        'coordinator_approved': 'Coordinator Approved',
        'hod_approved': 'Fully Accepted',
        'Accepted': 'Fully Accepted',
        'Approved': 'Fully Accepted',
        'Rejected': 'Rejected',
        'rejected': 'Rejected',
        'Queued Coordinator': 'In Coordinator Queue',
        'Queued HOD': 'In HOD Queue',
    }
    return labels.get(status, status)


def get_status_color(status):
    """Get status color for frontend"""
    colors = {
        'Pending Coordinator': 'yellow',
        'Pending HOD': 'orange',
        'coordinator_approved': 'blue',
        'hod_approved': 'green',
        'Accepted': 'green',
        'Approved': 'green',
        'Rejected': 'red',
        'rejected': 'red',
        'Queued Coordinator': 'purple',
        'Queued HOD': 'purple',
    }
    return colors.get(status, 'gray')


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


@app.route('/api/departments/by-code/<string:code>', methods=['GET'])
def get_department_by_code(code):
    """Get department by code"""
    dept = Department.query.filter(func.lower(Department.code) == func.lower(code)).first()
    if not dept:
        return jsonify({"error": "Department not found"}), 404
    return jsonify(dept.to_dict())


@app.route('/api/departments/<int:dept_id>/hod', methods=['GET'])
def get_department_hod(dept_id):
    """Get HOD information for a specific department"""
    try:
        dept = Department.query.get(dept_id)
        if not dept:
            return jsonify({"error": "Department not found"}), 404
        
        # Find HOD assigned to this department (must have HOD role)
        hod_role = Role.query.filter_by(name='HOD').first()
        hod_user = None
        
        if hod_role:
            hod_user = User.query.filter_by(
                assigned_department_id=dept_id,
                role_id=hod_role.id,
                is_active=True
            ).first()
        
        # Also try to get phone from legacy HOD table
        hod_phone = None
        legacy_hod = HOD.query.filter(
            db.func.lower(HOD.department) == db.func.lower(dept.name)
        ).first()
        if legacy_hod:
            # Check if there's a phone in the data field (if applicable)
            pass
        
        if not hod_user:
            # If no User-based HOD, try legacy HOD table
            if legacy_hod:
                return jsonify({
                    "id": legacy_hod.id,
                    "full_name": legacy_hod.name,
                    "phone": getattr(legacy_hod, 'phone', None) or "Not Available",
                    "email": legacy_hod.email,
                    "employee_id": legacy_hod.employee_id,
                    "department_id": dept_id,
                    "department_name": dept.name,
                    "is_active": True
                })
            # No HOD found at all
            return jsonify({
                "id": None,
                "full_name": f"HOD - {dept.name}",
                "phone": "Not Assigned",
                "email": "Not Assigned",
                "department_id": dept_id,
                "department_name": dept.name
            })
        
        return jsonify({
            "id": hod_user.id,
            "full_name": hod_user.full_name,
            "phone": hod_user.phone or (getattr(legacy_hod, 'phone', None) if legacy_hod else None) or "Not Available",
            "email": hod_user.email,
            "employee_id": hod_user.employee_id,
            "department_id": dept_id,
            "department_name": dept.name,
            "is_active": hod_user.is_active
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_program_to_department_mapping(program_name):
    """Get department name for a program from database"""
    mapping = ProgramDepartmentMapping.query.filter(
        func.lower(ProgramDepartmentMapping.program_name) == func.lower(program_name)
    ).first()
    return mapping.department_name if mapping else program_name


@app.route('/api/departments/<path:dept_name>/hod', methods=['GET'])
def get_department_hod_by_name(dept_name):
    """Get HOD information for a department by name or program name"""
    try:
        # If dept_name is numeric, look up department by ID
        if dept_name.isdigit():
            dept_id = int(dept_name)
            dept = Department.query.get(dept_id)
            if dept:
                dept_name = dept.name  # Use actual department name
            else:
                return jsonify({"error": "Department not found"}), 404
        
        # First check if this is a program name that needs mapping (from database)
        mapped_dept = get_program_to_department_mapping(dept_name)
        
        # DSAI umbrella variants for flexible matching
        dsai_variants = ['data science & ai', 'data science and ai', 'ds & ai', 'ds&ai', 'dsai', 
                         'artificial intelligence', 'b.sc.-honours(ai)', 'ai']
        
        def is_dsai(name):
            name_lower = name.lower()
            return any(v in name_lower or name_lower in v for v in dsai_variants)
        
        # Try to find HOD directly in hods table by department name
        hod = HOD.query.filter(
            (func.lower(HOD.department) == func.lower(mapped_dept)) | 
            (func.lower(HOD.department) == func.lower(dept_name))
        ).first()
        
        # If not found and this looks like DSAI, try DSAI code
        if not hod and is_dsai(dept_name):
            hod = HOD.query.filter(
                (func.lower(HOD.department) == 'dsai') |
                (func.lower(HOD.department).like('%data science%')) |
                (func.lower(HOD.department).like('%ai%'))
            ).first()
        
        if hod:
            return jsonify({
                "id": hod.id,
                "full_name": hod.name,
                "phone": getattr(hod, 'phone', None) or "Not Available",
                "email": hod.email,
                "employee_id": hod.employee_id,
                "department_name": hod.department
            })
        
        # If not found, try to find department first then look for HOD user
        dept = Department.query.filter(
            (func.lower(Department.name) == func.lower(mapped_dept)) | 
            (func.lower(Department.name) == func.lower(dept_name)) |
            (func.lower(Department.code) == func.lower(dept_name))
        ).first()
        
        if dept:
            # Find HOD assigned to this department
            hod_role = Role.query.filter_by(name='HOD').first()
            if hod_role:
                hod_user = User.query.filter_by(
                    assigned_department_id=dept.id,
                    role_id=hod_role.id,
                    is_active=True
                ).first()
                if hod_user:
                    return jsonify({
                        "id": hod_user.id,
                        "full_name": hod_user.full_name,
                        "phone": hod_user.phone or "Not Available",
                        "email": hod_user.email,
                        "employee_id": hod_user.employee_id,
                        "department_id": dept.id,
                        "department_name": dept.name
                    })
        
        # Return not found message
        return jsonify({
            "id": None,
            "full_name": "Not Assigned",
            "phone": "Not Assigned",
            "email": "Not Assigned",
            "department_name": dept_name
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== CREATOR MANAGEMENT APIs ====================

# Program-Department Mappings CRUD (No auth - accessed from admin console)
@app.route('/api/creator/program-mappings', methods=['GET'])
def get_program_mappings():
    """Get all program-to-department mappings"""
    mappings = ProgramDepartmentMapping.query.order_by(ProgramDepartmentMapping.program_name).all()
    return jsonify([m.to_dict() for m in mappings])


@app.route('/api/creator/program-mappings', methods=['POST'])
def create_program_mapping():
    """Create a new program-to-department mapping"""
    payload = request.get_json(silent=True) or {}
    program_name = payload.get('programName', '').strip()
    department_name = payload.get('departmentName', '').strip()
    
    if not program_name or not department_name:
        return jsonify({"error": "Program name and department name are required"}), 400
    
    # Check if mapping already exists
    existing = ProgramDepartmentMapping.query.filter(
        func.lower(ProgramDepartmentMapping.program_name) == func.lower(program_name)
    ).first()
    if existing:
        return jsonify({"error": "Mapping for this program already exists"}), 409
    
    mapping = ProgramDepartmentMapping(
        program_name=program_name,
        department_name=department_name
    )
    db.session.add(mapping)
    db.session.commit()
    
    return jsonify({"success": True, "mapping": mapping.to_dict()}), 201


@app.route('/api/creator/program-mappings/<int:mapping_id>', methods=['PUT'])
def update_program_mapping(mapping_id):
    """Update a program-to-department mapping"""
    mapping = ProgramDepartmentMapping.query.get(mapping_id)
    if not mapping:
        return jsonify({"error": "Mapping not found"}), 404
    
    payload = request.get_json(silent=True) or {}
    if 'programName' in payload:
        mapping.program_name = payload['programName'].strip()
    if 'departmentName' in payload:
        mapping.department_name = payload['departmentName'].strip()
    
    mapping.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({"success": True, "mapping": mapping.to_dict()})


@app.route('/api/creator/program-mappings/<int:mapping_id>', methods=['DELETE'])
def delete_program_mapping(mapping_id):
    """Delete a program-to-department mapping"""
    mapping = ProgramDepartmentMapping.query.get(mapping_id)
    if not mapping:
        return jsonify({"error": "Mapping not found"}), 404
    
    db.session.delete(mapping)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Mapping deleted"})


# HODs Management CRUD (No auth - accessed from admin console)
@app.route('/api/creator/manage-hods', methods=['GET'])
def get_all_hods():
    """Get all HODs from the hods table"""
    hods = HOD.query.order_by(HOD.department).all()
    return jsonify([h.to_dict() for h in hods])


@app.route('/api/creator/manage-hods', methods=['POST'])
def create_hod():
    """Create a new HOD"""
    payload = request.get_json(silent=True) or {}
    name = payload.get('name', '').strip()
    email = payload.get('email', '').strip().lower()
    employee_id = payload.get('employeeId', '').strip()
    department = payload.get('department', '').strip()
    
    if not all([name, email, employee_id, department]):
        return jsonify({"error": "All fields (name, email, employeeId, department) are required"}), 400
    
    # Check if HOD already exists
    existing = HOD.query.filter((HOD.email == email) | (HOD.employee_id == employee_id)).first()
    if existing:
        return jsonify({"error": "HOD with this email or employee ID already exists"}), 409
    
    hod = HOD(name=name, email=email, employee_id=employee_id, department=department)
    db.session.add(hod)
    db.session.commit()
    
    return jsonify({"success": True, "hod": hod.to_dict()}), 201


@app.route('/api/creator/manage-hods/<int:hod_id>', methods=['PUT'])
def update_hod(hod_id):
    """Update an HOD"""
    hod = HOD.query.get(hod_id)
    if not hod:
        return jsonify({"error": "HOD not found"}), 404
    
    payload = request.get_json(silent=True) or {}
    if 'name' in payload:
        hod.name = payload['name'].strip()
    if 'email' in payload:
        hod.email = payload['email'].strip().lower()
    if 'employeeId' in payload:
        hod.employee_id = payload['employeeId'].strip()
    if 'department' in payload:
        hod.department = payload['department'].strip()
    
    hod.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({"success": True, "hod": hod.to_dict()})


@app.route('/api/creator/manage-hods/<int:hod_id>', methods=['DELETE'])
def delete_hod(hod_id):
    """Delete an HOD"""
    hod = HOD.query.get(hod_id)
    if not hod:
        return jsonify({"error": "HOD not found"}), 404
    
    db.session.delete(hod)
    db.session.commit()
    
    return jsonify({"success": True, "message": "HOD deleted"})


# Departments Management CRUD (No auth - accessed from admin console)
@app.route('/api/creator/manage-departments', methods=['GET'])
def get_all_departments():
    """Get all departments"""
    departments = Department.query.order_by(Department.name).all()
    return jsonify([d.to_dict() for d in departments])


@app.route('/api/creator/manage-departments', methods=['POST'])
def create_department():
    """Create a new department"""
    payload = request.get_json(silent=True) or {}
    name = payload.get('name', '').strip()
    code = payload.get('code', '').strip()
    description = payload.get('description', '').strip()
    
    if not name:
        return jsonify({"error": "Department name is required"}), 400
    
    # Check if department already exists
    existing = Department.query.filter((func.lower(Department.name) == func.lower(name)) | (func.lower(Department.code) == func.lower(code))).first()
    if existing:
        return jsonify({"error": "Department with this name or code already exists"}), 409
    
    dept = Department(name=name, code=code, description=description)
    db.session.add(dept)
    db.session.commit()
    
    return jsonify({"success": True, "department": dept.to_dict()}), 201


@app.route('/api/creator/manage-departments/<int:dept_id>', methods=['PUT'])
def update_department(dept_id):
    """Update a department"""
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"error": "Department not found"}), 404
    
    payload = request.get_json(silent=True) or {}
    if 'name' in payload:
        dept.name = payload['name'].strip()
    if 'code' in payload:
        dept.code = payload['code'].strip()
    if 'description' in payload:
        dept.description = payload['description'].strip()
    
    db.session.commit()
    
    return jsonify({"success": True, "department": dept.to_dict()})


@app.route('/api/creator/manage-departments/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    """Delete a department"""
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"error": "Department not found"}), 404
    
    db.session.delete(dept)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Department deleted"})


@app.route('/api/activities/coordinator/<string:activity_name>', methods=['GET'])
def get_activity_coordinator_by_name(activity_name):
    """Get coordinator for a specific activity by name"""
    try:
        # Search for coordinator in User table
        coordinator = User.query.filter(
            (func.lower(User.assigned_activity_name) == func.lower(activity_name)) & 
            (User.is_active == True)
        ).first()
        
        if not coordinator:
            # Fallback: check Role and Name (some might be named like "NCC Coordinator")
            coordinator = User.query.filter(
                (func.lower(User.full_name).like(func.lower(f"%{activity_name}%"))) & 
                (User.is_active == True)
            ).first()

        if not coordinator:
            return jsonify({
                "full_name": "Not Assigned",
                "phone": "N/A",
                "email": "N/A"
            }), 200

        return jsonify({
            "id": coordinator.id,
            "full_name": coordinator.full_name,
            "phone": coordinator.phone or "Not Available",
            "email": coordinator.email,
            "employee_id": coordinator.employee_id,
            "assigned_activity": coordinator.assigned_activity_name
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/departments/<int:dept_id>/classes', methods=['GET'])
def get_department_classes(dept_id):
    """Get all classes for a specific department"""
    try:
        dept = Department.query.get(dept_id)
        if not dept:
            return jsonify({"error": "Department not found"}), 404
        
        # Create mapping of department codes to activity department names
        # Updated mapping to use DSAI (AI and Data Science)
        dept_code_map = {
            'BA': 'B.A.',
            'BCom': 'B.Com.',
            'BBA': 'B.B.A.',
            'BCA': 'B.C.A.',
            'BSc': 'B.Sc.',
            'DSAI': 'AI and Data Science'
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
        # Updated mapping to use DSAI (AI and Data Science)
        dept_code_map = {
            'BA': 'B.A.',
            'BCom': 'B.Com.',
            'BBA': 'B.B.A.',
            'BCA': 'B.C.A.',
            'BSc': 'B.Sc.',
            'DSAI': 'AI and Data Science'
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
            # Case-insensitive activity name filtering
            query = query.filter(db.func.lower(Registration.activity_name) == activity.lower())
        if department:
            query = query.filter_by(department=department)
        
        # If coordinator_email provided, filter by their activity role
        if coordinator_email:
            coordinator = Coordinator.query.filter_by(email=coordinator_email).first()
            if coordinator:
                query = query.filter(db.func.lower(Registration.activity_name) == coordinator.role.lower())
        
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
            
            total_slots_val = sub_activity.total_slots if sub_activity.total_slots is not None else 0
            filled_slots_val = sub_activity.filled_slots if sub_activity.filled_slots is not None else 0
            available_slots = total_slots_val - filled_slots_val
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

# NEW: Get students who are ACCEPTED into activities (for Events Management)
@app.route('/api/activity-members', methods=['GET'])
def get_activity_members():
    """
    Returns students who have been fully accepted into activities.
    Only students who:
    1. Registered through the website
    2. Completed their profile
    3. Were accepted (hod_approved/Accepted status) into an activity
    
    Query params:
    - activity: Filter by specific activity name/category (e.g., 'NCC', 'NSS')
    - sub_activity_id: Filter by specific sub-activity
    - department: Filter by student's department (for HOD view)
    """
    try:
        activity = request.args.get('activity')
        sub_activity_id = request.args.get('sub_activity_id')
        department = request.args.get('department')
        
        # Query CourseRegistrations with accepted status (primary source)
        accepted_statuses = ['Accepted', 'hod_approved']
        
        query = CourseRegistration.query.filter(
            CourseRegistration.status.in_(accepted_statuses)
        )
        
        if activity:
            # Filter by activity_category (main activity like NCC) OR activity_name
            query = query.filter(
                (CourseRegistration.activity_category == activity) |
                (CourseRegistration.activity_name == activity)
            )
        if sub_activity_id:
            query = query.filter(CourseRegistration.sub_activity_id == int(sub_activity_id))
        if department:
            query = query.filter(CourseRegistration.department == department)
        
        registrations = query.order_by(CourseRegistration.student_name.asc()).all()
        
        # Format response with student details
        members = []
        for reg in registrations:
            # Get sub-activity details if available
            sub_activity = None
            if reg.sub_activity_id:
                sub_activity = SubActivity.query.get(reg.sub_activity_id)
            
            member = {
                'id': reg.admission_id,
                'name': reg.student_name,
                'email': reg.data.get('email') if reg.data else None,
                'department': reg.department,
                'activity': reg.activity_category or reg.activity_name,
                'activityName': reg.activity_name,
                'activityCategory': reg.activity_category,
                'subActivity': sub_activity.sub_activity_name if sub_activity else (reg.activity_name if reg.activity_category else None),
                'subActivityId': reg.sub_activity_id,
                'status': reg.status,
                'acceptedAt': reg.last_updated.isoformat() if reg.last_updated else None,
                'registrationId': reg.id,
                # Include additional data from registration
                'course': reg.course,
                'year': reg.data.get('year') if reg.data else None,
                'phone': reg.data.get('phone') if reg.data else None,
            }
            members.append(member)
        
        # Also check old Registration table as fallback
        old_query = Registration.query.filter(
            Registration.status.in_(accepted_statuses)
        )
        
        if activity:
            old_query = old_query.filter(db.func.lower(Registration.activity_name) == activity.lower())
        if sub_activity_id:
            old_query = old_query.filter(Registration.sub_activity_id == int(sub_activity_id))
        if department:
            old_query = old_query.filter(Registration.department == department)
            
        old_registrations = old_query.order_by(Registration.student_name.asc()).all()
        
        existing_ids = {m['id'] for m in members}
        for reg in old_registrations:
            if reg.admission_id in existing_ids:
                continue
                
            sub_activity = None
            if reg.sub_activity_id:
                sub_activity = SubActivity.query.get(reg.sub_activity_id)
            
            member = {
                'id': reg.admission_id,
                'name': reg.student_name,
                'email': reg.student_email,
                'department': reg.department,
                'activity': reg.activity_name,
                'subActivity': sub_activity.sub_activity_name if sub_activity else None,
                'subActivityId': reg.sub_activity_id,
                'status': reg.status,
                'acceptedAt': reg.updated_at.isoformat() if reg.updated_at else None,
                'registrationId': reg.id,
                'course': reg.data.get('course') if reg.data else None,
                'year': reg.data.get('year') if reg.data else None,
                'phone': reg.data.get('phone') if reg.data else None,
            }
            members.append(member)
        
        return jsonify(members)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# NEW: Get activity summary with member counts (for Activity Head / Coordinator dashboard)
@app.route('/api/activity-summary', methods=['GET'])
def get_activity_summary():
    """
    Returns a summary of all activities with their accepted student counts.
    Useful for Activity Heads and Coordinators to see their member list.
    """
    try:
        coordinator_email = request.args.get('coordinator_email')
        
        # Get all activities with accepted registrations
        activities_data = {}
        
        accepted_statuses = ['Accepted', 'hod_approved']
        
        # Query CourseRegistrations (primary source)
        course_regs = CourseRegistration.query.filter(
            CourseRegistration.status.in_(accepted_statuses)
        ).all()
        
        for reg in course_regs:
            # Use activity_category as the main activity name
            activity_name = reg.activity_category or reg.activity_name
            if not activity_name:
                continue
                
            if activity_name not in activities_data:
                activities_data[activity_name] = {
                    'name': activity_name,
                    'totalMembers': 0,
                    'subActivities': {}
                }
            
            activities_data[activity_name]['totalMembers'] += 1
            
            # Track sub-activity breakdown
            sub_activity_name = reg.activity_name if reg.activity_category else None
            if sub_activity_name and sub_activity_name != reg.activity_category:
                if sub_activity_name not in activities_data[activity_name]['subActivities']:
                    activities_data[activity_name]['subActivities'][sub_activity_name] = {
                        'id': reg.sub_activity_id,
                        'name': sub_activity_name,
                        'count': 0,
                        'coordinatorEmail': None
                    }
                activities_data[activity_name]['subActivities'][sub_activity_name]['count'] += 1
        
        # Also check old Registration table as fallback
        old_registrations = Registration.query.filter(
            Registration.status.in_(accepted_statuses)
        ).all()
        
        for reg in old_registrations:
            activity_name = reg.activity_name
            if not activity_name:
                continue
                
            if activity_name not in activities_data:
                activities_data[activity_name] = {
                    'name': activity_name,
                    'totalMembers': 0,
                    'subActivities': {}
                }
            
            activities_data[activity_name]['totalMembers'] += 1
            
            # Track sub-activity breakdown
            if reg.sub_activity_id:
                sub = SubActivity.query.get(reg.sub_activity_id)
                if sub:
                    sub_name = sub.sub_activity_name
                    if sub_name not in activities_data[activity_name]['subActivities']:
                        activities_data[activity_name]['subActivities'][sub_name] = {
                            'id': sub.id,
                            'name': sub_name,
                            'count': 0,
                            'coordinatorEmail': sub.coordinator_email
                        }
                    activities_data[activity_name]['subActivities'][sub_name]['count'] += 1
        
        # Convert to list and filter by coordinator if specified
        result = []
        for activity_name, data in activities_data.items():
            data['subActivities'] = list(data['subActivities'].values())
            
            # Filter by coordinator if email provided
            if coordinator_email:
                # Check if coordinator manages this activity or any sub-activity
                is_coordinator = any(
                    sub.get('coordinatorEmail') == coordinator_email 
                    for sub in data['subActivities']
                )
                if is_coordinator:
                    result.append(data)
            else:
                result.append(data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# NEW: Dedicated endpoint for coordinator activities (filters out academic programs)
@app.route('/api/coordinator-activities', methods=['GET'])
def coordinator_activities():
    """Returns unique coordinator activities (NCC, Sports, Yoga, Gym, etc.) from sub-activities table.
    These are the REAL activities, not academic programs."""
    try:
        # Get distinct activity names from sub-activities table
        subs = SubActivity.query.all()
        
        # Build unique activities map with head info
        activity_map = {}
        for sub in subs:
            if sub.activity_name not in activity_map:
                activity_map[sub.activity_name] = {
                    'name': sub.activity_name,
                    'activityHeadName': sub.activity_head_name or 'Not Assigned',
                    'activityHeadPhone': sub.activity_head_phone or '',
                    'subActivityCount': 0
                }
            activity_map[sub.activity_name]['subActivityCount'] += 1
        
        activities = list(activity_map.values())
        return jsonify({
            'activities': activities,
            'total': len(activities),
            'statistics': {
                'totalSubActivities': len(subs),
                'activitiesBreakdown': {a['name']: a['subActivityCount'] for a in activities}
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sub-activities', methods=['GET', 'POST'])
def sub_activities():
    if request.method == 'GET':
        activity_name = request.args.get('activity')
        coordinator_email = request.args.get('coordinatorEmail')
        show_available_only = request.args.get('availableOnly', '').lower() == 'true'
        
        query = SubActivity.query
        
        if activity_name:
            # Case-insensitive activity name filtering
            query = query.filter(db.func.lower(SubActivity.activity_name) == activity_name.lower())
        if coordinator_email:
            query = query.filter_by(coordinator_email=coordinator_email)
        if show_available_only:
            # Only show active sub-activities with available slots
            query = query.filter(SubActivity.is_active == True)
        
        subs = query.all()
        
        # Filter out full activities if showing available only
        if show_available_only:
            def get_available(s):
                total = s.total_slots if s.total_slots is not None else 0
                filled = s.filled_slots if s.filled_slots is not None else 0
                return (total - filled) > 0
            subs = [s for s in subs if get_available(s)]
        
        return jsonify([s.to_dict() for s in subs])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        activity_name = payload.get('activityName', '').strip().upper()  # Convert to UPPERCASE
        sub_activity_name = payload.get('subActivityName', '').strip()
        coordinator_email = payload.get('coordinatorEmail', '').strip()
        total_slots = payload.get('totalSlots', 0)
        is_active = payload.get('isActive', True)
        data = payload.get('data', {})
        
        # Additional fields for activity head and sub-activity lead
        activity_head_name = payload.get('activityHeadName', '').strip()
        activity_head_phone = payload.get('activityHeadPhone', '').strip()
        sub_activity_lead_name = payload.get('subActivityLeadName', '').strip()
        sub_activity_lead_phone = payload.get('subActivityLeadPhone', '').strip()
        
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
                data=data,
                activity_head_name=activity_head_name,
                activity_head_phone=activity_head_phone,
                sub_activity_lead_name=sub_activity_lead_name,
                sub_activity_lead_phone=sub_activity_lead_phone
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
            sub.activity_name = payload['activityName'].strip().upper()  # Convert to UPPERCASE
        if 'subActivityName' in payload:
            sub.sub_activity_name = payload['subActivityName'].strip()
        if 'coordinatorEmail' in payload:
            sub.coordinator_email = payload['coordinatorEmail'].strip() if payload['coordinatorEmail'] else ''
        if 'totalSlots' in payload:
            sub.total_slots = payload['totalSlots']
        if 'isActive' in payload:
            sub.is_active = payload['isActive']
        if 'subActivityLeadName' in payload:
            sub.sub_activity_lead_name = payload['subActivityLeadName'].strip() if payload['subActivityLeadName'] else ''
        if 'subActivityLeadPhone' in payload:
            sub.sub_activity_lead_phone = payload['subActivityLeadPhone'].strip() if payload['subActivityLeadPhone'] else ''
        if 'activityHeadName' in payload:
            sub.activity_head_name = payload['activityHeadName'].strip() if payload['activityHeadName'] else ''
        if 'activityHeadPhone' in payload:
            sub.activity_head_phone = payload['activityHeadPhone'].strip() if payload['activityHeadPhone'] else ''
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


@app.route('/api/sub-activities/resolve', methods=['GET'])
def resolve_sub_activity():
    """Resolve a sub-activity by activityName + subActivityName.
    Useful when the frontend has a client-side placeholder ID.
    Query params: activityName, subActivityName
    """
    activity_name = (request.args.get('activityName') or '').strip()
    sub_activity_name = (request.args.get('subActivityName') or '').strip()
    if not activity_name or not sub_activity_name:
        return jsonify({"error": "activityName and subActivityName are required"}), 400

    try:
        sub = SubActivity.query.filter(
            db.func.lower(SubActivity.activity_name) == activity_name.lower(),
            db.func.lower(SubActivity.sub_activity_name) == sub_activity_name.lower()
        ).first()
        if not sub:
            return jsonify({"error": "Sub-activity not found"}), 404
        return jsonify(sub.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ STUDENT APPLICATION STATUS & VALIDATION APIs ============

@app.route('/api/student/<string:admission_id>/application-status', methods=['GET'])
def get_student_application_status(admission_id):
    """
    Get the current application status for a student.
    Returns the active/pending application if exists, or allows new application.
    """
    try:
        # Find student's registrations, ordered by most recent
        registrations = CourseRegistration.query.filter_by(
            admission_id=admission_id.upper()
        ).order_by(CourseRegistration.created_at.desc()).all()
        
        if not registrations:
            return jsonify({
                "hasActiveApplication": False,
                "canApply": True,
                "message": "No applications found. You can submit a new application.",
                "applications": []
            })
        
        # Check for active (non-rejected) applications
        active_statuses = ['Pending Coordinator', 'Pending HOD', 'Accepted', 'Approved', 'coordinator_approved', 'hod_approved']
        rejected_statuses = ['Rejected', 'rejected']
        
        active_apps = [r for r in registrations if r.status in active_statuses]
        rejected_apps = [r for r in registrations if r.status in rejected_statuses]
        
        if active_apps:
            latest = active_apps[0]
            # Determine detailed status
            coordinator_status = 'waiting'
            hod_status = 'waiting'
            
            if latest.status in ['Pending Coordinator']:
                coordinator_status = 'waiting'
                hod_status = 'waiting'
            elif latest.status in ['Pending HOD', 'coordinator_approved']:
                coordinator_status = 'approved'
                hod_status = 'waiting'
            elif latest.status in ['Accepted', 'Approved', 'hod_approved']:
                coordinator_status = 'approved'
                hod_status = 'approved'
            
            return jsonify({
                "hasActiveApplication": True,
                "canApply": False,
                "message": "You already have an active application. Please wait for approval.",
                "currentApplication": latest.to_dict(),
                "coordinatorStatus": coordinator_status,
                "hodStatus": hod_status,
                "statusMessage": get_status_message(latest.status),
                "applications": [r.to_dict() for r in registrations]
            })
        
        # All applications are rejected - allow new application
        return jsonify({
            "hasActiveApplication": False,
            "canApply": True,
            "message": "Your previous application was rejected. You can apply for a different activity.",
            "rejectedApplications": [r.to_dict() for r in rejected_apps],
            "applications": [r.to_dict() for r in registrations]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_status_message(status):
    """Helper to get user-friendly status message"""
    status_messages = {
        'Pending Coordinator': 'Waiting for Coordinator approval',
        'Pending HOD': 'Coordinator approved. Waiting for HOD approval',
        'coordinator_approved': 'Coordinator approved. Waiting for HOD approval',
        'Accepted': 'Application fully approved!',
        'Approved': 'Application fully approved!',
        'hod_approved': 'Application fully approved!',
        'Rejected': 'Application rejected',
        'rejected': 'Application rejected'
    }
    return status_messages.get(status, 'Status unknown')


@app.route('/api/student/<string:admission_id>/can-apply', methods=['GET'])
def check_student_can_apply(admission_id):
    """
    Quick check if student can submit a new application.
    Used before showing the registration form.
    """
    try:
        # Check for any non-rejected applications
        active_statuses = ['Pending Coordinator', 'Pending HOD', 'Accepted', 'Approved', 'coordinator_approved', 'hod_approved']
        
        active_count = CourseRegistration.query.filter(
            CourseRegistration.admission_id == admission_id.upper(),
            CourseRegistration.status.in_(active_statuses)
        ).count()
        
        if active_count > 0:
            return jsonify({
                "canApply": False,
                "reason": "You already have an active application pending or approved.",
                "activeCount": active_count
            })
        
        return jsonify({
            "canApply": True,
            "reason": "You can submit a new application.",
            "activeCount": 0
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/course-registrations/<int:reg_id>/approve', methods=['POST'])
def approve_course_registration(reg_id):
    """
    Unified approval endpoint for both Coordinator and HOD.
    Automatically determines the next step based on current status.
    """
    reg = CourseRegistration.query.get(reg_id)
    if not reg:
        return jsonify({"error": "Registration not found"}), 404
    
    payload = request.get_json(silent=True) or {}
    action = payload.get('action', '').lower()  # 'approve' or 'reject'
    reason = payload.get('reason', '')
    approver_type = payload.get('approverType', '')  # 'coordinator' or 'hod'
    approver_email = payload.get('approverEmail', '')
    
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Action must be 'approve' or 'reject'"}), 400
    
    # Store old status to check if we need to decrement slots
    old_status = reg.status
    
    try:
        if action == 'approve':
            if reg.status in ['Pending Coordinator', 'Queued Coordinator', 'pending']:
                # Coordinator approval
                reg.status = 'Pending HOD'
                if reg.data:
                    reg.data['coordinatorApprovedAt'] = datetime.utcnow().isoformat()
                    reg.data['coordinatorApprovedBy'] = approver_email
            elif reg.status in ['Pending HOD', 'Queued HOD', 'coordinator_approved']:
                # HOD approval - final approval
                reg.status = 'Accepted'
                if reg.data:
                    reg.data['hodApprovedAt'] = datetime.utcnow().isoformat()
                    reg.data['hodApprovedBy'] = approver_email
                
                # Update sub-activity slot count
                if reg.sub_activity_id:
                    sub = SubActivity.query.get(reg.sub_activity_id)
                    if sub:
                        sub.filled_slots = (sub.filled_slots or 0) + 1
                        print(f"[INFO] Incremented slot count for sub-activity {sub.id}. New filled: {sub.filled_slots}/{sub.total_slots}")
                        if sub.filled_slots >= sub.total_slots:
                            sub.is_active = False
            else:
                return jsonify({"error": f"Cannot approve registration with status: {reg.status}"}), 400
        else:
            # Reject - if was previously Accepted, decrement slot count
            if old_status == 'Accepted' and reg.sub_activity_id:
                sub = SubActivity.query.get(reg.sub_activity_id)
                if sub and sub.filled_slots > 0:
                    sub.filled_slots -= 1
                    print(f"[INFO] Decremented slot count for sub-activity {sub.id}. New filled: {sub.filled_slots}/{sub.total_slots}")
                    # Reactivate if it was full and now has space
                    if sub.filled_slots < sub.total_slots:
                        sub.is_active = True
            
            reg.status = 'Rejected'
            if reg.data:
                reg.data['rejectedAt'] = datetime.utcnow().isoformat()
                reg.data['rejectedBy'] = approver_email
                reg.data['rejectionReason'] = reason
        
        reg.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Registration {action}d successfully",
            "registration": reg.to_dict()
        })
        
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
            query = query.filter(CourseRegistration.data['branch'] == branch)
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
    
    # Store old status to check if we need to decrement slots
    old_status = reg.status
    
    try:
        if action == 'approve':
            reg.hod_status = 'approved'
            reg.status = 'hod_approved'  # Fully approved
            
            # Update sub-activity slot count if linked
            if reg.sub_activity_id:
                sub_activity = SubActivity.query.get(reg.sub_activity_id)
                if sub_activity:
                    sub_activity.filled_slots = (sub_activity.filled_slots or 0) + 1
                    print(f"[INFO] Incremented slot count for sub-activity {sub_activity.id}. New filled: {sub_activity.filled_slots}/{sub_activity.total_slots}")
                    # Deactivate if full
                    if sub_activity.filled_slots >= sub_activity.total_slots:
                        sub_activity.is_active = False
        else:
            # If registration was previously approved, decrement slot count
            if old_status == 'hod_approved' and reg.sub_activity_id:
                sub_activity = SubActivity.query.get(reg.sub_activity_id)
                if sub_activity and sub_activity.filled_slots > 0:
                    sub_activity.filled_slots -= 1
                    print(f"[INFO] Decremented slot count for sub-activity {sub_activity.id}. New filled: {sub_activity.filled_slots}/{sub_activity.total_slots}")
                    if sub_activity.filled_slots < sub_activity.total_slots:
                        sub_activity.is_active = True
            
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
        
        # Store old status to handle slot count updates
        old_status = reg.status
        new_status = payload.get('status')
        
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
        
        # Handle slot count changes based on status transitions
        accepted_statuses = ['Accepted', 'hod_approved', 'Approved']
        
        # If transitioning TO accepted status (and wasn't already accepted)
        if new_status in accepted_statuses and old_status not in accepted_statuses:
            if reg.sub_activity_id:
                sub = SubActivity.query.get(reg.sub_activity_id)
                if sub:
                    sub.filled_slots = (sub.filled_slots or 0) + 1
                    print(f"[INFO] Status changed to {new_status}. Incremented slot for sub-activity {sub.id}. New filled: {sub.filled_slots}/{sub.total_slots}")
                    # Deactivate if full
                    if sub.filled_slots >= sub.total_slots:
                        sub.is_active = False
                        print(f"[INFO] Sub-activity {sub.id} is now FULL")
        
        # If transitioning FROM accepted status (to rejected or other)
        elif old_status in accepted_statuses and new_status not in accepted_statuses:
            if reg.sub_activity_id:
                sub = SubActivity.query.get(reg.sub_activity_id)
                if sub and sub.filled_slots > 0:
                    sub.filled_slots -= 1
                    print(f"[INFO] Status changed from {old_status} to {new_status}. Decremented slot for sub-activity {sub.id}. New filled: {sub.filled_slots}/{sub.total_slots}")
                    # Reactivate if was full and now has space
                    if sub.filled_slots < sub.total_slots:
                        sub.is_active = True
        
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
            # If registration was accepted, decrement the slot count
            if reg.status == 'Accepted' and reg.sub_activity_id:
                sub = SubActivity.query.get(reg.sub_activity_id)
                if sub and sub.filled_slots > 0:
                    sub.filled_slots -= 1
                    # Reactivate if it was full and now has space
                    if sub.filled_slots < sub.total_slots:
                        sub.is_active = True
                    print(f"[INFO] Decremented slot count for sub-activity {sub.id}. New filled: {sub.filled_slots}")
            
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
            # Parse end date if provided
            event_end_date_obj = None
            if payload.get('eventEndDate'):
                try:
                    event_end_date_obj = parser.parse(payload.get('eventEndDate'))
                except:
                    pass
            
            # Determine if approval is required (student coordinator creates event)
            created_by_role = payload.get('createdByRole', 'faculty_coordinator')
            requires_approval = created_by_role == 'student_coordinator'
            event_status = 'pending_approval' if requires_approval else payload.get('eventStatus', 'approved')
            
            new_event = Event(
                event_name=event_name,
                activity_name=activity_name,
                sub_activity_id=payload.get('subActivityId'),
                coordinator_email=payload.get('coordinatorEmail', '').strip(),
                event_date=event_date_obj,
                event_end_date=event_end_date_obj,
                event_time=payload.get('eventTime', ''),
                location=payload.get('location', ''),
                description=payload.get('description', ''),
                assigned_students=payload.get('assignedStudents', []),
                is_active=payload.get('isActive', True),
                event_type=payload.get('eventType', 'college'),
                event_status=event_status,
                created_by_role=created_by_role,
                requires_approval=requires_approval,
                required_students=payload.get('requiredStudents')
            )
            db.session.add(new_event)
            db.session.commit()
            
            # If requires approval, create notification for faculty coordinator
            if requires_approval:
                # Find the faculty coordinator for this activity
                sub_activity = SubActivity.query.get(payload.get('subActivityId')) if payload.get('subActivityId') else None
                if sub_activity and sub_activity.activity_head_name:
                    notification = Notification(
                        recipient_id=sub_activity.coordinator_email or activity_name,
                        recipient_type='faculty',
                        title='New Event Pending Approval',
                        message=f'Student coordinator has created event "{event_name}" that requires your approval.',
                        notification_type='approval_request',
                        related_event_id=new_event.id
                    )
                    db.session.add(notification)
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
        if 'eventEndDate' in payload:
            try:
                from dateutil import parser
                event.event_end_date = parser.parse(payload['eventEndDate']) if payload['eventEndDate'] else None
            except:
                pass
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
        if 'eventType' in payload:
            event.event_type = payload['eventType']
        if 'eventStatus' in payload:
            event.event_status = payload['eventStatus']
        if 'requiredStudents' in payload:
            event.required_students = payload['requiredStudents']
        
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


# ============================================================================
# EVENT PARTICIPANTS & ASSIGNMENT ENDPOINTS
# ============================================================================

@app.route('/api/events/<int:event_id>/participants', methods=['GET', 'POST'])
def event_participants(event_id):
    """Get or add participants to an event"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    if request.method == 'GET':
        participants = EventParticipant.query.filter_by(event_id=event_id).all()
        return jsonify([p.to_dict() for p in participants])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        students = payload.get('students', [])
        assigned_by = payload.get('assignedBy', '')
        send_notifications = payload.get('sendNotifications', True)
        
        if not students:
            return jsonify({"error": "No students provided"}), 400
        
        added = []
        notifications_created = []
        
        try:
            for student in students:
                # Check if already assigned
                existing = EventParticipant.query.filter_by(
                    event_id=event_id,
                    student_admission_id=student.get('admissionId', '')
                ).first()
                
                if not existing:
                    participant = EventParticipant(
                        event_id=event_id,
                        student_admission_id=student.get('admissionId', ''),
                        student_name=student.get('name', ''),
                        student_department=student.get('department', ''),
                        assigned_by=assigned_by
                    )
                    db.session.add(participant)
                    added.append(student.get('admissionId'))
                    
                    # Create notification for student
                    if send_notifications:
                        notification = Notification(
                            recipient_id=student.get('admissionId', ''),
                            recipient_type='student',
                            title='Event Assignment',
                            message=f'You have been assigned to "{event.event_name}" on {event.event_date.strftime("%B %d, %Y") if event.event_date else "TBD"}. Location: {event.location or "TBD"}.',
                            notification_type='event_assignment',
                            related_event_id=event_id
                        )
                        db.session.add(notification)
                        notifications_created.append(student.get('admissionId'))
                        participant.notification_sent = True
            
            # Also update the legacy assigned_students JSON field
            current_assigned = event.assigned_students or []
            event.assigned_students = list(set(current_assigned + added))
            
            db.session.commit()
            return jsonify({
                "success": True,
                "added": len(added),
                "notificationsSent": len(notifications_created),
                "students": added
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/events/<int:event_id>/participants/<student_id>', methods=['DELETE'])
def remove_event_participant(event_id, student_id):
    """Remove a student from an event"""
    participant = EventParticipant.query.filter_by(
        event_id=event_id,
        student_admission_id=student_id
    ).first()
    
    if not participant:
        return jsonify({"error": "Participant not found"}), 404
    
    try:
        # Also update legacy JSON field
        event = Event.query.get(event_id)
        if event and event.assigned_students:
            event.assigned_students = [s for s in event.assigned_students if s != student_id]
        
        db.session.delete(participant)
        db.session.commit()
        return jsonify({"success": True, "message": "Participant removed"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/events/<int:event_id>/approve', methods=['POST'])
def approve_event(event_id):
    """Faculty coordinator approves a student-coordinator-created event"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    if event.event_status != 'pending_approval':
        return jsonify({"error": "Event is not pending approval"}), 400
    
    payload = request.get_json(silent=True) or {}
    approved_by = payload.get('approvedBy', '')
    action = payload.get('action', 'approve')  # 'approve' or 'reject'
    
    try:
        if action == 'approve':
            event.event_status = 'approved'
            event.approved_by = approved_by
            event.approved_at = datetime.utcnow()
            
            # Notify the student coordinator who created it
            notification = Notification(
                recipient_id=event.coordinator_email,
                recipient_type='coordinator',
                title='Event Approved',
                message=f'Your event "{event.event_name}" has been approved. You can now assign students.',
                notification_type='event_update',
                related_event_id=event_id
            )
            db.session.add(notification)
        else:
            event.event_status = 'rejected'
            reason = payload.get('reason', 'No reason provided')
            
            notification = Notification(
                recipient_id=event.coordinator_email,
                recipient_type='coordinator',
                title='Event Rejected',
                message=f'Your event "{event.event_name}" was rejected. Reason: {reason}',
                notification_type='event_update',
                related_event_id=event_id
            )
            db.session.add(notification)
        
        db.session.commit()
        return jsonify(event.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/events/<int:event_id>/attendance', methods=['GET', 'POST'])
def event_attendance(event_id):
    """Get or mark attendance for an event"""
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    if request.method == 'GET':
        participants = EventParticipant.query.filter_by(event_id=event_id).all()
        return jsonify([{
            **p.to_dict(),
            'eventName': event.event_name,
            'eventDate': event.event_date.isoformat() if event.event_date else None
        } for p in participants])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        attendance_records = payload.get('records', [])
        marked_by = payload.get('markedBy', '')
        attendance_date = payload.get('attendanceDate', datetime.utcnow().strftime('%Y-%m-%d'))
        
        try:
            for record in attendance_records:
                student_id = record.get('studentAdmissionId', '')
                status = record.get('status', 'present')
                
                # Update participant record
                participant = EventParticipant.query.filter_by(
                    event_id=event_id,
                    student_admission_id=student_id
                ).first()
                
                if participant:
                    participant.attendance_status = status
                    participant.attended_at = datetime.utcnow()
                    participant.remarks = record.get('remarks', '')
                
                # Also create an Attendance record for history
                att_record = Attendance(
                    student_admission_id=student_id,
                    student_name=record.get('studentName', participant.student_name if participant else ''),
                    activity_name=event.activity_name,
                    sub_activity_id=event.sub_activity_id,
                    event_id=event_id,
                    attendance_date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                    attendance_type='event',
                    status=status,
                    coordinator_email=marked_by,
                    remarks=f"Event: {event.event_name}"
                )
                db.session.add(att_record)
            
            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"Attendance marked for {len(attendance_records)} students"
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/events/pending-approval', methods=['GET'])
def pending_approval_events():
    """Get all events pending faculty approval"""
    activity_name = request.args.get('activity')
    
    query = Event.query.filter_by(event_status='pending_approval')
    if activity_name:
        query = query.filter_by(activity_name=activity_name)
    
    events = query.order_by(Event.created_at.desc()).all()
    return jsonify([e.to_dict() for e in events])


# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for a user"""
    recipient_id = request.args.get('recipientId')
    recipient_type = request.args.get('recipientType', 'student')
    unread_only = request.args.get('unreadOnly', 'false').lower() == 'true'
    limit = request.args.get('limit', type=int)
    
    if not recipient_id:
        return jsonify({"error": "recipientId is required"}), 400
    
    query = Notification.query.filter_by(
        recipient_id=recipient_id,
        recipient_type=recipient_type
    )
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    query = query.order_by(Notification.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    notifications = query.all()
    return jsonify([n.to_dict() for n in notifications])


@app.route('/api/notifications/unread-count', methods=['GET'])
def unread_notification_count():
    """Get count of unread notifications"""
    recipient_id = request.args.get('recipientId')
    recipient_type = request.args.get('recipientType', 'student')
    
    if not recipient_id:
        return jsonify({"error": "recipientId is required"}), 400
    
    count = Notification.query.filter_by(
        recipient_id=recipient_id,
        recipient_type=recipient_type,
        is_read=False
    ).count()
    
    return jsonify({"unreadCount": count})


@app.route('/api/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    """Mark notification(s) as read"""
    payload = request.get_json(silent=True) or {}
    notification_ids = payload.get('notificationIds', [])
    mark_all = payload.get('markAll', False)
    recipient_id = payload.get('recipientId')
    
    try:
        if mark_all and recipient_id:
            Notification.query.filter_by(
                recipient_id=recipient_id,
                is_read=False
            ).update({'is_read': True})
        elif notification_ids:
            Notification.query.filter(
                Notification.id.in_(notification_ids)
            ).update({'is_read': True}, synchronize_session=False)
        
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/api/notifications', methods=['POST'])
def create_notification():
    """Create a new notification"""
    payload = request.get_json(silent=True) or {}
    
    recipient_id = payload.get('recipientId')
    title = payload.get('title')
    message = payload.get('message')
    
    if not all([recipient_id, title, message]):
        return jsonify({"error": "recipientId, title, and message are required"}), 400
    
    try:
        notification = Notification(
            recipient_id=recipient_id,
            recipient_type=payload.get('recipientType', 'student'),
            title=title,
            message=message,
            notification_type=payload.get('notificationType', 'general'),
            related_event_id=payload.get('relatedEventId')
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify(notification.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# ============================================================================
# STUDENT EVENT ENDPOINTS
# ============================================================================

@app.route('/api/student/my-events', methods=['GET'])
def student_my_events():
    """Get events assigned to a student"""
    student_id = request.args.get('studentId')
    
    if not student_id:
        return jsonify({"error": "studentId is required"}), 400
    
    # Get events via EventParticipant
    participants = EventParticipant.query.filter_by(student_admission_id=student_id).all()
    event_ids = [p.event_id for p in participants]
    
    events = Event.query.filter(Event.id.in_(event_ids)).order_by(Event.event_date.desc()).all()
    
    result = []
    for event in events:
        participant = next((p for p in participants if p.event_id == event.id), None)
        event_dict = event.to_dict()
        event_dict['participantInfo'] = participant.to_dict() if participant else None
        result.append(event_dict)
    
    return jsonify(result)


@app.route('/api/student/event-attendance', methods=['GET'])
def student_event_attendance():
    """Get event attendance records (special attendance) for a student"""
    student_id = request.args.get('studentId')
    
    if not student_id:
        return jsonify({"error": "studentId is required"}), 400
    
    # Get attendance records of type 'event'
    attendance = Attendance.query.filter_by(
        student_admission_id=student_id,
        attendance_type='event'
    ).order_by(Attendance.attendance_date.desc()).all()
    
    result = []
    for record in attendance:
        record_dict = record.to_dict()
        # Get event details
        if record.event_id:
            event = Event.query.get(record.event_id)
            if event:
                record_dict['event'] = {
                    'name': event.event_name,
                    'type': event.event_type,
                    'location': event.location
                }
        result.append(record_dict)
    
    return jsonify(result)


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
    # Get all approved registrations for this activity from CourseRegistration
    course_regs = CourseRegistration.query.filter(
        CourseRegistration.status.in_(['Accepted', 'hod_approved']),
        (CourseRegistration.activity_category == activity_name) |
        (CourseRegistration.activity_name == activity_name)
    ).all()
    
    # Also check old Registration table
    old_regs = Registration.query.filter_by(activity_name=activity_name, status='hod_approved').all()
    
    total_enrolled = len(course_regs) + len(old_regs)
    
    # Get sub-activities
    sub_activities = SubActivity.query.filter_by(activity_name=activity_name).all()
    
    # Get attendance stats
    attendance_records = Attendance.query.filter_by(activity_name=activity_name).all()
    total_attendance_days = len(attendance_records)
    present_count = len([a for a in attendance_records if a.status == 'present'])
    
    # Count by department
    dept_distribution = {}
    for reg in course_regs:
        dept = reg.department or 'Unknown'
        dept_distribution[dept] = dept_distribution.get(dept, 0) + 1
    for reg in old_regs:
        dept = reg.department or 'Unknown'
        dept_distribution[dept] = dept_distribution.get(dept, 0) + 1
    
    # Count by sub-activity
    sub_activity_distribution = {}
    for reg in course_regs:
        sub_name = reg.activity_name if reg.activity_category else 'Unassigned'
        sub_activity_distribution[sub_name] = sub_activity_distribution.get(sub_name, 0) + 1
    
    return jsonify({
        "activityName": activity_name,
        "totalEnrolled": total_enrolled,
        "subActivities": [s.to_dict() for s in sub_activities],
        "totalAttendanceDays": total_attendance_days,
        "presentCount": present_count,
        "overallAttendanceRate": round((present_count / total_attendance_days * 100) if total_attendance_days > 0 else 0, 2),
        "departmentDistribution": dept_distribution,
        "subActivityDistribution": sub_activity_distribution
    })


@app.route('/api/analytics/department/<department>', methods=['GET'])
def department_analytics(department):
    """Get analytics for a specific department (HOD view)"""
    # Get all students from this department
    students = Student.query.filter_by(department=department).all()
    
    # Get registrations from CourseRegistration table (primary source)
    course_regs = CourseRegistration.query.filter_by(department=department).all()
    course_approved = [r for r in course_regs if r.status in ['Accepted', 'hod_approved']]
    course_pending = [r for r in course_regs if r.status in ['Pending Coordinator', 'coordinator_approved', 'Pending HOD']]
    
    # Also get from old Registration table
    registrations = Registration.query.filter_by(department=department).all()
    reg_approved = [r for r in registrations if r.status == 'hod_approved']
    reg_pending = [r for r in registrations if r.status in ['pending', 'coordinator_approved']]
    
    total_approved = len(course_approved) + len(reg_approved)
    total_pending = len(course_pending) + len(reg_pending)
    
    # Count by activity
    activity_distribution = {}
    for reg in course_approved:
        activity_name = reg.activity_category or reg.activity_name
        activity_distribution[activity_name] = activity_distribution.get(activity_name, 0) + 1
    for reg in reg_approved:
        activity_distribution[reg.activity_name] = activity_distribution.get(reg.activity_name, 0) + 1
    
    # Count by course/class
    course_distribution = {}
    for reg in course_approved:
        course_name = reg.course or 'Unknown'
        course_distribution[course_name] = course_distribution.get(course_name, 0) + 1
    
    # Get attendance stats for this department
    attendance_records = Attendance.query.filter(
        Attendance.student_admission_id.in_([r.admission_id for r in course_approved + reg_approved if r.admission_id])
    ).all()
    total_attendance = len(attendance_records)
    present_count = len([a for a in attendance_records if a.status == 'present'])
    
    return jsonify({
        "department": department,
        "totalStudents": len(students),
        "totalRegistrations": len(course_regs) + len(registrations),
        "approvedRegistrations": total_approved,
        "pendingRegistrations": total_pending,
        "activityDistribution": activity_distribution,
        "courseDistribution": course_distribution,
        "totalAttendanceRecords": total_attendance,
        "presentCount": present_count,
        "attendanceRate": round((present_count / total_attendance * 100) if total_attendance > 0 else 0, 2)
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
        # Case-insensitive activity name filtering
        query = query.filter(db.func.lower(Registration.activity_name) == activity_name.lower())
    elif coordinator_email:
        # Filter by coordinator's activity
        coordinator = Coordinator.query.filter_by(email=coordinator_email).first()
        if coordinator:
            query = query.filter(db.func.lower(Registration.activity_name) == coordinator.role.lower())
    
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


# ==================== HOD ROUTES ====================

@app.route('/api/hod/departments', methods=['GET'])
def get_hod_departments():
    """Get all departments with HOD information from Database"""
    try:
        # Query from HOD table which has the actual HOD data
        hods_list = HOD.query.order_by(HOD.department).all()
        
        departments = []
        for hod in hods_list:
            departments.append({
                'hod_id': hod.id,
                'employee_id': hod.employee_id,
                'hod_name': hod.name,
                'dept_code': hod.employee_id,
                'dept_name': hod.department,
                'phone': hod.phone,
                'hod_email': hod.email
            })
        
        return jsonify({
            'status': 'success',
            'departments': departments
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/login', methods=['POST'])
def hod_login():
    """HOD Login with department selection using Database"""
    try:
        data = request.get_json()
        # Frontend sends hod_id (which might be user.id or employee_id)
        hod_id_input = data.get('hod_id')
        dept_code = data.get('dept_code')
        password = data.get('password')
        
        if not all([hod_id_input, dept_code, password]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Find user by ID or Employee ID
        user = User.query.filter(
            (User.id == int(hod_id_input) if str(hod_id_input).isdigit() else False) | 
            (User.employee_id == str(hod_id_input))
        ).first()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        # Verify Role
        if not user.role or user.role.name != 'HOD':
             return jsonify({'status': 'error', 'message': 'User is not an HOD'}), 403

        # Verify Password
        if not verify_password(password, user.password_hash):
             return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        # Verify Department
        dept = Department.query.get(user.assigned_department_id)
        if not dept or dept.code != dept_code:
             return jsonify({'status': 'error', 'message': 'HOD does not belong to this department'}), 403

        # Create session
        session.permanent = True
        session['user_id'] = user.id
        session['role'] = 'HOD'
        session['hod_session'] = {
            'hod_id': user.id,
            'employee_id': user.employee_id,
            'hod_name': user.full_name,
            'dept_code': dept.code,
            'dept_name': dept.name,
            'phone': user.phone,
            'email': user.email,
            'status': 'active',
            'permissions': [{
                'dept_code': dept.code,
                'can_view_students': True,
                'can_approve_requests': True,
                'can_view_reports': True,
                'can_manage_courses': True
            }]
        }
        
        return jsonify({
            'status': 'success',
            'message': 'HOD login successful',
            'hod_info': session['hod_session'],
            'requiresProfileCompletion': not user.profile_completed
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/panel', methods=['GET'])
def hod_panel():
    """Get HOD panel data - requires session"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    hod_info = session['hod_session']
    
    return jsonify({
        'status': 'success',
        'panel_data': {
            'hod_id': hod_info['hod_id'],
            'hod_name': hod_info['hod_name'],
            'dept_code': hod_info['dept_code'],
            'dept_name': hod_info['dept_name'],
            'phone': hod_info['phone'],
            'permissions': hod_info['permissions']
        }
    }), 200


@app.route('/api/hod/students', methods=['GET'])
def hod_get_students():
    """Get students for HOD's department"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        hod_info = session['hod_session']
        dept_code = hod_info['dept_code']
        
        # Query students from database filtered by department
        # For now, return from student_info table
        students_list = db.session.execute(
            db.text('''
                SELECT DISTINCT 
                    si.roll_number,
                    si.student_name,
                    si.email,
                    si.phone,
                    si.pcode,
                    si.dept,
                    si.class,
                    sr.status as registration_status,
                    si.jyear,
                    si.secl
                FROM student_info si
                LEFT JOIN student_registrations sr ON si.roll_number = sr.roll_number
                WHERE si.dept = :dept_code OR si.pcode IN (
                    SELECT DISTINCT pcode FROM program_info WHERE dept = :dept_code
                )
                ORDER BY si.class, si.roll_number
            '''),
            {'dept_code': dept_code}
        ).fetchall()
        
        students = []
        for student in students_list:
            students.append({
                'roll_number': student[0],
                'student_name': student[1],
                'email': student[2],
                'phone': student[3],
                'pcode': student[4],
                'dept_code': student[5],
                'class_name': student[6],
                'registration_status': student[7] or 'not_registered',
                'year': student[8],
                'section': student[9]
            })
        
        return jsonify({
            'status': 'success',
            'department': dept_code,
            'dept_name': hod_info['dept_name'],
            'total': len(students),
            'students': students
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/logout', methods=['POST'])
def hod_logout():
    """HOD Logout"""
    if 'hod_session' in session:
        del session['hod_session']
    
    return jsonify({
        'status': 'success',
        'message': 'HOD logout successful'
    }), 200


@app.route('/api/hod/profile', methods=['GET', 'PUT'])
def hod_profile():
    """Get or update HOD profile"""
    try:
        # Get email from query param or session
        email = request.args.get('email') or (session.get('hod_session', {}).get('hod_id'))
        
        if not email:
            return jsonify({'status': 'error', 'message': 'Email required'}), 400
        
        # Find HOD user by email
        user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
        
        if request.method == 'GET':
            if not user:
                # Return empty profile if user doesn't exist yet
                return jsonify({
                    'status': 'success',
                    'profile': None,
                    'message': 'Profile not found'
                }), 200
            
            return jsonify({
                'status': 'success',
                'profile': user.to_dict()
            }), 200
        
        elif request.method == 'PUT':
            payload = request.get_json(silent=True) or {}
            
            if not user:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
            # Update profile fields
            if 'fullName' in payload:
                user.full_name = payload['fullName']
            if 'phone' in payload:
                user.phone = payload['phone']
            if 'gender' in payload:
                user.gender = payload['gender']
            if 'address' in payload:
                user.address = payload['address']
            if 'specialization' in payload:
                user.specialization = payload['specialization']
            if 'qualifications' in payload:
                user.qualifications = payload['qualifications']
            if 'bio' in payload:
                user.bio = payload['bio']
            if 'profilePhoto' in payload:
                user.profile_photo = payload['profilePhoto']
            
            # Mark profile as completed
            user.profile_completed = True
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Profile updated successfully',
                'profile': user.to_dict()
            }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/profile/upload-photo', methods=['POST'])
def hod_upload_photo():
    """Upload HOD profile photo"""
    try:
        email = request.form.get('email')
        if not email:
            return jsonify({'status': 'error', 'message': 'Email required'}), 400
        
        if 'photo' not in request.files:
            return jsonify({'status': 'error', 'message': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Create unique filename
            filename = secure_filename(f"hod_{email.replace('@', '_')}_{int(datetime.utcnow().timestamp())}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Update user profile_photo in DB
            relative_path = f"/uploads/{filename}"
            user = User.query.filter(func.lower(User.email) == func.lower(email)).first()
            if user:
                user.profile_photo = relative_path
                db.session.commit()
            
            return jsonify({
                'status': 'success',
                'profilePhoto': relative_path
            }), 200
        
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== REGISTRATION & APPROVAL ROUTES ====================

@app.route('/api/registration/submit', methods=['POST'])
def submit_registration():
    """Student submits registration with department selection"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    department_id = data.get('departmentId')
    
    if not department_id:
        return jsonify({'status': 'error', 'message': 'Department is required'}), 400
        
    try:
        user = User.query.get(user_id)
        user.assigned_department_id = department_id
        user.registration_status = 'PENDING'
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Registration submitted. Waiting for HOD approval.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/hod/pending-students', methods=['GET'])
def get_pending_students():
    """HOD gets pending students for their department"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    hod_info = session['hod_session']
    # Find department ID based on code
    dept = Department.query.filter_by(code=hod_info['dept_code']).first()
    
    if not dept:
        return jsonify({'status': 'error', 'message': 'Department not found'}), 404
        
    try:
        # Get students with PENDING status in this department
        students = User.query.filter_by(
            assigned_department_id=dept.id,
            registration_status='PENDING'
        ).join(Role).filter(Role.name == 'STUDENT').all()
        
        return jsonify({
            'status': 'success',
            'students': [s.to_dict() for s in students]
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/hod/approve-student', methods=['POST'])
def approve_student():
    """HOD approves a student registration"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        
    data = request.get_json()
    student_id = data.get('studentId')
    action = data.get('action', 'APPROVE') # APPROVE or REJECT
    
    if not student_id:
        return jsonify({'status': 'error', 'message': 'Student ID required'}), 400
        
    try:
        student = User.query.get(student_id)
        if not student:
            return jsonify({'status': 'error', 'message': 'Student not found'}), 404
            
        if action == 'APPROVE':
            student.registration_status = 'APPROVED'
        elif action == 'REJECT':
            student.registration_status = 'REJECTED'
            
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Student {action}D successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== COORDINATOR ATTENDANCE ROUTES ====================

@app.route('/api/coordinator/sub-activity/<int:sub_activity_id>/students', methods=['GET'])
def get_sub_activity_students(sub_activity_id):
    """Get students assigned to a specific sub-activity for attendance marking"""
    try:
        # Get accepted students in this sub-activity
        students = CourseRegistration.query.filter(
            CourseRegistration.sub_activity_id == sub_activity_id,
            CourseRegistration.status.in_(['Accepted', 'hod_approved'])
        ).all()
        
        student_list = [{
            'admissionId': s.admission_id,
            'studentName': s.student_name,
            'course': s.course,
            'department': s.department
        } for s in students]
        
        return jsonify({
            'status': 'success',
            'students': student_list,
            'count': len(student_list)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/coordinator/sub-activity-name/<string:sub_activity_name>/students', methods=['GET'])
def get_sub_activity_students_by_name(sub_activity_name):
    """Get students assigned to a sub-activity by name (used by student coordinator attendance)"""
    try:
        # First find the sub-activity ID from the name
        sub_activity = SubActivity.query.filter(
            SubActivity.sub_activity_name == sub_activity_name
        ).first()
        
        if not sub_activity:
            return jsonify({
                'status': 'error',
                'message': f'Sub-activity "{sub_activity_name}" not found'
            }), 404
        
        # Get accepted students in this sub-activity
        students = CourseRegistration.query.filter(
            CourseRegistration.sub_activity_id == sub_activity.id,
            CourseRegistration.status.in_(['Accepted', 'hod_approved'])
        ).all()
        
        student_list = [{
            'admissionId': s.admission_id,
            'studentName': s.student_name,
            'course': s.course,
            'department': s.department
        } for s in students]
        
        return jsonify({
            'status': 'success',
            'students': student_list,
            'count': len(student_list),
            'subActivityId': sub_activity.id,
            'subActivityName': sub_activity.sub_activity_name,
            'activityName': sub_activity.activity_name
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/coordinator/activity/<string:activity_name>/students', methods=['GET'])
def get_activity_students(activity_name):
    """Get all students in an activity for faculty coordinator"""
    try:
        students = CourseRegistration.query.filter(
            CourseRegistration.activity_category == activity_name,
            CourseRegistration.status.in_(['Accepted', 'hod_approved'])
        ).all()
        
        student_list = [{
            'admissionId': s.admission_id,
            'studentName': s.student_name,
            'course': s.course,
            'department': s.department,
            'subActivityId': s.sub_activity_id
        } for s in students]
        
        return jsonify({
            'status': 'success',
            'students': student_list,
            'count': len(student_list)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/submit', methods=['POST'])
def submit_attendance():
    """Student coordinator submits attendance (pending approval)"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        submitted_by = data.get('submittedBy', '')
        activity_name = data.get('activityName', '')
        sub_activity_id = data.get('subActivityId')
        attendance_date = data.get('attendanceDate')
        
        if not records:
            return jsonify({'status': 'error', 'message': 'No attendance records provided'}), 400
        
        # Generate batch ID for grouping
        import uuid
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        for record in records:
            new_attendance = Attendance(
                student_admission_id=record.get('studentAdmissionId'),
                student_name=record.get('studentName'),
                activity_name=activity_name,
                sub_activity_id=sub_activity_id,
                attendance_date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                attendance_type='daily',
                status=record.get('status', 'present'),
                coordinator_email=submitted_by,
                approval_status='pending',  # Pending faculty coordinator approval
                submitted_by=submitted_by,
                batch_id=batch_id
            )
            db.session.add(new_attendance)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance submitted for approval ({len(records)} students)',
            'batchId': batch_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/pending', methods=['GET'])
def get_pending_attendance():
    """Faculty coordinator gets pending attendance submissions"""
    try:
        activity_name = request.args.get('activity')
        
        # Get unique batches of pending attendance
        query = Attendance.query.filter_by(approval_status='pending')
        
        if activity_name:
            query = query.filter_by(activity_name=activity_name)
        
        pending_records = query.order_by(Attendance.created_at.desc()).all()
        
        # Group by batch_id
        batches = {}
        for record in pending_records:
            batch_id = record.batch_id or f"SINGLE-{record.id}"
            if batch_id not in batches:
                batches[batch_id] = {
                    'batchId': batch_id,
                    'activityName': record.activity_name,
                    'subActivityId': record.sub_activity_id,
                    'attendanceDate': record.attendance_date.isoformat() if record.attendance_date else None,
                    'submittedBy': record.submitted_by,
                    'submittedAt': record.created_at.isoformat() if record.created_at else None,
                    'records': [],
                    'presentCount': 0,
                    'absentCount': 0
                }
            batches[batch_id]['records'].append(record.to_dict())
            if record.status == 'present':
                batches[batch_id]['presentCount'] += 1
            else:
                batches[batch_id]['absentCount'] += 1
        
        return jsonify({
            'status': 'success',
            'pendingBatches': list(batches.values()),
            'totalBatches': len(batches)
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/approve', methods=['POST'])
def approve_attendance():
    """Faculty coordinator approves pending attendance"""
    try:
        data = request.get_json()
        batch_id = data.get('batchId')
        approved_by = data.get('approvedBy', '')
        action = data.get('action', 'approve')  # 'approve' or 'reject'
        
        if not batch_id:
            return jsonify({'status': 'error', 'message': 'Batch ID required'}), 400
        
        # Update all records in this batch
        records = Attendance.query.filter_by(batch_id=batch_id, approval_status='pending').all()
        
        if not records:
            return jsonify({'status': 'error', 'message': 'No pending records found for this batch'}), 404
        
        for record in records:
            if action == 'approve':
                record.approval_status = 'approved'
                record.approved_by = approved_by
                record.approved_at = datetime.utcnow()
            else:
                record.approval_status = 'rejected'
                record.approved_by = approved_by
                record.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance {action}d successfully ({len(records)} records)',
            'recordCount': len(records)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/status-by-dates', methods=['GET'])
def get_attendance_status_by_dates():
    """Get attendance status (pending/approved/rejected) for a range of dates"""
    try:
        activity_name = request.args.get('activity')
        sub_activity_id = request.args.get('subActivityId', type=int)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        if not activity_name:
            return jsonify({'status': 'error', 'message': 'Activity is required'}), 400
        
        # Default to current month if not provided
        if not year or not month:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        # Get first and last day of month
        from calendar import monthrange
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, monthrange(year, month)[1]).date()
        
        # Query attendance records for this month
        query = Attendance.query.filter(
            Attendance.activity_name == activity_name,
            Attendance.attendance_date >= first_day,
            Attendance.attendance_date <= last_day
        )
        
        if sub_activity_id:
            query = query.filter(Attendance.sub_activity_id == sub_activity_id)
        
        records = query.all()
        
        # Group by date and get status
        date_status = {}
        for record in records:
            date_str = record.attendance_date.isoformat()
            current_status = date_status.get(date_str)
            
            # Priority: approved > pending > rejected
            if record.approval_status == 'approved':
                date_status[date_str] = 'approved'
            elif record.approval_status == 'pending' and current_status != 'approved':
                date_status[date_str] = 'pending'
            elif record.approval_status == 'rejected' and current_status not in ['approved', 'pending']:
                date_status[date_str] = 'rejected'
        
        return jsonify({
            'status': 'success',
            'year': year,
            'month': month,
            'dateStatuses': date_status
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/check-existing-all', methods=['GET'])
def check_existing_attendance_all():
    """Check if attendance exists (pending or approved) for a specific date"""
    try:
        activity_name = request.args.get('activity')
        sub_activity_id = request.args.get('subActivityId', type=int)
        attendance_date = request.args.get('date')
        
        if not activity_name or not attendance_date:
            return jsonify({'status': 'error', 'message': 'Activity and date are required'}), 400
        
        try:
            date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400
        
        # Check for approved attendance
        approved_query = Attendance.query.filter(
            Attendance.activity_name == activity_name,
            Attendance.attendance_date == date_obj,
            Attendance.approval_status == 'approved'
        )
        if sub_activity_id:
            approved_query = approved_query.filter(Attendance.sub_activity_id == sub_activity_id)
        approved_records = approved_query.all()
        
        # Check for pending attendance
        pending_query = Attendance.query.filter(
            Attendance.activity_name == activity_name,
            Attendance.attendance_date == date_obj,
            Attendance.approval_status == 'pending'
        )
        if sub_activity_id:
            pending_query = pending_query.filter(Attendance.sub_activity_id == sub_activity_id)
        pending_records = pending_query.all()
        
        result = {
            'status': 'success',
            'approvedExists': len(approved_records) > 0,
            'pendingExists': len(pending_records) > 0,
            'approvedData': None,
            'pendingData': None
        }
        
        if approved_records:
            first = approved_records[0]
            result['approvedData'] = {
                'presentCount': len([r for r in approved_records if r.status == 'present']),
                'absentCount': len([r for r in approved_records if r.status == 'absent']),
                'approvedBy': first.approved_by,
                'approvedAt': first.approved_at.isoformat() if first.approved_at else None,
                'batchId': first.batch_id,
                'records': [{'studentAdmissionId': r.student_admission_id, 'status': r.status} for r in approved_records]
            }
        
        if pending_records:
            first = pending_records[0]
            result['pendingData'] = {
                'presentCount': len([r for r in pending_records if r.status == 'present']),
                'absentCount': len([r for r in pending_records if r.status == 'absent']),
                'submittedBy': first.submitted_by,
                'submittedAt': first.created_at.isoformat() if first.created_at else None,
                'batchId': first.batch_id,
                'records': [{'studentAdmissionId': r.student_admission_id, 'status': r.status} for r in pending_records]
            }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/check-existing', methods=['GET'])
def check_existing_attendance():
    """Check if attendance already exists for a specific date/activity/sub-activity"""
    try:
        activity_name = request.args.get('activity')
        sub_activity_id = request.args.get('subActivityId', type=int)
        attendance_date = request.args.get('date')
        
        if not activity_name or not attendance_date:
            return jsonify({'status': 'error', 'message': 'Activity and date are required'}), 400
        
        # Parse the date
        try:
            date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format'}), 400
        
        # Build query
        query = Attendance.query.filter(
            Attendance.activity_name == activity_name,
            Attendance.attendance_date == date_obj,
            Attendance.approval_status == 'approved'
        )
        
        if sub_activity_id:
            query = query.filter(Attendance.sub_activity_id == sub_activity_id)
        
        existing_records = query.all()
        
        if existing_records:
            # Get the batch info
            first_record = existing_records[0]
            records_data = [{
                'studentAdmissionId': r.student_admission_id,
                'studentName': r.student_name,
                'status': r.status
            } for r in existing_records]
            
            return jsonify({
                'status': 'success',
                'exists': True,
                'attendanceDate': date_obj.isoformat(),
                'batchId': first_record.batch_id,
                'submittedBy': first_record.submitted_by,
                'approvedBy': first_record.approved_by,
                'approvedAt': first_record.approved_at.isoformat() if first_record.approved_at else None,
                'records': records_data,
                'totalRecords': len(existing_records),
                'presentCount': len([r for r in existing_records if r.status == 'present']),
                'absentCount': len([r for r in existing_records if r.status == 'absent'])
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'exists': False
            }), 200
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/update', methods=['PUT'])
def update_attendance():
    """Faculty coordinator updates existing attendance records"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        updated_by = data.get('updatedBy', '')
        activity_name = data.get('activityName', '')
        sub_activity_id = data.get('subActivityId')
        attendance_date = data.get('attendanceDate')
        
        if not records or not attendance_date:
            return jsonify({'status': 'error', 'message': 'Records and date are required'}), 400
        
        date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        
        # Build query for existing records
        query = Attendance.query.filter(
            Attendance.activity_name == activity_name,
            Attendance.attendance_date == date_obj,
            Attendance.approval_status == 'approved'
        )
        
        if sub_activity_id:
            query = query.filter(Attendance.sub_activity_id == sub_activity_id)
        
        existing_records = query.all()
        existing_map = {r.student_admission_id: r for r in existing_records}
        
        updated_count = 0
        added_count = 0
        
        for record in records:
            student_id = record.get('studentAdmissionId')
            new_status = record.get('status', 'present')
            student_name = record.get('studentName', '')
            
            if student_id in existing_map:
                # Update existing record
                existing_map[student_id].status = new_status
                existing_map[student_id].coordinator_email = updated_by
                updated_count += 1
            else:
                # Add new record (student might have been added to sub-activity after initial attendance)
                import uuid
                new_attendance = Attendance(
                    student_admission_id=student_id,
                    student_name=student_name,
                    activity_name=activity_name,
                    sub_activity_id=sub_activity_id,
                    attendance_date=date_obj,
                    attendance_type='daily',
                    status=new_status,
                    coordinator_email=updated_by,
                    approval_status='approved',
                    submitted_by=updated_by,
                    approved_by=updated_by,
                    approved_at=datetime.utcnow(),
                    batch_id=f"UPDATE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
                )
                db.session.add(new_attendance)
                added_count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance updated successfully ({updated_count} updated, {added_count} added)',
            'updatedCount': updated_count,
            'addedCount': added_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/mark-direct', methods=['POST'])
def mark_attendance_direct():
    """Faculty coordinator marks attendance directly (auto-approved)"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        marked_by = data.get('markedBy', '')
        activity_name = data.get('activityName', '')
        sub_activity_id = data.get('subActivityId')
        attendance_date = data.get('attendanceDate')
        
        if not records:
            return jsonify({'status': 'error', 'message': 'No attendance records provided'}), 400
        
        import uuid
        batch_id = f"DIRECT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        for record in records:
            new_attendance = Attendance(
                student_admission_id=record.get('studentAdmissionId'),
                student_name=record.get('studentName'),
                activity_name=activity_name,
                sub_activity_id=sub_activity_id,
                attendance_date=datetime.strptime(attendance_date, '%Y-%m-%d').date(),
                attendance_type='daily',
                status=record.get('status', 'present'),
                coordinator_email=marked_by,
                approval_status='approved',  # Auto-approved for faculty coordinator
                submitted_by=marked_by,
                approved_by=marked_by,
                approved_at=datetime.utcnow(),
                batch_id=batch_id
            )
            db.session.add(new_attendance)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance marked successfully ({len(records)} students)',
            'batchId': batch_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/student/<string:student_id>', methods=['GET'])
def get_student_attendance(student_id):
    """Get attendance records for a specific student"""
    try:
        records = Attendance.query.filter_by(
            student_admission_id=student_id,
            approval_status='approved'  # Only show approved attendance
        ).order_by(Attendance.attendance_date.desc()).all()
        
        total = len(records)
        present = len([r for r in records if r.status == 'present'])
        absent = len([r for r in records if r.status == 'absent'])
        rate = (present / total * 100) if total > 0 else 0
        
        return jsonify({
            'status': 'success',
            'studentId': student_id,
            'summary': {
                'totalDays': total,
                'presentDays': present,
                'absentDays': absent,
                'attendanceRate': round(rate, 2)
            },
            'records': [r.to_dict() for r in records]
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/history', methods=['GET'])
def get_attendance_history():
    """Get attendance history for a specific activity (faculty coordinator view)"""
    try:
        activity_name = request.args.get('activity')
        limit = request.args.get('limit', 50, type=int)

        query = Attendance.query.filter_by(approval_status='approved')
        if activity_name:
            query = query.filter_by(activity_name=activity_name)

        records = query.order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc()).limit(limit).all()

        # Group by date + subActivityId (more specific grouping)
        grouped = {}
        for r in records:
            sub_activity_id = r.sub_activity_id or 'N/A'
            key = f"{r.attendance_date.isoformat()}|{sub_activity_id}"
            if key not in grouped:
                # Get sub-activity name if available
                sub_activity_name = None
                if r.sub_activity_id:
                    sub_activity = SubActivity.query.get(r.sub_activity_id)
                    if sub_activity:
                        sub_activity_name = sub_activity.sub_activity_name
                
                grouped[key] = {
                    'attendanceDate': r.attendance_date.isoformat() if r.attendance_date else None,
                    'activityName': r.activity_name,
                    'subActivityId': r.sub_activity_id,
                    'subActivityName': sub_activity_name,
                    'batchId': r.batch_id,
                    'approvedBy': r.approved_by,
                    'submittedBy': r.submitted_by,
                    'records': [],
                    'presentCount': 0,
                    'absentCount': 0
                }
            grouped[key]['records'].append(r.to_dict())
            if r.status == 'present':
                grouped[key]['presentCount'] += 1
            else:
                grouped[key]['absentCount'] += 1

        return jsonify({
            'status': 'success',
            'history': list(grouped.values()),
            'totalGroups': len(grouped)
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== HOD ANALYTICS ROUTES ====================

@app.route('/api/hod/analytics/overview', methods=['GET'])
def hod_analytics_overview():
    """Get overall attendance analytics for HOD's department"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        hod_info = session['hod_session']
        dept_name = hod_info.get('dept_name') or hod_info.get('department')
        
        # Get department programs mapping
        program_mappings = ProgramDepartmentMapping.query.filter_by(
            department_name=dept_name
        ).all()
        
        program_names = [pm.program_name for pm in program_mappings]
        
        # Get all students from these programs who are accepted in activities
        accepted_statuses = ['Accepted', 'hod_approved']
        students_query = CourseRegistration.query.filter(
            CourseRegistration.status.in_(accepted_statuses),
            CourseRegistration.department == dept_name
        ).all()
        
        total_students = len(students_query)
        student_ids = [s.admission_id for s in students_query]
        
        # Get attendance records for these students
        attendance_records = Attendance.query.filter(
            Attendance.student_admission_id.in_(student_ids)
        ).all()
        
        total_attendance_records = len(attendance_records)
        present_count = len([a for a in attendance_records if a.status == 'present'])
        absent_count = len([a for a in attendance_records if a.status == 'absent'])
        
        # Calculate overall attendance rate
        attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0
        
        # Activity-wise breakdown
        activity_stats = {}
        for record in attendance_records:
            activity = record.activity_name
            if activity not in activity_stats:
                activity_stats[activity] = {
                    'total': 0,
                    'present': 0,
                    'absent': 0
                }
            activity_stats[activity]['total'] += 1
            if record.status == 'present':
                activity_stats[activity]['present'] += 1
            else:
                activity_stats[activity]['absent'] += 1
        
        # Add attendance rate for each activity
        for activity, stats in activity_stats.items():
            stats['attendanceRate'] = (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return jsonify({
            'status': 'success',
            'department': dept_name,
            'programs': program_names,
            'overview': {
                'totalStudents': total_students,
                'totalAttendanceRecords': total_attendance_records,
                'presentCount': present_count,
                'absentCount': absent_count,
                'overallAttendanceRate': round(attendance_rate, 2)
            },
            'activityBreakdown': activity_stats
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/analytics/program/<string:program_name>', methods=['GET'])
def hod_analytics_by_program(program_name):
    """Get attendance analytics for a specific program"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        # Get students from this program
        students_query = CourseRegistration.query.filter(
            CourseRegistration.course == program_name,
            CourseRegistration.status.in_(['Accepted', 'hod_approved'])
        ).all()
        
        student_ids = [s.admission_id for s in students_query]
        
        # Get attendance records
        attendance_records = Attendance.query.filter(
            Attendance.student_admission_id.in_(student_ids)
        ).all()
        
        total_records = len(attendance_records)
        present_count = len([a for a in attendance_records if a.status == 'present'])
        
        return jsonify({
            'status': 'success',
            'program': program_name,
            'totalStudents': len(student_ids),
            'totalAttendanceRecords': total_records,
            'presentCount': present_count,
            'attendanceRate': round((present_count / total_records * 100) if total_records > 0 else 0, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/analytics/activity/<string:activity_name>', methods=['GET'])
def hod_analytics_by_activity(activity_name):
    """Get attendance analytics for a specific activity within department"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        hod_info = session['hod_session']
        dept_name = hod_info.get('dept_name') or hod_info.get('department')
        
        # Get students from this department in this activity
        students_query = CourseRegistration.query.filter(
            CourseRegistration.department == dept_name,
            CourseRegistration.activity_name == activity_name,
            CourseRegistration.status.in_(['Accepted', 'hod_approved'])
        ).all()
        
        student_ids = [s.admission_id for s in students_query]
        
        # Get attendance records for this activity
        attendance_records = Attendance.query.filter(
            Attendance.student_admission_id.in_(student_ids),
            Attendance.activity_name == activity_name
        ).all()
        
        total_records = len(attendance_records)
        present_count = len([a for a in attendance_records if a.status == 'present'])
        
        # Student-wise breakdown
        student_attendance = {}
        for record in attendance_records:
            student_id = record.student_admission_id
            if student_id not in student_attendance:
                student_attendance[student_id] = {
                    'studentId': student_id,
                    'studentName': record.student_name,
                    'total': 0,
                    'present': 0,
                    'absent': 0
                }
            student_attendance[student_id]['total'] += 1
            if record.status == 'present':
                student_attendance[student_id]['present'] += 1
            else:
                student_attendance[student_id]['absent'] += 1
        
        # Add attendance rate for each student
        for student_id, stats in student_attendance.items():
            stats['attendanceRate'] = (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return jsonify({
            'status': 'success',
            'activity': activity_name,
            'department': dept_name,
            'totalStudents': len(student_ids),
            'totalAttendanceRecords': total_records,
            'presentCount': present_count,
            'overallAttendanceRate': round((present_count / total_records * 100) if total_records > 0 else 0, 2),
            'studentBreakdown': list(student_attendance.values())
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/analytics/student/<string:student_id>', methods=['GET'])
def hod_analytics_student_detail(student_id):
    """Get detailed attendance analytics for a specific student"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        # Get student info
        student = CourseRegistration.query.filter_by(
            admission_id=student_id
        ).first()
        
        if not student:
            return jsonify({'status': 'error', 'message': 'Student not found'}), 404
        
        # Get all attendance records
        attendance_records = Attendance.query.filter_by(
            student_admission_id=student_id
        ).order_by(Attendance.attendance_date.desc()).all()
        
        total_records = len(attendance_records)
        present_count = len([a for a in attendance_records if a.status == 'present'])
        absent_count = len([a for a in attendance_records if a.status == 'absent'])
        
        # Monthly breakdown
        from collections import defaultdict
        monthly_stats = defaultdict(lambda: {'total': 0, 'present': 0, 'absent': 0})
        
        for record in attendance_records:
            month_key = record.attendance_date.strftime('%Y-%m')
            monthly_stats[month_key]['total'] += 1
            if record.status == 'present':
                monthly_stats[month_key]['present'] += 1
            else:
                monthly_stats[month_key]['absent'] += 1
        
        # Format monthly stats
        monthly_data = []
        for month, stats in sorted(monthly_stats.items()):
            stats['month'] = month
            stats['attendanceRate'] = (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
            monthly_data.append(stats)
        
        return jsonify({
            'status': 'success',
            'student': {
                'admissionId': student_id,
                'name': student.student_name,
                'department': student.department,
                'course': student.course,
                'activity': student.activity_name
            },
            'summary': {
                'totalRecords': total_records,
                'presentCount': present_count,
                'absentCount': absent_count,
                'attendanceRate': round((present_count / total_records * 100) if total_records > 0 else 0, 2)
            },
            'monthlyBreakdown': monthly_data,
            'recentAttendance': [a.to_dict() for a in attendance_records[:10]]
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/hod/analytics/export', methods=['GET'])
def hod_analytics_export():
    """Export attendance analytics to CSV"""
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        import csv
        from io import StringIO
        from flask import Response
        
        hod_info = session['hod_session']
        dept_name = hod_info.get('dept_name') or hod_info.get('department')
        
        # Get all students from department
        students = CourseRegistration.query.filter(
            CourseRegistration.department == dept_name,
            CourseRegistration.status.in_(['Accepted', 'hod_approved'])
        ).all()
        
        # Create CSV
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Student ID', 'Name', 'Program', 'Activity', 'Total Days', 'Present', 'Absent', 'Attendance %'])
        
        for student in students:
            records = Attendance.query.filter_by(
                student_admission_id=student.admission_id
            ).all()
            
            total = len(records)
            present = len([r for r in records if r.status == 'present'])
            absent = total - present
            rate = (present / total * 100) if total > 0 else 0
            
            writer.writerow([
                student.admission_id,
                student.student_name,
                student.course,
                student.activity_name,
                total,
                present,
                absent,
                f"{rate:.2f}%"
            ])
        
        output = si.getvalue()
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=attendance_report_{dept_name}_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Catch-all route to serve HTML files
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from the web directory"""
    return send_from_directory(WEB_DIR, filename)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(500)
def handle_500(e):
    """Log all 500 errors with full traceback to errors.log and send Telegram alert"""
    tb = traceback.format_exc()
    logger.error(
        f"500 Internal Server Error\n"
        f"URL: {request.method} {request.url}\n"
        f"IP: {request.remote_addr}\n"
        f"Traceback:\n{tb}"
    )
    send_telegram_alert(
        f"\U0001f534 <b>500 Server Error</b>\n"
        f"<b>URL:</b> {request.method} {request.path}\n"
        f"<b>Error:</b> {str(e)[:200]}"
    )
    return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Catch ALL unhandled exceptions, log them, and send Telegram alert"""
    if hasattr(e, 'code') and e.code in (404, 405):
        return e  # Let Flask handle HTTP errors normally
    tb = traceback.format_exc()
    logger.error(
        f"Unhandled Exception: {type(e).__name__}: {str(e)}\n"
        f"URL: {request.method} {request.url}\n"
        f"IP: {request.remote_addr}\n"
        f"Traceback:\n{tb}"
    )
    send_telegram_alert(
        f"\U0001f6a8 <b>Unhandled Exception</b>\n"
        f"<b>Type:</b> {type(e).__name__}\n"
        f"<b>URL:</b> {request.method} {request.path}\n"
        f"<b>Error:</b> {str(e)[:200]}"
    )
    return jsonify({'error': 'Unexpected error', 'message': str(e)}), 500


@app.after_request
def log_response_errors(response):
    """Log 4xx and 5xx HTTP responses"""
    if response.status_code >= 400:
        logger.warning(
            f"HTTP {response.status_code} — {request.method} {request.path} "
            f"[IP: {request.remote_addr}]"
        )
    return response


@app.errorhandler(404)
def handle_404(e):
    """Handle 404 errors by returning index.html for client-side routing"""
    # Try to serve the requested file
    try:
        return send_from_directory(WEB_DIR, request.path.lstrip('/'))
    except:
        # If file not found, return index.html for single-page app
        try:
            return send_from_directory(WEB_DIR, 'index.html')
        except:
            return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all() # Creates tables if they don't exist
            print("[OK] Successfully connected to the database and created tables.")
            
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
                    'employee_id': 'ADMIN001',
                    'status': 'APPROVED'
                },
                {
                    'email': 'create',
                    'password': '1234',
                    'name': 'Super Admin',
                    'role': 'CREATOR',
                    'employee_id': 'CREATOR001',
                    'status': 'APPROVED'
                },
                {
                    'email': 'student@pbsiddhartha.ac.in',
                    'password': 'student123',
                    'name': 'Test Student',
                    'role': 'STUDENT',
                    'employee_id': '22B91A05L6',
                    'status': 'APPROVED'
                },
                {
                    'email': 'hod@pbsiddhartha.ac.in',
                    'password': 'hod123',
                    'name': 'Dr. K Uday Sri',
                    'role': 'HOD',
                    'employee_id': '12345',
                    'status': 'APPROVED'
                },
                {
                    'email': 'ruhi@pbsiddhartha.ac.in',
                    'password': 'ruhi123',
                    'name': 'Ruhi - NCC Coordinator',
                    'role': 'COORDINATOR',
                    'employee_id': '123',
                    'status': 'APPROVED'
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
                        is_active=True,
                        registration_status=user_data.get('status', 'APPROVED')
                    )
                    db.session.add(user)
            db.session.commit()
            
            # Print all available credentials
            print("\n[OK] All default users are ready!")
            print("\n[INFO] Available Login Credentials:")
            print("=" * 80)
            print("Creator (Super): create / 1234")
            print("Creator (Admin): admin@pbsiddhartha.ac.in / admin123")
            print("Student:         student@pbsiddhartha.ac.in / student123")
            print("HOD:             hod@pbsiddhartha.ac.in / hod123")
            print("Coordinator:     ruhi@pbsiddhartha.ac.in / ruhi123")
            print("=" * 80)
            
        except Exception as e:
            print(f"[ERROR] Database Error: {e}")
            print("[HINT] Ensure the database is properly configured.")
            exit(1)
    port = int(os.environ.get('PORT', '5000'))
    print(f"\n[INFO] Starting server on port {port}...")
    # use_reloader=False is set to prevent [WinError 10038] on Windows
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

# Replaced duplicate if __name__ == '__main__': block with single clean execution block
