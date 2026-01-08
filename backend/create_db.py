import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db, Role, Department, User, hash_password

load_dotenv()

def create_database():
    """Creates the database and tables."""
    db.create_all()
    print("✓ Database and tables created.")

def seed_roles():
    """Seeds the roles table with default roles."""
    roles = [
        {'name': 'CREATOR', 'description': 'Super Admin with all privileges'},
        {'name': 'HOD', 'description': 'Head of Department'},
        {'name': 'FACULTY_COORDINATOR', 'description': 'Coordinator for a specific activity'},
        {'name': 'STUDENT', 'description': 'Student'}
    ]
    for role_data in roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
    db.session.commit()
    print("✓ Roles seeded.")

def seed_departments():
    """Seeds the departments table with initial data."""
    departments = [
        {'name': 'AI & DS', 'code': 'AIDT'},
        {'name': 'B.A.', 'code': 'BA'},
        {'name': 'B.Com.', 'code': 'BCom'},
        {'name': 'B.B.A.', 'code': 'BBA'},
        {'name': 'B.C.A.', 'code': 'BCA'},
        {'name': 'B.Sc.', 'code': 'BSc'}
    ]
    for dept_data in departments:
        dept = Department.query.filter_by(code=dept_data['code']).first()
        if not dept:
            dept = Department(name=dept_data['name'], code=dept_data['code'])
            db.session.add(dept)
    db.session.commit()
    print("✓ Departments seeded.")

def seed_creator():
    """Seeds the database with a creator user."""
    creator_email = 'creator@admin.com'
    creator = User.query.filter_by(email=creator_email).first()
    if not creator:
        creator_role = Role.query.filter_by(name='CREATOR').first()
        if creator_role:
            creator = User(
                full_name='Creator Admin',
                email=creator_email,
                password_hash=hash_password('admin'),
                role_id=creator_role.id,
                profile_completed=True
            )
            db.session.add(creator)
            db.session.commit()
            print("✓ Creator user seeded.")

if __name__ == '__main__':
    app = Flask(__name__)
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '1234')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'school_db')

    database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        create_database()
        seed_roles()
        seed_departments()
        seed_creator()
        print("✓ Database setup complete.")