"""
Comprehensive Data Import Script
Imports students, HODs, departments, and programs from CSV files to database.
Maps pcode to department for proper HOD-student relationships.
"""

import os
import csv
import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Import after loading env
from app import app, db, Student, Department, User, Role, hash_password

# Program code to department code mapping based on CSV data
PCODE_TO_DEPT = {
    '11': 'ECO',  # B.A.-Honours(ECO)
    '21': 'COM',  # B.Com.-Honours(General)
    '22': 'COM',  # B.Com.-Honours(Computer Applications)-A
    '23': 'COM',  # B.Com.-Honours(Computer Applications)-B
    '24': 'COM',  # B.Com.-Honours(Computer Applications)-C
    '25': 'COM',  # B.Com.-Honours(Tax Procedures)
    '26': 'COM',  # B.Com.-Honours(Finance)
    '27': 'COM',  # B.Com.-Honours(BPM)
    '28': 'COM',  # B.Com.-Honours(Banking)
    '31': 'BBA',  # B.B.A.-Honours-A
    '32': 'BBA',  # B.B.A.-Honours-B
    '33': 'BBA',  # B.B.A.-Honours(Business Analytics)
    '41': 'CSC',  # B.C.A.-Honours-A
    '42': 'CSC',  # B.C.A.-Honours-B
    '51': 'BOT',  # B.Sc.-Honours(Botany)
    '52': 'ZOO',  # B.Sc.-Honours(Zoology)
    '61': 'MAT',  # B.Sc.-Honours(Mathematics)
    '62': 'CHE',  # B.Sc.-Honours(Chemistry)
    '63': 'PHY',  # B.Sc.-Honours(Physics)
    '64': 'ELE',  # B.Sc.-Honours(Electronics)
    '65': 'STA',  # B.Sc.-Honours(Statistics)
    '71': 'CSC',  # B.Sc.-Honours(Computer Science)-A
    '72': 'CSC',  # B.Sc.-Honours(Computer Science)-B
    '73': 'CSC',  # B.Sc.-Honours(Computer Science)-C
    '74': 'DSAI', # B.Sc.-Honours(Data Science)
    '75': 'DSAI', # B.Sc.-Honours(Data Analytics)
    '76': 'CSC',  # B.Sc.-Honours(CS and Cognitive Systems)
    '77': 'DSAI', # B.Sc.-Honours(Artificial Intelligence)
}

