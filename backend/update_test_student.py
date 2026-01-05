#!/usr/bin/env python
"""
Update existing test student email to match login form
"""
from app import app, db, User, hash_password

with app.app_context():
    # Get the existing test student
    student = User.query.filter_by(full_name='Test Student').first()
    if student:
        print(f"Found existing student: {student.full_name}")
        print(f"  Email: {student.email}")
        print(f"  Admission ID: {student.employee_id}")
        
        # Update email to match login form
        student.email = '237706p@pbsiddhartha.ac.in'
        student.password_hash = hash_password('test123')
        
        db.session.commit()
        print(f"\n✓ Updated student:")
        print(f"  Email: {student.email}")
        print(f"  Admission ID: {student.employee_id}")
        print(f"  Password: test123")
    else:
        print("No test student found - creating new one")
        student_role = User.query.filter_by(email='237706p@pbsiddhartha.ac.in').first()
        if student_role:
            print("Student with this email already exists")
        else:
            from datetime import datetime
            from app import Role
            role = Role.query.filter_by(name='STUDENT').first()
            if role:
                # Create student with a different admission ID
                new_student = User(
                    email='237706p@pbsiddhartha.ac.in',
                    full_name='Pavan Kumar',
                    employee_id='237706',  # Use roll number as admission ID
                    role_id=role.id,
                    password_hash=hash_password('test123'),
                    is_active=True,
                    profile_completed=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_student)
                db.session.commit()
                print(f"✓ Created new student:")
                print(f"  Email: {new_student.email}")
                print(f"  Admission ID: {new_student.employee_id}")
                print(f"  Password: test123")
