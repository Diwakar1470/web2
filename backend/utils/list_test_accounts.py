#!/usr/bin/env python3
"""
List all test accounts and credentials available in the database
"""

import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore
import json

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='school_db'
    )
    cursor = conn.cursor(dictionary=True)
    
    print("\n" + "="*100)
    print("📋 ALL TEST ACCOUNTS IN DATABASE")
    print("="*100)
    
    # Get all users with their roles
    cursor.execute('''
        SELECT 
            u.id,
            u.email,
            u.password_hash,
            u.full_name,
            u.phone,
            u.registration_status,
            u.profile_completed,
            u.is_active,
            r.name as role
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY r.name, u.id
    ''')
    
    users = cursor.fetchall()
    
    if not users:
        print("❌ No users found in database!")
    else:
        print(f"\n✅ Found {len(users)} test accounts:\n")
        
        # Group by role
        by_role = {}
        for user in users:
            role = user['role'] or 'NO_ROLE'
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(user)
        
        # Display by role
        for role in sorted(by_role.keys()):
            users_list = by_role[role]
            print(f"\n{'─'*100}")
            print(f"👤 {role} ({len(users_list)} account(s))")
            print(f"{'─'*100}")
            
            for user in users_list:
                print(f"\n  📧 Email:              {user['email']}")
                print(f"  � Full Name:          {user['full_name']}")
                print(f"  🔐 Hash:               {user['password_hash'][:50]}...")
                print(f"  📱 Phone:              {user['phone'] or 'N/A'}")
                print(f"  ✅ Status:             {user['registration_status']}")
                print(f"  🟢 Active:             {'Yes' if user['is_active'] else 'No'}")
                print(f"  📝 Profile Complete:   {'Yes' if user['profile_completed'] else 'No'}")
    
    # Summary statistics
    print(f"\n{'='*100}")
    print("📊 SUMMARY STATISTICS")
    print(f"{'='*100}")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM users')
    total_users = cursor.fetchone()['cnt']
    print(f"\n  ✓ Total Users: {total_users}")
    
    cursor.execute('SELECT r.name, COUNT(u.id) as cnt FROM users u LEFT JOIN roles r ON u.role_id = r.id GROUP BY r.name')
    role_counts = cursor.fetchall()
    print("\n  Users by Role:")
    for row in role_counts:
        print(f"    - {row['name']}: {row['cnt']}")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM students')
    total_students = cursor.fetchone()['cnt']
    print(f"\n  ✓ Total Students (in students table): {total_students}")
    
    # Quick login command examples
    print(f"\n{'='*100}")
    print("🚀 QUICK LOGIN EXAMPLES - DEFAULT TEST ACCOUNTS")
    print(f"{'='*100}\n")
    
    # Hardcoded default accounts (from app.py)
    default_accounts = [
        {'role': 'Creator (Super Admin)', 'email': 'create', 'password': '1234'},
        {'role': 'Creator (System Admin)', 'email': 'admin@pbsiddhartha.ac.in', 'password': 'admin123'},
        {'role': 'Student', 'email': 'student@pbsiddhartha.ac.in', 'password': 'student123'},
        {'role': 'HOD', 'email': 'hod@pbsiddhartha.ac.in', 'password': 'hod123'},
        {'role': 'Coordinator (NCC)', 'email': 'ruhi@pbsiddhartha.ac.in', 'password': 'ruhi123'},
    ]
    
    print("Use these credentials to login:\n")
    for acc in default_accounts:
        print(f"  {acc['role']:30} | {acc['email']:35} / {acc['password']}")

    
    # Student quick access
    print(f"\n{'─'*100}")
    print("🎓 STUDENT QUICK ACCESS (Roll Numbers)")
    print(f"{'─'*100}\n")
    
    cursor.execute('SELECT lookup_key FROM students LIMIT 10')
    sample_students = cursor.fetchall()
    print("Try these roll numbers in 'Student Quick Access':\n")
    for student in sample_students:
        print(f"  • {student['lookup_key']}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*100}\n")
    
except Error as e:
    print(f'❌ Database Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
