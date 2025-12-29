import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APP_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(APP_DIR)
WEB_DIR = os.path.join(PARENT_DIR, 'web')

app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

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

# Database Models
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    # We store the calculated key (rollNo or email) to maintain the uniqueness logic
    lookup_key = db.Column(db.String, unique=True, index=True)
    profile = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        # Merge metadata with the profile data for the API response
        data = self.profile.copy() if self.profile else {}
        data['createdAt'] = self.created_at.isoformat() if self.created_at else None
        data['updatedAt'] = self.updated_at.isoformat() if self.updated_at else None
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
    activity_name = db.Column(db.String(255), index=True)  # Activity applied for
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
            "activityName": self.activity_name,
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
    data = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'activityName': self.activity_name,
            'subActivityName': self.sub_activity_name,
            'coordinatorEmail': self.coordinator_email,
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
    activity_name = db.Column(db.String(255))
    activity_category = db.Column(db.String(255))
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
            'activityName': self.activity_name,
            'activityCategory': self.activity_category,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastUpdated': self.last_updated.isoformat() if self.last_updated else None
        })
        return result

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
    """Student authentication endpoint"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    admission_id = payload.get('admissionId', '').strip()
    
    if not email or not admission_id:
        return jsonify({"error": "Email and admission ID are required"}), 400
    
    # Search for student by email or admission ID
    student = Student.query.filter(
        db.or_(
            Student.profile['email'].astext.ilike(f'%{email}%'),
            Student.profile['admissionId'].astext == admission_id
        )
    ).first()
    
    if student:
        return jsonify({"success": True, "student": student.to_dict()})
    else:
        return jsonify({"error": "Student not found"}), 404


@app.route('/api/auth/coordinator', methods=['POST'])
def auth_coordinator():
    """Coordinator authentication endpoint"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    coordinator_id = payload.get('id', '').strip()
    
    if not email or not coordinator_id:
        return jsonify({"error": "Email and ID are required"}), 400
    
    # Find coordinator by email and ID
    coordinator = Coordinator.query.filter_by(email=email, coordinator_id=coordinator_id).first()
    
    if coordinator:
        return jsonify({"success": True, "coordinator": coordinator.to_dict()})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/auth/hod', methods=['POST'])
def auth_hod():
    """HOD authentication endpoint"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    employee_id = payload.get('id', '').strip()
    
    if not email or not employee_id:
        return jsonify({"error": "Email and employee ID are required"}), 400
    
    # Find HOD by email and employee ID
    hod = HOD.query.filter_by(email=email, employee_id=employee_id).first()
    
    if hod:
        return jsonify({"success": True, "hod": hod.to_dict()})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/api/students', methods=['POST'])
def register_student():
    """Student registration endpoint - saves student to database"""
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    admission_id = payload.get('admissionId', '').strip()
    student_name = payload.get('studentName', '').strip()
    
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
        regs = Registration.query.all()
        return jsonify([r.to_dict() for r in regs])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        email = payload.get('email', '').strip().lower()
        admission_id = payload.get('admissionId', '').strip()
        activity_name = payload.get('activityName', '').strip()
        
        if not email or not admission_id or not activity_name:
            return jsonify({"error": "Email, admission ID, and activity name are required"}), 400
        
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
                activity_name=activity_name,
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
        if activity_name:
            subs = SubActivity.query.filter_by(activity_name=activity_name).all()
        else:
            subs = SubActivity.query.all()
        return jsonify([s.to_dict() for s in subs])
    
    elif request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        activity_name = payload.get('activityName', '').strip()
        sub_activity_name = payload.get('subActivityName', '').strip()
        coordinator_email = payload.get('coordinatorEmail', '').strip()
        data = payload.get('data', {})
        
        if not all([activity_name, sub_activity_name]):
            return jsonify({"error": "Activity name and sub-activity name are required"}), 400
        
        try:
            new_sub = SubActivity(
                activity_name=activity_name, 
                sub_activity_name=sub_activity_name, 
                coordinator_email=coordinator_email,
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
                activity_name=payload.get('activityName', ''),
                activity_category=payload.get('activityCategory', ''),
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
            reg.status = 'hod_approved'  # Fully approved - student cannot apply again
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


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all() # Creates tables if they don't exist
            print("✅ Successfully connected to the database and created tables.")
        except Exception as e:
            print(f"❌ Database Error: {e}")
            print("💡 Hint: Run 'python backend/create_db.py' to create the database first.")
            exit(1)
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=True)
