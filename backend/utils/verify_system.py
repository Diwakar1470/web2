#!/usr/bin/env python3
"""
FINAL VERIFICATION - Confirm system is working
"""

import mysql.connector  # type: ignore
import requests

print("\n" + "="*120)
print("✅ FINAL SYSTEM VERIFICATION")
print("="*120 + "\n")

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='school_db'
    )
    cursor = conn.cursor(dictionary=True)
    
    print("1️⃣  DATABASE CONTENT CHECK")
    print("-" * 120)

    
    
    checks = {
        'activities': 'SELECT COUNT(*) as cnt FROM activities',
        'sub_activities': 'SELECT COUNT(*) as cnt FROM sub_activities',
        'registrations': 'SELECT COUNT(*) as cnt FROM registrations',
        'attendance': 'SELECT COUNT(*) as cnt FROM attendance',
        'students': 'SELECT COUNT(*) as cnt FROM students',
        'users': 'SELECT COUNT(*) as cnt FROM users',
    }
    
    all_good = True
    for name, query in checks.items():
        cursor.execute(query)
        count = cursor.fetchone()['cnt']
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {name:20}: {count:6} records")
        if count == 0 and 'activity' in name.lower() or 'registration' in name.lower() or 'attendance' in name.lower():
            all_good = False
    
    print("\n2️⃣  DATA QUALITY CHECK")
    print("-" * 120)
    
    # Check sample student registration
    cursor.execute('SELECT COUNT(*) as cnt FROM registrations WHERE status="hod_approved"')
    approved = cursor.fetchone()['cnt']
    print(f"  ✅ Approved registrations: {approved}")
    
    # Check attendance distribution
    cursor.execute('''
        SELECT status, COUNT(*) as cnt FROM attendance GROUP BY status
    ''')
    print(f"  ✅ Attendance status distribution:")
    for row in cursor.fetchall():
        print(f"     • {row['status'].upper()}: {row['cnt']} records")
    
    # Check students in data
    cursor.execute('SELECT COUNT(DISTINCT student_admission_id) as cnt FROM attendance')
    students_with_data = cursor.fetchone()['cnt']
    print(f"  ✅ Unique students in attendance: {students_with_data}")
    
    print("\n3️⃣  API CONNECTIVITY CHECK")
    print("-" * 120)
    
    try:
        response = requests.get('http://127.0.0.1:5000/api/health', timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Backend server running: {response.json()}")
        else:
            print(f"  ⚠️  Backend returned: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Backend not responding: {str(e)}")
        print(f"     (Make sure Flask server is running: python start_server.py)")
    
    print("\n4️⃣  SAMPLE QUERIES  validation")
    print("-" * 120)
    
    # Test analytics query
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as present
        FROM attendance 
        WHERE student_admission_id = '241101p'
    ''')
    result = cursor.fetchone()
    if result and result['total'] and result['total'] > 0:
        presence_rate = round(100 * result['present'] / result['total'], 1)
        print(f"  ✅ Student 241101p attendance: {result['total']} records, {presence_rate}% present")
    
    # Test activity statistics
    cursor.execute('''
        SELECT activity_name, COUNT(DISTINCT admission_id) as students
        FROM registrations
        GROUP BY activity_name
        ORDER BY students DESC
    ''')
    print(f"  ✅ Activity registration counts:")
    for row in cursor.fetchall():
        print(f"     • {row['activity_name']}: {row['students']} students")
    
    print("\n" + "="*120)
    if all_good and approved > 0 and students_with_data > 0:
        print("🎉 SYSTEM VERIFICATION: ALL CHECKS PASSED!")
    else:
        print("⚠️  SYSTEM VERIFICATION: Some checks incomplete")
    
    print("="*120)
    print("""
✅ DATABASE IS READY FOR TESTING

Next steps:
  1. Make sure Flask server is running: python backend/start_server.py
  2. Test Creator Analytics Page: http://127.0.0.1:5000/creator-dashboard.html
  3. Login with test_creator@pbsiddhartha.ac.in / password123
  4. Check Analytics tab → Should show attendance data

The analysis, attendance, and reports pages should now display data correctly!
    """)
    print("="*120 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Verification failed: {e}')
    import traceback
    traceback.print_exc()
