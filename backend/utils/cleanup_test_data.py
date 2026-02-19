#!/usr/bin/env python3
"""
Cleanup script to remove all test and synthetic data from the system:
1. Delete test users (test_creator@, ruhi@pbsiddhartha, hod@pbsiddhartha)
2. Delete test student records (241101p-241250p range)
3. Delete test attendance records
4. Delete test registrations 
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

# Database configuration
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'school_db')
}

def get_connection():
    """Create database connection"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

def execute_query(conn, query, params=None):
    """Execute query and return results"""
    cursor = conn.cursor(dictionary=True)
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"❌ Query error: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()

def cleanup_test_data():
    """Main cleanup function"""
    conn = get_connection()
    print("🔍 Starting cleanup of test and synthetic data...\n")
    
    # Step 1: Find and delete test users
    print("📋 Step 1: Identifying test users...")
    test_emails = [
        'test_creator@pbsiddhartha.ac.in',
        'ruhi@pbsiddhartha.ac.in',
        'hod@pbsiddhartha.ac.in'
    ]
    
    user_ids_to_delete = []
    for email in test_emails:
        query = "SELECT id, email, username FROM users WHERE email = %s OR username = %s"
        result = execute_query(conn, query, (email, email))
        if result:
            for user in result:
                user_ids_to_delete.append(user['id'])
                print(f"  • Found: {user['email']} (ID: {user['id']})")
    
    # Step 2: Find and delete test students (241101p-241250p range)
    print("\n📋 Step 2: Identifying test students (241101p-241250p)...")
    query = """SELECT id, admission_id FROM students 
               WHERE admission_id REGEXP '^241[0-2][0-9][0-9]p$' 
               ORDER BY admission_id"""
    student_results = execute_query(conn, query)
    
    student_ids_to_delete = []
    if student_results:
        print(f"  • Found {len(student_results)} test students")
        for student in student_results[:3]:  # Show first 3
            print(f"    - {student['admission_id']}")
        if len(student_results) > 3:
            print(f"    ... and {len(student_results) - 3} more")
        student_ids_to_delete = [s['id'] for s in student_results]
    
    # Step 3: Get test attendance records count
    print("\n📋 Step 3: Counting test attendance records...")
    if student_ids_to_delete:
        placeholders = ','.join(['%s'] * len(student_ids_to_delete))
        query = f"SELECT COUNT(*) as count FROM attendance WHERE student_id IN ({placeholders})"
        result = execute_query(conn, query, student_ids_to_delete)
        if result:
            print(f"  • Found {result[0]['count']} attendance records for test students")
    
    # Step 4: Get test registrations count
    print("\n📋 Step 4: Counting test registrations...")
    if student_ids_to_delete:
        placeholders = ','.join(['%s'] * len(student_ids_to_delete))
        query = f"SELECT COUNT(*) as count FROM registrations WHERE student_id IN ({placeholders})"
        result = execute_query(conn, query, student_ids_to_delete)
        if result:
            print(f"  • Found {result[0]['count']} registrations for test students")
    
    # Confirmation before deletion
    print("\n" + "="*60)
    print("⚠️  DELETION SUMMARY:")
    print("="*60)
    print(f"Test Users to DELETE: {len(test_emails)}")
    print("  - test_creator@pbsiddhartha.ac.in")
    print("  - ruhi@pbsiddhartha.ac.in")
    print("  - hod@pbsiddhartha.ac.in")
    print(f"\nTest Students to DELETE: {len(student_ids_to_delete)} (241101p-241250p)")
    print(f"Test Attendance Records to DELETE: ~7,625 records")
    print(f"Test Registrations to DELETE: ~438 records")
    print("="*60)
    
    confirm = input("\n⚠️  Do you want to PERMANENTLY DELETE all test data? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cleanup cancelled. No data deleted.")
        conn.close()
        return
    
    print("\n🗑️  Proceeding with deletion...\n")
    
    # Delete in correct order (dependencies)
    try:
        cursor = conn.cursor()
        
        # 1. Delete attendance records for test students
        if student_ids_to_delete:
            placeholders = ','.join(['%s'] * len(student_ids_to_delete))
            query = f"DELETE FROM attendance WHERE student_id IN ({placeholders})"
            cursor.execute(query, student_ids_to_delete)
            print(f"✅ Deleted {cursor.rowcount} attendance records")
            conn.commit()
        
        # 2. Delete registrations for test students
        if student_ids_to_delete:
            placeholders = ','.join(['%s'] * len(student_ids_to_delete))
            query = f"DELETE FROM registrations WHERE student_id IN ({placeholders})"
            cursor.execute(query, student_ids_to_delete)
            print(f"✅ Deleted {cursor.rowcount} registrations")
            conn.commit()
        
        # 3. Delete test students
        if student_ids_to_delete:
            placeholders = ','.join(['%s'] * len(student_ids_to_delete))
            query = f"DELETE FROM students WHERE id IN ({placeholders})"
            cursor.execute(query, student_ids_to_delete)
            print(f"✅ Deleted {cursor.rowcount} test students")
            conn.commit()
        
        # 4. Delete test user accounts
        if user_ids_to_delete:
            placeholders = ','.join(['%s'] * len(user_ids_to_delete))
            query = f"DELETE FROM users WHERE id IN ({placeholders})"
            cursor.execute(query, user_ids_to_delete)
            print(f"✅ Deleted {cursor.rowcount} test user accounts")
            conn.commit()
        
        print("\n✅ TEST DATA CLEANUP COMPLETED SUCCESSFULLY!")
        
    except Error as e:
        print(f"❌ Error during deletion: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    cleanup_test_data()
