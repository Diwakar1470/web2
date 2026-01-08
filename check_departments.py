"""
Check and populate departments in database
"""

import sys
sys.path.insert(0, 'backend')

from backend.app import app, db, Department

def check_and_populate_departments():
    with app.app_context():
        try:
            print("[CHECK] Current Departments in Database:")
            depts = Department.query.all()
            
            if not depts:
                print("  No departments found. Creating default departments...")
                
                default_depts = [
                    {'name': 'AI and Data Science', 'code': 'DSAI'},
                    {'name': 'Computer Science', 'code': 'CSC'},
                    {'name': 'Bachelor of Arts', 'code': 'BA'},
                    {'name': 'Bachelor of Commerce', 'code': 'BCom'},
                    {'name': 'Bachelor of Business Administration', 'code': 'BBA'},
                    {'name': 'Bachelor of Computer Applications', 'code': 'BCA'},
                    {'name': 'Bachelor of Science', 'code': 'BSc'},
                ]
                
                for dept_data in default_depts:
                    dept = Department(name=dept_data['name'], code=dept_data['code'])
                    db.session.add(dept)
                    print(f"  ✓ Added: {dept_data['name']} ({dept_data['code']})")
                
                db.session.commit()
                print("[OK] Departments created successfully!")
            else:
                print(f"  Found {len(depts)} departments:")
                for d in depts:
                    print(f"    {d.id}: {d.name} ({d.code})")
                    
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_and_populate_departments()
