import os
import sys
import csv
from datetime import datetime
import bcrypt
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Role, Department, hash_password

load_dotenv()

# Constants
HOD_DETAILS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hod_details.csv')

def read_hod_csv(file_path):
    """Read HOD details from CSV file"""
    hod_data = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                hod_data.append(row)
        return hod_data
    except FileNotFoundError:
        print(f"✗ Error: {file_path} not found.")
        sys.exit(1)

def migrate_data():
    with app.app_context():
        print("🔄 Starting HOD Data Migration to Unified User System...")
        
        # 1. Get HOD Role
        hod_role = Role.query.filter_by(name='HOD').first()
        if not hod_role:
            print("❌ Error: HOD role not found in database. Please run create_db.py first.")
            return

        # 2. Read CSV
        hod_data = read_hod_csv(HOD_DETAILS_FILE)
        print(f"📋 Read {len(hod_data)} HOD records from CSV.")

        # 3. Process each HOD
        for row in hod_data:
            dept_name = row['Department Name'].strip()
            dept_code = row['Department Code'].strip()
            hod_name = row['HOD Name'].strip()
            phone = row['Phone'].strip()
            email = row['Email'].strip()

            print(f"\n⚙️ Processing: {hod_name} ({dept_name})")

            # A. Ensure Department exists
            dept = Department.query.filter_by(code=dept_code).first()
            if not dept:
                dept = Department(name=dept_name, code=dept_code, description=f"Department of {dept_name}")
                db.session.add(dept)
                db.session.flush()
                print(f"  ✅ Created Department: {dept_name}")
            else:
                dept.name = dept_name # Update name if changed
                print(f"  ✅ Department exists: {dept_code}")

            # B. Ensure User exists or update
            user = User.query.filter_by(email=email).first()
            if not user:
                # Create new user
                user = User(
                    email=email,
                    password_hash=hash_password('hod123'),
                    full_name=hod_name,
                    role_id=hod_role.id,
                    assigned_department_id=dept.id,
                    phone=phone,
                    profile_completed=False,
                    is_temp_password=True,
                    registration_status='APPROVED'
                )
                db.session.add(user)
                print(f"  ✅ Created new HOD user: {email}")
            else:
                # Update existing user
                user.full_name = hod_name
                user.role_id = hod_role.id
                user.assigned_department_id = dept.id
                user.phone = phone
                user.is_active = True
                user.profile_completed = False
                user.is_temp_password = True
                user.password_hash = hash_password('hod123')
                print(f"  ✅ Updated existing HOD user: {email}")

        try:
            db.session.commit()
            print("\n" + "="*50)
            print("🎉 HOD Migration Completed Successfully!")
            print("="*50)
            print("Default credentials for HODs:")
            print("Department: [Select from dropdown]")
            print("Password: hod123")
            print("="*50)
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing to database: {e}")

if __name__ == "__main__":
    migrate_data()
