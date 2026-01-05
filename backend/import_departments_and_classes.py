"""
Import Departments and Classes from CSV to Database
This script safely imports department and class data from CSV files into the database
"""

import csv
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db, Department, Activity

def import_departments_from_csv():
    """
    Import departments from the program_info CSV file.
    Creates entries in the departments table and activities table.
    """
    
    csv_file = Path(__file__).parent.parent / 'file' / 'program_info (4).csv'
    
    if not csv_file.exists():
        print(f"Error: CSV file not found at {csv_file}")
        return False
    
    try:
        with app.app_context():
            departments_created = 0
            activities_created = 0
            activities_processed = set()
            
            print("\n" + "="*80)
            print("IMPORTING DEPARTMENTS AND CLASSES FROM CSV")
            print("="*80)
            
            # Read CSV and extract unique programs
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        program_id = row['pid'].strip()
                        program_code = row['pcode'].strip()
                        program_name = row['pname'].strip()
                        program_title = row['ptitle'].strip()
                        program_short = row['pshort'].strip()
                        batch = row['pbatch'].strip() if row['pbatch'] else '2024'
                        status = row['pstatus'].strip() if row['pstatus'] else 'Running'
                        
                        # Extract department from program title (e.g., "B.A.-Honours" -> "BA")
                        if '-' in program_title:
                            dept_name = program_title.split('-')[0].strip()
                        else:
                            dept_name = program_title
                        
                        # Create activity entry (class/program)
                        activity_name = f"{program_short} ({batch})"
                        
                        # Check if activity already exists
                        existing_activity = Activity.query.filter_by(
                            name=program_short
                        ).first()
                        
                        if not existing_activity:
                            activity = Activity(
                                name=program_short,
                                data={
                                    'programId': program_id,
                                    'programCode': program_code,
                                    'programTitle': program_title,
                                    'programName': program_name,
                                    'description': f"{program_name} - {program_title}",
                                    'batch': batch,
                                    'status': status,
                                    'department': dept_name,
                                    'category': 'Academic'
                                }
                            )
                            db.session.add(activity)
                            activities_created += 1
                            activities_processed.add(program_short)
                            print(f"  [CREATED] Activity: {program_short} ({program_name})")
                        else:
                            activities_processed.add(program_short)
                    
                    except Exception as e:
                        print(f"  [ERROR] Processing row {program_id}: {str(e)}")
                        continue
            
            # Commit all activities
            db.session.commit()
            print(f"\n[OK] Activities Created: {activities_created}")
            
            # Get unique departments and create department entries
            print("\nProcessing Departments...")
            
            # Department mapping from CSV data
            department_codes = {
                'B.A.': 'BA',
                'B.Com.': 'BCom',
                'B.B.A.': 'BBA',
                'B.C.A.': 'BCA',
                'B.Sc.': 'BSc'
            }
            
            for full_name, code in department_codes.items():
                # Check if department already exists
                existing_dept = Department.query.filter_by(code=code).first()
                
                if not existing_dept:
                    # Create department
                    dept = Department(
                        name=full_name.replace('.', ''),
                        code=code,
                        description=f"{full_name} Programs"
                    )
                    db.session.add(dept)
                    departments_created += 1
                    print(f"  [CREATED] Department: {full_name} ({code})")
            
            db.session.commit()
            print(f"\n[OK] Departments Created: {departments_created}")
            
            print("\n" + "="*80)
            print("IMPORT SUMMARY")
            print("="*80)
            print(f"Departments Created: {departments_created}")
            print(f"Classes/Activities Created: {activities_created}")
            print(f"Total Unique Classes Processed: {len(activities_processed)}")
            print("="*80)
            
            return True
    
    except Exception as e:
        print(f"Error importing departments: {str(e)}")
        return False


def verify_import():
    """Verify the imported data"""
    
    try:
        with app.app_context():
            print("\n" + "="*80)
            print("VERIFICATION: Departments and Classes in Database")
            print("="*80)
            
            # Verify departments
            depts = Department.query.all()
            print(f"\nDepartments in Database: {len(depts)}")
            for dept in depts:
                print(f"  • {dept.name} ({dept.code})")
            
            # Verify activities
            activities = Activity.query.all()
            print(f"\nClasses/Activities in Database: {len(activities)}")
            
            # Group by category
            by_category = {}
            for activity in activities:
                cat = activity.data.get('department', 'Uncategorized') if activity.data else 'Uncategorized'
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(activity)
            
            for cat in sorted(by_category.keys()):
                print(f"\n  {cat}:")
                for activity in by_category[cat]:
                    status = activity.data.get('status', 'Unknown') if activity.data else 'Unknown'
                    desc = activity.data.get('description', 'N/A') if activity.data else 'N/A'
                    print(f"    • {activity.name} - {desc} ({status})")
            
            print("\n" + "="*80)
            return True
    
    except Exception as e:
        print(f"Error verifying import: {str(e)}")
        return False


def update_hod_departments():
    """
    Assign departments to existing HODs.
    Maps HOD email to departments based on faculty data.
    """
    
    try:
        with app.app_context():
            from app import User, Role
            
            print("\n" + "="*80)
            print("ASSIGNING DEPARTMENTS TO HODs")
            print("="*80)
            
            # HOD to department mapping (from faculty CSV analysis)
            hod_mappings = {
                'hod@pbsiddhartha.ac.in': 'BA',  # Generic HOD
                'ruhi@pbsiddhartha.ac.in': 'BA',  # Assign to BA
            }
            
            hod_role = Role.query.filter_by(name='HOD').first()
            if not hod_role:
                print("Error: HOD role not found in database")
                return False
            
            assignments_made = 0
            
            for hod_email, dept_code in hod_mappings.items():
                # Find HOD user
                hod_user = User.query.filter_by(email=hod_email).first()
                
                if not hod_user:
                    print(f"  [SKIP] HOD not found: {hod_email}")
                    continue
                
                # Find department
                dept = Department.query.filter_by(code=dept_code).first()
                
                if not dept:
                    print(f"  [ERROR] Department not found: {dept_code}")
                    continue
                
                # Assign department to HOD
                if hod_user.assigned_department_id != dept.id:
                    hod_user.assigned_department_id = dept.id
                    db.session.add(hod_user)
                    assignments_made += 1
                    print(f"  [ASSIGNED] {hod_email} = {dept.name}")
            
            db.session.commit()
            print(f"\n[OK] Department Assignments Made: {assignments_made}")
            print("="*80)
            
            return True
    
    except Exception as e:
        print(f"Error assigning departments: {str(e)}")
        return False


if __name__ == '__main__':
    print("\n[IMPORT] Department and Class Import Utility")
    print("="*80)
    
    # Step 1: Import departments and classes
    success = import_departments_from_csv()
    
    if success:
        # Step 2: Verify import
        verify_import()
        
        # Step 3: Assign departments to HODs
        update_hod_departments()
        
        print("\n[SUCCESS] All operations completed successfully!")
    else:
        print("\n[FAILED] Import failed. Check the errors above.")
        sys.exit(1)
