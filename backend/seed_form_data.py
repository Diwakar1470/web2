
import os
import csv
from datetime import datetime
from app import app, db, Department, User, Role, Activity, hash_password

def seed_data():
    with app.app_context():
        print("[*] Starting seeding process...")
        
        # 1. Ensure Roles exist
        roles = {
            'CREATOR': 'System Administrator',
            'STUDENT': 'Student',
            'HOD': 'Head of Department',
            'COORDINATOR': 'Faculty Coordinator'
        }
        role_objs = {}
        for r_name, r_desc in roles.items():
            role = Role.query.filter_by(name=r_name).first()
            if not role:
                role = Role(name=r_name, description=r_desc)
                db.session.add(role)
                db.session.flush()
            role_objs[r_name] = role
        db.session.commit()
        print("[+] Roles verified.")

        # 2. Seed Departments from hod_details.csv
        hod_details_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'hod_details.csv')
        if not os.path.exists(hod_details_path):
            # Try same dir
            hod_details_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hod_details.csv')
        
        if os.path.exists(hod_details_path):
            with open(hod_details_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Header: Department Name,Department Code,HOD Name,Phone,Email
                    dept_name = row['Department Name'].strip()
                    dept_code = row['Department Code'].strip()
                    hod_name = row['HOD Name'].strip()
                    hod_phone = row['Phone'].strip()
                    hod_email = row['Email'].strip().lower()

                    # Department
                    dept = Department.query.filter_by(code=dept_code).first()
                    if not dept:
                        dept = Department(name=dept_name, code=dept_code)
                        db.session.add(dept)
                        db.session.flush()
                    else:
                        dept.name = dept_name
                    
                    # HOD User
                    hod_user = User.query.filter_by(email=hod_email).first()
                    if not hod_user:
                        hod_user = User(
                            email=hod_email,
                            password_hash=hash_password('pb123'),
                            full_name=hod_name,
                            role_id=role_objs['HOD'].id,
                            employee_id=f"HOD_{dept_code}",
                            phone=hod_phone,
                            assigned_department_id=dept.id,
                            is_active=True,
                            registration_status='APPROVED',
                            profile_completed=True
                        )
                        db.session.add(hod_user)
                    else:
                        hod_user.full_name = hod_name
                        hod_user.phone = hod_phone
                        hod_user.assigned_department_id = dept.id
                
            db.session.commit()
            print("[+] Departments and HODs seeded from hod_details.csv.")
        else:
            print(f"[!] Warning: {hod_details_path} not found.")

        # 3. Seed Activities (Classes) from program_info (7).csv
        # Use the CSV at the root or under file/
        prog_info_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'program_info (7).csv')
        if not os.path.exists(prog_info_path):
             prog_info_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'program_info (7).csv')
        
        if os.path.exists(prog_info_path):
            with open(prog_info_path, newline='', encoding='utf-8') as f:
                # The file uses semicolon delimiter
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    # "pid";"pcode";"pname";"ptitle";"pshort";"pbatch";"pstatus";"pdate";"user";"ptime";"cname";"pdegree";"dept"
                    pname = row.get('pname', '').replace('"', '').strip()
                    pshort = row.get('pshort', '').replace('"', '').strip()
                    dept_code = row.get('dept', '').replace('"', '').strip()
                    pcode = row.get('pcode', '').replace('"', '').strip()
                    
                    if not pshort or not dept_code:
                        continue
                    
                    # Find department to linked activity if needed, though Activity.data stores code
                    activity = Activity.query.filter_by(name=pshort).first()
                    if not activity:
                        activity = Activity(
                            name=pshort,
                            data={
                                'programName': pname,
                                'department': dept_code,
                                'pcode': pcode,
                                'batch': row.get('pbatch', '').replace('"', '').strip(),
                                'degree': row.get('pdegree', '').replace('"', '').strip()
                            }
                        )
                        db.session.add(activity)
                    else:
                        activity.data = {
                            'programName': pname,
                            'department': dept_code,
                            'pcode': pcode,
                            'batch': row.get('pbatch', '').replace('"', '').strip(),
                            'degree': row.get('pdegree', '').replace('"', '').strip()
                        }
            db.session.commit()
            print("[+] Classes seeded from program_info (7).csv.")
        else:
            print(f"[!] Warning: {prog_info_path} not found.")

        # 4. Seed Coordinators
        coordinators = [
            {'name': 'Lt. K.P.T. Vijaya Bhaskara Rao', 'email': 'ncc@pbsiddhartha.ac.in', 'activity': 'NCC', 'phone': '9848132101'},
            {'name': 'Mr. S. Rajesh', 'email': 'nss@pbsiddhartha.ac.in', 'activity': 'NSS', 'phone': '9502474508'},
            {'name': 'Capt. Ruhi', 'email': 'ruhi@pbsiddhartha.ac.in', 'activity': 'NCC', 'phone': '9123456789'},
            {'name': 'Sports Coordinator', 'email': 'sports@pbsiddhartha.ac.in', 'activity': 'SPORTS', 'phone': '8888888888'}
        ]

        for coord in coordinators:
            user = User.query.filter_by(email=coord['email']).first()
            if not user:
                user = User(
                    email=coord['email'],
                    password_hash=hash_password('pb123'),
                    full_name=coord['name'],
                    role_id=role_objs['COORDINATOR'].id,
                    employee_id=f"CO_{coord['activity']}_{coord['email'].split('@')[0]}",
                    phone=coord['phone'],
                    assigned_activity_name=coord['activity'],
                    is_active=True,
                    registration_status='APPROVED',
                    profile_completed=True
                )
                db.session.add(user)
        db.session.commit()
        print("[+] Default Coordinators seeded.")

        print("[!] Seeding complete!")

if __name__ == "__main__":
    seed_data()
