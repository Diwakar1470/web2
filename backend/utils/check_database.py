#!/usr/bin/env python3
"""
Script to check what's inside the MySQL database
"""

import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='school_db'
    )
    cursor = conn.cursor(dictionary=True)
    
    # Check total students count
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE role_id = (SELECT id FROM roles WHERE name="STUDENT")')
    count = cursor.fetchone()
    print(f'\n📊 Total Students in Database: {count["total"]}')
    
    # Show all students with all details
    cursor.execute('''
        SELECT id, full_name, email, phone, registration_status, profile_completed
        FROM users 
        WHERE role_id = (SELECT id FROM roles WHERE name="STUDENT")
        LIMIT 50
    ''')
    
    print('\n📋 Student Records:')
    print('=' * 100)
    students = cursor.fetchall()
    if students:
        for row in students:
            print(f'ID: {row["id"]} | Name: {row["full_name"]} | Email: {row["email"]} | Phone: {row["phone"]} | Status: {row["registration_status"]}')
    else:
        print('❌ NO STUDENTS FOUND IN DATABASE')
    
    # Check if there are any students at all
    cursor.execute('''
        SELECT COUNT(*) as total FROM users
    ''')
    total_users = cursor.fetchone()
    print(f'\n📊 Total Users (All Roles): {total_users["total"]}')
    
    # Show all roles and their counts
    cursor.execute('SELECT id, name FROM roles')
    print('\n👥 Available Roles:')
    roles = cursor.fetchall()
    for row in roles:
        cursor.execute('SELECT COUNT(*) as cnt FROM users WHERE role_id = %s', (row['id'],))
        count = cursor.fetchone()
        print(f'  - {row["name"]}: {count["cnt"]} users')
    
    # Check all users (with role info)
    print('\n👥 All Users in Database:')
    print('=' * 100)
    cursor.execute('''
        SELECT u.id, u.full_name, u.email, r.name as role, u.registration_status
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY u.id
        LIMIT 30
    ''')
    
    for row in cursor.fetchall():
        print(f'ID: {row["id"]} | Name: {row["full_name"]} | Email: {row["email"]} | Role: {row["role"]} | Status: {row["registration_status"]}')
    
    # Check if students table exists
    cursor.execute("SHOW TABLES LIKE '%student%'")
    student_tables = cursor.fetchall()
    print(f'\n📋 Tables with "student" in name: {student_tables}')
    
    cursor.close()
    conn.close()
    
    print('\n✅ Database check complete!')
    
except Error as e:
    print(f'❌ Error: {e}')
except Exception as e:
    print(f'❌ Unexpected Error: {e}')
