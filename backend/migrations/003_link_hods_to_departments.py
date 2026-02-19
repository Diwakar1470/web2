"""
Migration script to link HODs to departments
"""

from app import app, db, User, Role, Department

def migrate_hods_to_departments():
    """Assign HODs to their respective departments"""
    with app.app_context():
        try:
            print("[MIGRATION] Linking HODs to Departments...")
            
            # Get HOD role
            hod_role = Role.query.filter_by(name='HOD').first()
            if not hod_role:
                print("[WARNING] HOD role not found")
                return
            
            # HOD mappings from hod_rbac_config.json
            hod_mappings = {
                'DSAI': {
                    'hod_id': '3069',
                    'hod_name': 'Dr.K.Udaya Sri',
                    'email': 'hod@pbsiddhartha.ac.in',
                    'phone': '9490965267'
                },
                'CSC': {
                    'hod_id': '5018',
                    'hod_name': 'Dr.T.S.Ravi kiran',
                    'email': 'ravi@pbsiddhartha.ac.in',
                    'phone': '9999999999'
                },
                'BA': {
                    'hod_id': '2001',
                    'hod_name': 'Sri K.Perachary',
                    'email': 'ba@pbsiddhartha.ac.in',
                    'phone': '9963043362'
                },
                'BCom': {
                    'hod_id': '2035',
                    'hod_name': 'Sri K.Narayana Rao',
                    'email': 'bcom@pbsiddhartha.ac.in',
                    'phone': '9885038196'
                },
                'BBA': {
                    'hod_id': '2002',
                    'hod_name': 'Sri V.Babu Rao',
                    'email': 'bba@pbsiddhartha.ac.in',
                    'phone': '9948221110'
                },
                'BCA': {
                    'hod_id': '3011',
                    'hod_name': 'Dr.T.S.Krishna',
                    'email': 'bca@pbsiddhartha.ac.in',
                    'phone': '9700003993'
                },
                'BSc': {
                    'hod_id': '3004',
                    'hod_name': 'Smt.S.Siva Naga Lakshmi',
                    'email': 'bsc@pbsiddhartha.ac.in',
                    'phone': '9703315452'
                }
            }
            
            # Link HODs to departments
            for dept_code, hod_info in hod_mappings.items():
                dept = Department.query.filter_by(code=dept_code).first()
                if not dept:
                    print(f"  ⚠ Department {dept_code} not found")
                    continue
                
                # Check if HOD user exists
                hod_user = User.query.filter_by(email=hod_info['email']).first()
                
                if hod_user:
                    # Update existing HOD
                    hod_user.assigned_department_id = dept.id
                    hod_user.phone = hod_info['phone']
                    hod_user.full_name = hod_info['hod_name']
                    print(f"  ✓ Updated HOD for {dept_code}: {hod_info['hod_name']}")
                else:
                    # Create new HOD
                    from app import hash_password
                    hod_user = User(
                        email=hod_info['email'],
                        password_hash=hash_password('hod123'),
                        full_name=hod_info['hod_name'],
                        role_id=hod_role.id,
                        assigned_department_id=dept.id,
                        employee_id=hod_info['hod_id'],
                        phone=hod_info['phone'],
                        is_active=True,
                        profile_completed=True,
                        is_temp_password=False,
                        registration_status='APPROVED'
                    )
                    db.session.add(hod_user)
                    print(f"  ✓ Created HOD for {dept_code}: {hod_info['hod_name']}")
            
            db.session.commit()
            print("[OK] HOD to Department mapping complete!")
            
            # Verify mappings
            print("\n[VERIFY] Current HOD-Department Mappings:")
            all_depts = Department.query.all()
            for dept in all_depts:
                hod = User.query.filter_by(assigned_department_id=dept.id, role_id=hod_role.id).first()
                if hod:
                    print(f"  {dept.name:20} → {hod.full_name:25} ({hod.phone})")
                else:
                    print(f"  {dept.name:20} → NOT ASSIGNED")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_hods_to_departments()
