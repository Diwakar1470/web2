"""
Setup and Update Departments in Database
This script ensures correct departments exist and removes deprecated ones
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db, Department

def remove_deprecated_departments():
    """Remove CSE and ECE departments if they exist"""
    try:
        with app.app_context():
            print("\n" + "="*80)
            print("REMOVING DEPRECATED DEPARTMENTS (CSE, ECE)")
            print("="*80)
            
            deprecated_codes = ['CSE', 'ECE']
            removed_count = 0
            
            for code in deprecated_codes:
                dept = Department.query.filter_by(code=code).first()
                if dept:
                    print(f"  [FOUND] Department: {dept.name} ({dept.code})")
                    # Check if any users are assigned to this department
                    from app import User
                    users = User.query.filter_by(assigned_department_id=dept.id).all()
                    
                    if users:
                        print(f"    ⚠️  {len(users)} users assigned to this department:")
                        for user in users:
                            print(f"       - {user.full_name} ({user.email})")
                        print(f"    ℹ️  Consider reassigning these users before deletion")
                    
                    db.session.delete(dept)
                    removed_count += 1
                    print(f"  [REMOVED] {dept.name} ({code})")
                else:
                    print(f"  [NOT FOUND] Department with code: {code}")
            
            if removed_count > 0:
                db.session.commit()
                print(f"\n[OK] {removed_count} deprecated departments removed")
            else:
                print("\n[OK] No deprecated departments found")
            
            print("="*80)
            return True
    
    except Exception as e:
        print(f"❌ Error removing deprecated departments: {str(e)}")
        db.session.rollback()
        return False


def create_ai_department():
    """Create or update AI and Data Science department"""
    try:
        with app.app_context():
            print("\n" + "="*80)
            print("ENSURING AI AND DATA SCIENCE DEPARTMENT EXISTS")
            print("="*80)
            
            # Check if AIDT department exists
            dept = Department.query.filter_by(code='AIDT').first()
            
            if dept:
                print(f"  [FOUND] Department: {dept.name} ({dept.code})")
                print(f"  [OK] AI and Data Science department already exists")
            else:
                # Create AI and Data Science department
                dept = Department(
                    name='AI and Data Science',
                    code='AIDT',
                    description='B.Tech - Artificial Intelligence and Data Science'
                )
                db.session.add(dept)
                db.session.commit()
                print(f"  [CREATED] AI and Data Science (AIDT)")
                print(f"  [OK] Department created with ID: {dept.id}")
            
            print("="*80)
            return True
    
    except Exception as e:
        print(f"❌ Error creating AI department: {str(e)}")
        db.session.rollback()
        return False


def create_academic_departments():
    """Ensure all academic departments exist"""
    try:
        with app.app_context():
            print("\n" + "="*80)
            print("ENSURING ACADEMIC DEPARTMENTS EXIST")
            print("="*80)
            
            academic_depts = {
                'BA': 'Bachelor of Arts',
                'BCom': 'Bachelor of Commerce',
                'BBA': 'Bachelor of Business Administration',
                'BCA': 'Bachelor of Computer Applications',
                'BSc': 'Bachelor of Science'
            }
            
            created_count = 0
            
            for code, name in academic_depts.items():
                dept = Department.query.filter_by(code=code).first()
                
                if dept:
                    print(f"  [FOUND] {name} ({code})")
                else:
                    dept = Department(
                        name=name,
                        code=code,
                        description=f"{name} Programs"
                    )
                    db.session.add(dept)
                    created_count += 1
                    print(f"  [CREATED] {name} ({code})")
            
            if created_count > 0:
                db.session.commit()
                print(f"\n[OK] {created_count} new academic departments created")
            else:
                print(f"\n[OK] All academic departments already exist")
            
            print("="*80)
            return True
    
    except Exception as e:
        print(f"❌ Error creating academic departments: {str(e)}")
        db.session.rollback()
        return False


def verify_departments():
    """Verify all departments are correctly configured"""
    try:
        with app.app_context():
            print("\n" + "="*80)
            print("DEPARTMENT VERIFICATION")
            print("="*80)
            
            depts = Department.query.all()
            
            if not depts:
                print("  ⚠️  No departments found in database!")
                return False
            
            print(f"\nTotal Departments: {len(depts)}\n")
            
            # Group by type
            academic = []
            engineering = []
            other = []
            
            for dept in depts:
                if dept.code in ['BA', 'BCom', 'BBA', 'BCA', 'BSc']:
                    academic.append(dept)
                elif dept.code in ['AIDT', 'CSE', 'ECE']:
                    engineering.append(dept)
                else:
                    other.append(dept)
            
            if academic:
                print("Academic Departments:")
                for dept in sorted(academic, key=lambda d: d.code):
                    print(f"  ✓ {dept.name} ({dept.code})")
            
            if engineering:
                print("\nEngineering Departments:")
                for dept in sorted(engineering, key=lambda d: d.code):
                    status = "✓" if dept.code == 'AIDT' else "✗ [DEPRECATED]"
                    print(f"  {status} {dept.name} ({dept.code})")
            
            if other:
                print("\nOther Departments:")
                for dept in other:
                    print(f"  • {dept.name} ({dept.code})")
            
            # Check for deprecated departments
            deprecated = Department.query.filter(
                Department.code.in_(['CSE', 'ECE'])
            ).all()
            
            if deprecated:
                print("\n⚠️  WARNING: Deprecated departments found:")
                for dept in deprecated:
                    print(f"     • {dept.name} ({dept.code})")
                print("  Run 'remove_deprecated_departments()' to clean up")
                return False
            
            # Check that AIDT exists
            if not Department.query.filter_by(code='AIDT').first():
                print("\n⚠️  ERROR: AI and Data Science (AIDT) department not found!")
                return False
            
            print("\n✅ All departments configured correctly!")
            print("="*80)
            return True
    
    except Exception as e:
        print(f"❌ Error verifying departments: {str(e)}")
        return False


def main():
    """Run all setup steps"""
    print("\n" + "="*80)
    print("DEPARTMENT SETUP AND CLEANUP UTILITY")
    print("="*80)
    
    # Step 1: Remove deprecated departments
    if not remove_deprecated_departments():
        print("\n⚠️  Warning: Could not remove deprecated departments")
    
    # Step 2: Create AI department
    if not create_ai_department():
        print("\n❌ Failed to create AI department")
        return False
    
    # Step 3: Create academic departments
    if not create_academic_departments():
        print("\n❌ Failed to create academic departments")
        return False
    
    # Step 4: Verify all departments
    if verify_departments():
        print("\n[SUCCESS] Department setup completed successfully!")
        return True
    else:
        print("\n[PARTIAL] Department setup completed with warnings")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
