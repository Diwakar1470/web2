#!/usr/bin/env python3
"""
FINAL SEED DATA SCRIPT - Using correct table structure
"""

import mysql.connector  # type: ignore
from datetime import datetime, timedelta
import random

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='school_db'
    )
    cursor = conn.cursor(dictionary=True)
    
    print("\n" + "="*120)
    print("🌱 SEEDING DATABASE - FINAL VERSION")
    print("="*120 + "\n")
    
    # Activities already created
    print("STEP 1: Checking Activities...")
    cursor.execute('SELECT COUNT(*) as cnt FROM activities')
    act_count = cursor.fetchone()['cnt']
    print(f"✅ Found {act_count} activities\n")
    
    # ========== STEP 2: SEED REGISTRATIONS ==========
    print("STEP 2: Creating Student Registrations...")
    print("-" * 120)
    
    # Get all students
    cursor.execute('''
        SELECT id, lookup_key, department 
        FROM students 
        WHERE lookup_key IS NOT NULL AND lookup_key != '' 
        LIMIT 300
    ''')
    students = cursor.fetchall()
    
    # Get activities
    cursor.execute('SELECT name FROM activities')
    activities = [row['name'] for row in cursor.fetchall()]
    
    registrations_created = 0
    
    if students and activities:
        print(f"Found {len(students)} students and {len(activities)} activities\n")
        
        for i, student in enumerate(students[:150]):  # Register first 150 students
            student_id = student['id']
            admission_id = student['lookup_key']
            department = student['department'] or 'General'
            
            # Each student registers for 2-4 activities
            num_activities = random.randint(2, 4)
            selected_activities = random.sample(activities, min(num_activities, len(activities)))
            
            for activity_name in selected_activities:
                try:
                    cursor.execute('''
                        INSERT INTO registrations 
                        (student_email, admission_id, student_name, department, activity_name, status, 
                         coordinator_status, hod_status, timestamp, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ''', (
                        f'student-{admission_id}@pbsiddhartha.ac.in',
                        admission_id,
                        f'Student {admission_id}',
                        department,
                        activity_name,
                        'hod_approved',
                        'approved',
                        'approved'
                    ))
                    registrations_created += 1
                except Exception as e:
                    if 'Duplicate' not in str(e):
                        print(f"  Error: {e}")
            
            if (i + 1) % 30 == 0:
                print(f"  Processed {i+1}/{len(students[:150])} students...")
                conn.commit()
        
        conn.commit()
        print(f"\n✅ Student registrations created: {registrations_created}\n")
    else:
        print(f"⚠️  Students found: {len(students)}, Activities found: {len(activities)}\n")
    
    # ========== STEP 3: SEED ATTENDANCE ==========
    print("STEP 3: Creating Attendance Records...")
    print("-" * 120)
    
    # Get all registrations
    cursor.execute('''
        SELECT id, admission_id, activity_name 
        FROM registrations 
    ''')
    registrations = cursor.fetchall()
    
    attendance_created = 0
    base_date = datetime.now() - timedelta(days=60)
    coordinator_emails = [
        'coord-ncc@pbsiddhartha.ac.in',
        'coord-sports@pbsiddhartha.ac.in',
        'coord-gym@pbsiddhartha.ac.in',
        'ruhi@pbsiddhartha.ac.in',
        'master@pbsiddhartha.ac.in'
    ]
    
    if registrations:
        print(f"Found {len(registrations)} registrations\n")
        
        for reg_idx, registration in enumerate(registrations):
            registration_id = registration['id']
            admission_id = registration['admission_id']
            activity_name = registration['activity_name']
            
            # Create attendance for 15-20 random past dates (80% present, 20% absent)
            num_days = random.randint(15, 20)
            created_for_reg = 0
            
            # Generate random days from the past 60 days
            random_days = random.sample(range(5, 60), num_days)
            
            for days_ago in random_days:
                attendance_date = base_date + timedelta(days=days_ago)
                status = random.choices(['present', 'absent'], weights=[80, 20])[0]
                
                try:
                    cursor.execute('''
                        INSERT INTO attendance 
                        (student_admission_id, student_name, activity_name, 
                         attendance_date, attendance_type, status, coordinator_email, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ''', (
                        admission_id,
                        f'Student {admission_id}',
                        activity_name,
                        attendance_date.date(),
                        'daily',
                        status,
                        random.choice(coordinator_emails)
                    ))
                    attendance_created += 1
                    created_for_reg += 1
                except Exception as e:
                    pass  # Silently skip errors
            
            if (reg_idx + 1) % 50 == 0:
                print(f"  Processed {reg_idx+1}/{len(registrations)} registrations...")
                conn.commit()
        
        conn.commit()
        print(f"\n✅ Attendance records created: {attendance_created}\n")
    else:
        print("⚠️  No registrations found\n")
    
    # ========== VERIFY DATA ==========
    cursor = conn.cursor(dictionary=True)
    print("\n" + "="*120)
    print("✅ FINAL VERIFICATION")
    print("="*120 + "\n")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM activities')
    print(f"  Activities:            {cursor.fetchone()['cnt']:>6} records ✅")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM sub_activities')
    print(f"  Sub-activities:        {cursor.fetchone()['cnt']:>6} records ✅")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM registrations')
    reg_count = cursor.fetchone()['cnt']
    print(f"  Registrations:         {reg_count:>6} records ✅")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM attendance')
    att_count = cursor.fetchone()['cnt']
    print(f"  Attendance:            {att_count:>6} records ✅")
    
    # Sample data verification
    print("\n" + "-"*120)
    print("SAMPLE DATA:")
    print("-"*120)
    
    cursor.execute('SELECT name FROM activities LIMIT 6')
    print("\nActivities:")
    for row in cursor.fetchall():
        print(f"  • {row['name']}")
    
    cursor.execute('SELECT activity_name, sub_activity_name FROM sub_activities ORDER BY activity_name LIMIT 10')
    print("\nSub-Activities (sample):")
    for row in cursor.fetchall():
        print(f"  • {row['activity_name']} → {row['sub_activity_name']}")
    
    cursor.execute('SELECT DISTINCT admission_id, activity_name FROM registrations LIMIT 5')
    print("\nRegistrations (sample):")
    for row in cursor.fetchall():
        print(f"  • {row['admission_id']} → {row['activity_name']}")
    
    cursor.execute('''
        SELECT student_admission_id, activity_name, DATE(attendance_date), status 
        FROM attendance 
        ORDER BY attendance_date DESC 
        LIMIT 5
    ''')
    print("\nAttendance (sample):")
    for row in cursor.fetchall():
        print(f"  • {row['student_admission_id']} in {row['activity_name']} on {row['DATE(attendance_date)']}: {row['status']}")
    
    # Summary stats
    print("\n" + "="*120)
    print("📊 DATABASE SUMMARY")
    print("="*120)
    
    if reg_count > 0:
        cursor.execute('SELECT COUNT(DISTINCT admission_id) as unique_students FROM registrations')
        unique_students = cursor.fetchone()['unique_students']
        avg_regs_per_student = round(reg_count / unique_students, 2) if unique_students > 0 else 0
        print(f"\n✅ {unique_students} unique students with activity registrations")
        print(f"✅ Average {avg_regs_per_student} activities per student")
    
    if att_count > 0:
        cursor.execute('SELECT COUNT(DISTINCT student_admission_id) as unique_students FROM attendance')
        att_students = cursor.fetchone()['unique_students']
        cursor.execute('''
            SELECT ROUND(100.0 * SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) / COUNT(*), 1) as present_percentage
            FROM attendance
        ''')
        present_pct = cursor.fetchone()['present_percentage']
        print(f"✅ {att_students} students have attendance records")
        print(f"✅ Overall presence rate: {present_pct}%")
    
    print("\n" + "="*120)
    print("🎉 DATABASE SEEDING COMPLETE!")
    print("="*120)
    
    if reg_count > 100 and att_count > 500:
        print(f"""
✅ SUCCESS! Database populated with sufficient data:
   • {reg_count} registrations
   • {att_count} attendance records

NOW TEST THE SYSTEM:

1. CREATOR ANALYTICS PAGE:
   • URL: http://127.0.0.1:5000/creator-dashboard.html
   • Go to: http://localhost:5000/pages/creator/creator-dashboard.html
   • Check Analytics tab → Should show attendance statistics

2. COORDINATOR ATTENDANCE:
   • Login as: ruhi@pbsiddhartha.ac.in / password
   • Check Attendance page → Should show attendance records for activities

3. STUDENT VIEW:
   • Login as: 241101P / password123 (or any roll number starting with 241)
   • Check Dashboard → Should show registrations and attendance

The analysis, attendance, and reports pages should now display data!
        """)
    else:
        print(f"""
⚠️  Database populated but with limited data:
   • {reg_count} registrations (need minimum 100)
   • {att_count} attendance records (need minimum 500)

This is enough to test basic functionality, but limited for full testing.
        """)
    
    print("="*120 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
