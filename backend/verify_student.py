#!/usr/bin/env python
"""Verify test student credentials"""
from app import app, db, User, Role

with app.app_context():
    user = User.query.filter_by(email='237706p@pbsiddhartha.ac.in').first()
    if user:
        role = Role.query.get(user.role_id)
        print('✓ Student found:')
        print(f'  Name: {user.full_name}')
        print(f'  Email: {user.email}')
        print(f'  Admission ID: {user.employee_id}')
        print(f'  Role: {role.name if role else "Unknown"}')
        print(f'  Active: {user.is_active}')
        print(f'  Profile Complete: {user.profile_completed}')
        print('\nLogin Credentials for Testing:')
        print(f'  Email: {user.email}')
        print(f'  Admission ID: {user.employee_id}')
        print(f'  Password: test123')
    else:
        print('✗ Student not found')
