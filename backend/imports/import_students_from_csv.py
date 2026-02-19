"""
Import student data from CSV to the database.
Maps 'rollno' to 'lookup_key' for easy login.
"""

import os
import csv
import glob
from datetime import datetime
from app import app, db, Student

def load_latest_student_csv():
    """Find the latest student_info*.csv in file/ directory."""
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "file")
    paths = sorted(glob.glob(os.path.join(base, "student_info*.csv")))
    if not paths:
        candidate = os.path.join(base, "student_info (3).csv")
        if os.path.exists(candidate):
            return candidate
        # Also check root directory as some structure might vary
        root_candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "student_info (3).csv")
        if os.path.exists(root_candidate):
            return root_candidate
        raise FileNotFoundError("No student_info CSV found in file/ directory")
    return paths[-1]

def import_students(csv_path: str):
    print(f"[*] Starting import from: {csv_path}")
    count_created = 0
    count_updated = 0
    
    with app.app_context():
        # Ensure table exists (though it should already)
        db.create_all()
        
        with open(csv_path, newline='', encoding='utf-8') as f:
            # Check if there are quotes or specific delimiters
            # The sample showed: "rid","rollno",...
            reader = csv.DictReader(f)
            
            for row in reader:
                roll_no = (row.get('rollno') or '').strip().lower()
                if not roll_no:
                    continue
                
                # Check for existing student by roll number
                student = Student.query.filter_by(lookup_key=roll_no).first()
                
                profile_data = {
                    'studentName': (row.get('sname') or '').strip(),
                    'fatherName': (row.get('fname') or '').strip(),
                    'motherName': (row.get('mname') or '').strip(),
                    'joiningYear': (row.get('jyear') or '').strip(),
                    'caste': (row.get('caste') or '').strip(),
                    'pcode': (row.get('pcode') or '').strip(),
                    'program': (row.get('pshort') or '').strip(),
                    'aadharNo': (row.get('aadharno') or '').strip(),
                    'dob': (row.get('dob') or '').strip(),
                    'gender': (row.get('gender') or '').strip(),
                    'currentSem': (row.get('currsem') or '').strip(),
                    'mobileNo': (row.get('mobileno') or '').strip(),
                    'rollNo': roll_no,
                    'section': (row.get('secl') or '').strip()
                }
                
                if student:
                    student.profile = profile_data
                    student.department = (row.get('pshort') or '').strip()
                    student.updated_at = datetime.utcnow()
                    count_updated += 1
                else:
                    new_student = Student(
                        lookup_key=roll_no,
                        department=(row.get('pshort') or '').strip(),
                        profile=profile_data
                    )
                    db.session.add(new_student)
                    count_created += 1
                
                if (count_created + count_updated) % 100 == 0:
                    db.session.commit()
                    print(f"[+] Processed {count_created + count_updated} records...")
                    
        db.session.commit()
        print(f"[!] Import complete!")
        print(f"    - Created: {count_created}")
        print(f"    - Updated: {count_updated}")
        print(f"    - Total: {count_created + count_updated}")

if __name__ == "__main__":
    try:
        csv_path = load_latest_student_csv()
        import_students(csv_path)
    except Exception as e:
        print(f"[ERROR] {str(e)}")
