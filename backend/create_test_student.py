#!/usr/bin/env python
"""
Create test student account for login testing
"""
from app import app, db, User, Role, hash_password
from datetime import datetime

def create_test_student():
    with app.app_context():
        # Get STUDENT role
        student_role = Role.query.filter_by(name='STUDENT').first()
        if not student_role:
            print("ERROR: STUDENT role not found!")
            return False
        
        # Create test student with the credentials shown in the form
        email = '237706p@pbsiddhartha.ac.in'
        admission_id = '12345'
        
        # Check if student already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"✓ Student already exists: {existing.full_name} ({existing.email})")
            print(f"  Admission ID: {existing.employee_id}")
            return True
        
        # Create new test student
        student = User(
            email=email,
            full_name='Pavan Kumar',
            employee_id=admission_id,
            role_id=student_role.id,
            password_hash=hash_password('test123'),
            is_active=True,
            profile_completed=True,
            created_at=datetime.utcnow()
        )
        db.session.add(student)
        db.session.commit()
        print(f"✓ Test student created!")
        print(f"  Email: {email}")
        print(f"  Admission ID: {admission_id}")
        print(f"  Password: test123")
        print(f"  Role: STUDENT")
        return True

if __name__ == '__main__':
    create_test_student()