def get_file_path(filename):
    """Get full path to file in project directories."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check multiple possible locations (exact match)
    locations = [
        os.path.join(base_dir, 'file', filename),
        os.path.join(base_dir, filename),
        os.path.join(base_dir, 'keep', filename),
    ]
    
    for loc in locations:
        if os.path.exists(loc):
            return loc
    
    # Try glob pattern for versioned files (with spaces and parentheses)
    for loc_dir in [os.path.join(base_dir, 'file'), base_dir, os.path.join(base_dir, 'keep')]:
        # Handle filenames like "student_info" to find "student_info (3).csv"
        base_name = filename.replace('.csv', '')
        pattern = os.path.join(loc_dir, f"{base_name}*")
        matches = glob.glob(pattern)
        # Filter to only .csv files
        csv_matches = [m for m in matches if m.endswith('.csv')]
        if csv_matches:
            return sorted(csv_matches)[-1]  # Return latest version
    
    return None


def import_departments():
    """Import departments from hod_details.csv"""
    print("\n[1/4] Importing Departments and HODs...")
    
    csv_path = get_file_path('hod_details.csv')
    if not csv_path:
        print("    ⚠ hod_details.csv not found, using defaults")
        return import_default_departments()
    
    print(f"    Using: {csv_path}")
    count_created = 0
    count_updated = 0
    
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            dept_name = row.get('Department Name', '').strip()
            dept_code = row.get('Department Code', '').strip()
            hod_name = row.get('HOD Name', '').strip()
            hod_phone = row.get('Phone', '').strip()
            hod_email = row.get('Email', '').strip().lower()
            
            if not dept_code:
                continue
            
            # Create or update department
            dept = Department.query.filter_by(code=dept_code).first()
            if not dept:
                dept = Department(name=dept_name, code=dept_code)
                db.session.add(dept)
                db.session.flush()  # Get the ID
                count_created += 1
            else:
                dept.name = dept_name
                count_updated += 1
            
            # Create or update HOD user for this department
            if hod_email:
                hod_role = Role.query.filter_by(name='HOD').first()
                if not hod_role:
                    hod_role = Role(name='HOD', description='Head of Department')
                    db.session.add(hod_role)
                    db.session.flush()
                
                hod_user = User.query.filter_by(email=hod_email).first()
                if not hod_user:
                    hod_user = User(
                        email=hod_email,
                        password_hash=hash_password('hod123'),
                        full_name=hod_name,
                        role_id=hod_role.id,
                        employee_id=f"HOD-{dept_code}",
                        assigned_department_id=dept.id,
                        phone=hod_phone,
                        profile_completed=True,
                        is_temp_password=True,
                        registration_status='APPROVED'
                    )
                    db.session.add(hod_user)
                    print(f"    ✓ Created HOD: {hod_name} for {dept_name}")
                else:
                    hod_user.full_name = hod_name
                    hod_user.phone = hod_phone
                    hod_user.assigned_department_id = dept.id
                    if not hod_user.role_id:
                        hod_user.role_id = hod_role.id
    
    db.session.commit()
    print(f"    Departments - Created: {count_created}, Updated: {count_updated}")
    return True


def import_default_departments():
    """Import default departments if CSV not found"""
    default_depts = [
        ('Economics', 'ECO'),
        ('Commerce', 'COM'),
        ('Business Administration', 'BBA'),
        ('Computer Science', 'CSC'),
        ('Data Science & AI', 'DSAI'),
        ('Mathematics', 'MAT'),
        ('Statistics', 'STA'),
        ('Physics', 'PHY'),
        ('Chemistry', 'CHE'),
        ('Electronics', 'ELE'),
        ('Botany', 'BOT'),
        ('Zoology', 'ZOO'),
        ('English', 'ENG'),
        ('Telugu', 'TEL'),
        ('Hindi', 'HIN'),
        ('Physical Education', 'PED'),
    ]
    
    count = 0
    for name, code in default_depts:
        existing = Department.query.filter_by(code=code).first()
        if not existing:
            dept = Department(name=name, code=code)
            db.session.add(dept)
            count += 1
    
    db.session.commit()
    print(f"    Default departments created: {count}")
    return True


def import_students():
    """Import students from student_info CSV"""
    print("\n[2/4] Importing Students...")
    
    csv_path = get_file_path('student_info')
    if not csv_path:
        print("    ⚠ student_info CSV not found")
        return False
    
    print(f"    Using: {csv_path}")
    count_created = 0
    count_updated = 0
    
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            roll_no = (row.get('rollno') or '').strip().lower()
            if not roll_no:
                continue
            
            pcode = (row.get('pcode') or '').strip()
            dept_code = PCODE_TO_DEPT.get(pcode, '')
            
            # Find department
            dept = Department.query.filter_by(code=dept_code).first() if dept_code else None
            dept_name = dept.name if dept else (row.get('pshort') or '').strip()
            
            profile_data = {
                'rollNo': roll_no.upper(),
                'studentName': (row.get('sname') or '').strip(),
                'fatherName': (row.get('fname') or '').strip(),
                'motherName': (row.get('mname') or '').strip(),
                'joiningYear': (row.get('jyear') or '').strip(),
                'caste': (row.get('caste') or '').strip(),
                'pcode': pcode,
                'program': (row.get('pshort') or '').strip(),
                'aadharNo': (row.get('aadharno') or '').strip(),
                'dob': (row.get('dob') or '').strip(),
                'gender': (row.get('gender') or '').strip(),
                'currentSem': (row.get('currsem') or '').strip(),
                'mobileNo': (row.get('mobileno') or '').strip(),
                'section': (row.get('secl') or '').strip(),
                'profileImage': (row.get('profile_image') or '').strip(),
                'departmentCode': dept_code,
                'departmentId': dept.id if dept else None,
                'departmentName': dept_name,
            }
            
            # Check for existing student
            student = Student.query.filter_by(lookup_key=roll_no).first()
            
            if student:
                # Merge profile data
                current_profile = student.profile or {}
                student.profile = {**current_profile, **profile_data}
                student.department = dept_name
                student.updated_at = datetime.utcnow()
                count_updated += 1
            else:
                new_student = Student(
                    lookup_key=roll_no,
                    department=dept_name,
                    profile=profile_data
                )
                db.session.add(new_student)
                count_created += 1
            
            if (count_created + count_updated) % 200 == 0:
                db.session.commit()
                print(f"    Processed {count_created + count_updated} students...")
    
    db.session.commit()
    print(f"    Students - Created: {count_created}, Updated: {count_updated}")
    return True


def import_programs():
    """Import program information for mapping"""
    print("\n[3/4] Importing Programs...")
    
    csv_path = get_file_path('program_info')
    if not csv_path:
        print("    ⚠ program_info CSV not found, skipping")
        return False
    
    print(f"    Using: {csv_path}")
    # Programs are used for mapping, already handled via PCODE_TO_DEPT
    print("    ✓ Program mapping loaded (built-in)")
    return True


def seed_activity_leads():
    """Seed sample activity leads if not present"""
    print("\n[4/4] Seeding Activity Leads...")
    
    coordinator_role = Role.query.filter_by(name='FACULTY_COORDINATOR').first()
    if not coordinator_role:
        coordinator_role = Role(name='FACULTY_COORDINATOR', description='Coordinator for a specific activity')
        db.session.add(coordinator_role)
        db.session.flush()
    
    # Default activity leads
    activity_leads = [
        ('NCC', 'Dr. K. Ramesh', 'ncc.coordinator@pbsiddhartha.ac.in', '9876543210'),
        ('NSS', 'Dr. P. Srinivas', 'nss.coordinator@pbsiddhartha.ac.in', '9876543211'),
        ('Sports', 'Dr. T.V. Bala Krishna Reddy', 'sports.coordinator@pbsiddhartha.ac.in', '9963992102'),
        ('Culturals', 'Dr. M. Lakshmi', 'culturals.coordinator@pbsiddhartha.ac.in', '9876543213'),
        ('GYM', 'Sri K. Venkat', 'gym.coordinator@pbsiddhartha.ac.in', '9876543214'),
        ('YOGA', 'Dr. S. Prasad', 'yoga.coordinator@pbsiddhartha.ac.in', '9876543215'),
    ]
    
    count_created = 0
    for activity, name, email, phone in activity_leads:
        existing = User.query.filter_by(email=email).first()
        if not existing:
            user = User(
                email=email,
                password_hash=hash_password('coord123'),
                full_name=name,
                role_id=coordinator_role.id,
                employee_id=f"COORD-{activity.upper()[:3]}",
                assigned_activity_name=activity,
                phone=phone,
                profile_completed=True,
                is_temp_password=True,
                registration_status='APPROVED'
            )
            db.session.add(user)
            count_created += 1
            print(f"    ✓ Created coordinator: {name} for {activity}")
    
    db.session.commit()
    print(f"    Activity Leads created: {count_created}")
    return True


def run_all_imports():
    """Run all import operations"""
    print("=" * 60)
    print("COMPREHENSIVE DATA IMPORT")
    print("=" * 60)
    
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Ensure default roles exist
        default_roles = [
            ('CREATOR', 'Super Admin with all privileges'),
            ('HOD', 'Head of Department'),
            ('FACULTY_COORDINATOR', 'Coordinator for a specific activity'),
            ('STUDENT', 'Student'),
        ]
        for role_name, desc in default_roles:
            existing = Role.query.filter_by(name=role_name).first()
            if not existing:
                role = Role(name=role_name, description=desc)
                db.session.add(role)
        db.session.commit()
        
        # Run imports
        import_departments()
        import_students()
        import_programs()
        seed_activity_leads()
        
        # Summary
        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)
        print(f"Total Departments: {Department.query.count()}")
        print(f"Total Students: {Student.query.count()}")
        print(f"Total Users (HODs/Coordinators): {User.query.count()}")
        print("=" * 60)


if __name__ == "__main__":
    run_all_imports()
