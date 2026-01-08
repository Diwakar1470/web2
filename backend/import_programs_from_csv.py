"""
Import programs and departments from CSV and seed database.
This script clears existing Departments and Activities, then repopulates
from the CSV in file/program_info*.csv.
"""

import os
import csv
import glob
from datetime import datetime

from app import app, db, Department, Activity

# Map pcode ranges to department code/name
DEPT_RULES = [
    ((11,), ("BA", "Bachelor of Arts")),
    (tuple(range(21, 29)), ("BCom", "Bachelor of Commerce")),
    (tuple(range(31, 34)), ("BBA", "Bachelor of Business Administration")),
    (tuple(range(41, 43)), ("BCA", "Bachelor of Computer Applications")),
    (tuple(range(51, 66)), ("BSc", "Bachelor of Science")),
    # Computer Science under B.Sc.
    ((71, 72, 73, 76), ("CSC", "Computer Science")),
    # AI & Data Science tracks
    ((74, 75, 77), ("DSAI", "AI and Data Science")),
]


def pcode_to_department(pcode: int):
    for codes, (code, name) in DEPT_RULES:
        if pcode in codes:
            return code, name
    # Default: treat as BSc if unknown science code
    return "BSc", "Bachelor of Science"


def load_latest_program_csv():
    """Find the latest program_info*.csv in file/ directory."""
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "file")
    paths = sorted(glob.glob(os.path.join(base, "program_info*.csv")))
    if not paths:
        # Fallback to the provided file name with parentheses
        candidate = os.path.join(base, "program_info (4).csv")
        if os.path.exists(candidate):
            return candidate
        raise FileNotFoundError("No program_info CSV found in file/ directory")
    return paths[-1]


def import_programs(csv_path: str):
    count_depts_created = 0
    count_classes_created = 0
    with app.app_context():
        # 1) Clear existing classes only (keep departments to preserve FK integrity)
        db.session.query(Activity).delete()
        db.session.commit()

        # 2) Read CSV and collect depts + classes
        # Load existing departments keyed by code
        existing_by_code = {d.code: d for d in Department.query.all()}
        departments = dict(existing_by_code)  # working map: code -> Department
        classes = []

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    pcode_s = (row.get('pcode') or '').strip()
                    if not pcode_s:
                        continue
                    pcode = int(pcode_s)
                except Exception:
                    continue

                pname = (row.get('pname') or '').strip()
                pshort = (row.get('pshort') or '').strip()
                ptitle = (row.get('ptitle') or '').strip()
                pstatus = (row.get('pstatus') or '').strip() or 'Running'
                pdegree = (row.get('pdegree') or '').strip()
                pbatch = (row.get('pbatch') or '').strip()

                dept_code, dept_name = pcode_to_department(pcode)

                # ensure department
                if dept_code not in departments:
                    dept = Department(name=dept_name, code=dept_code, description=f"Imported from CSV on {datetime.utcnow().isoformat()}Z")
                    db.session.add(dept)
                    db.session.flush()  # get id
                    departments[dept_code] = dept
                    count_depts_created += 1
                else:
                    # Update name if changed
                    dept = departments[dept_code]
                    if dept.name != dept_name:
                        dept.name = dept_name

                # build activity (class)
                act = Activity(
                    name=pshort or pname or f"Program-{pcode}",
                    data={
                        'programName': pname,
                        'programCode': pcode,
                        'pshort': pshort,
                        'ptitle': ptitle,
                        'degree': pdegree,
                        'batch': pbatch,
                        'status': pstatus or 'Running',
                        'department': dept.code,
                        'departmentName': dept.name
                    },
                )
                db.session.add(act)
                count_classes_created += 1

        db.session.commit()

    return count_depts_created, count_classes_created


if __name__ == "__main__":
    path = load_latest_program_csv()
    print(f"[IMPORT] Using CSV: {path}")
    d, c = import_programs(path)
    print(f"[OK] Imported Departments: {d}, Classes: {c}")
