"""Run this to get real credentials for the stress test."""
import sys
sys.path.insert(0, 'd:/web1/web1/backend')
from app import app, db, Student, User, Role

with app.app_context():
    print("=== REAL STUDENT ROLL NUMBERS ===")
    students = Student.query.limit(15).all()
    for s in students:
        print(f'  "{s.lookup_key}",')

    print("\n=== REAL STAFF ACCOUNTS ===")
    users = User.query.filter_by(is_active=True).all()
    for u in users:
        role = Role.query.get(u.role_id)
        print(f'  Email: {u.email}  | Role: {role.name if role else "?"}  | TempPw: {u.is_temp_password}')
