#!/usr/bin/env python3
"""
CORRECTED SEED DATA SCRIPT
Uses actual database column names from app.py models
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
    cursor = conn.cursor()
    
    print("\n" + "="*120)
    print("🌱 SEEDING DATABASE WITH SAMPLE DATA (CORRECTED)")
    print("="*120 + "\n")
    
    # ========== STEP 1: SEED ACTIVITIES ==========
    print("STEP 1: Creating Activities...")
    print("-" * 120)
    
    activities_data = [
        'NCC',
        'NSS', 
        'Sports',
        'Gym',
        'Yoga',
        'Culturals',
    ]
    
    activity_ids = {}
    for name in activities_data:
        try:
            cursor.execute('''
                INSERT INTO activities (name, created_at, updated_at)
                VALUES (%s, NOW(), NOW())
            ''', (name,))
            activity_ids[name] = cursor.lastrowid
            print(f"  ✓ Created: {name}")
        except Exception as e:
            if 'Duplicate entry' in str(e):
                print(f"  • Already exists: {name}")
            else:
                print(f"  ✗ Error: {e}")
    
    conn.commit()
    print(f"✅ Activities created: {len(activity_ids)}\n")
    
    # ========== STEP 2: SEED SUB-ACTIVITIES ==========
    print("STEP 2: Creating Sub-Activities...")
    print("-" * 120)
    
    sub_activities_data = {
        'Sports': [
            'Cricket',
            'Football',
            'Basketball',
            'Volleyball',
            'Badminton',
        ],
        'Gym': [
            'Weight Training',
            'Cardio',
            'Aerobics',
        ],
        'Culturals': [
            'Music',
            'Dance',
            'Drama',
            'Art & Craft',
        ],
        'NCC': [
            'Drill Training',
            'Leadership',
        ],
        'NSS': [
            'Community Service',
            'Environment',
        ],
        'Yoga': [
            'Fitness Yoga',
            'Meditation',
        ],
    }
    
    sub_activity_count = 0
    for activity_name, subs in sub_activities_data.items():
        for sub_name in subs:
            try:
                cursor.execute('''
                    INSERT INTO sub_activities 
                    (activity_name, sub_activity_name, coordinator_email, total_slots, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                ''', (activity_name, sub_name, f'coord-{activity_name.lower()}@pbsiddhartha.ac.in', 50))
                sub_activity_count += 1
                print(f"  ✓ {activity_name} → {sub_name}")
            except Exception as e:
                if 'Duplicate' not in str(e):
                    print(f"  ✗ Error: {e}")
    
    conn.commit()
    print(f"✅ Sub-activities created: {sub_activity_count}\n")
    
    # ========== STEP 3: SEED REGISTRATIONS ==========
    print("STEP 3: Creating Student Registrations...")
    print("-" * 120)
    
    # Get all students
    cursor.execute('''
        SELECT id, lookup_key, profile 
        FROM students 
        WHERE lookup_key IS NOT NULL AND lookup_key != '' 
        LIMIT 300
    ''')
    students = cursor.fetchall()
    
    activities_list = list(activities_data)
    registrations_created = 0
    
    if students:
        for student_id, admission_id, profile_json in students[:200]:  # Register first 200 students
            # Each student registers for 2-4 activities
            num_activities = random.randint(2, 4)
            selected_activities = random.sample(activities_list, min(num_activities, len(activities_list)))
            
            for activity_name in selected_activities:
                try:
                    cursor.execute('''
                        INSERT INTO registrations 
                        (student_email, admission_id, student_name, activity_name, status, 
                         coordinator_status, hod_status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ''', (
                        f'student-{admission_id}@gmail.com',
                        admission_id,
                        f'Student {admission_id}',
                        activity_name,
                        'hod_approved',
                        'approved',
                        'approved'
                    ))
                    registrations_created += 1
                except Exception as e:
                    pass  # Silently skip duplicates
        
        conn.commit()
        print(f"✅ Student registrations created: {registrations_created}\n")
    else:
        print("⚠️  No students found\n")
    
    # ========== STEP 4: SEED ATTENDANCE ==========
    print("STEP 4: Creating Attendance Records...")
    print("-" * 120)
    
    # Get all registrations
    cursor.execute('''
        SELECT id, admission_id, activity_name 
        FROM registrations 
        LIMIT 500
    ''')
    registrations = cursor.fetchall()
    
    attendance_created = 0
    base_date = datetime.now() - timedelta(days=60)
    coordinator_emails = [
        'coord-ncc@pbsiddhartha.ac.in',
        'coord-sports@pbsiddhartha.ac.in',
        'coord-gym@pbsiddhartha.ac.in',
        'ruhi@pbsiddhartha.ac.in',
    ]
    
    if registrations:
        for registration_id, admission_id, activity_name in registrations:
            # Create attendance for 15-20 past dates (80% present, 20% absent)
            num_days = random.randint(15, 20)
            
            for i in range(num_days):
                days_ago = random.randint(5, 55)
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
                except Exception as e:
                    pass  # Silently skip errors
        
        conn.commit()
        print(f"✅ Attendance records created: {attendance_created}\n")
    else:
        print("⚠️  No registrations found\n")
    
    # ========== VERIFY DATA ==========
    print("\n" + "="*120)
    print("✅ VERIFICATION OF SEEDED DATA")
    print("="*120 + "\n")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM activities')
    act_count = cursor.fetchone()[0]
    print(f"  Activities:  {act_count} records ✅")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM sub_activities')
    sub_count = cursor.fetchone()[0]
    print(f"  Sub-activities: {sub_count} records ✅")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM registrations')
    reg_count = cursor.fetchone()[0]
    print(f"  Registrations: {reg_count} records ✅")
    
    cursor.execute('SELECT COUNT(*) as cnt FROM attendance')
    att_count = cursor.fetchone()[0]
    print(f"  Attendance: {att_count} records ✅")
    
    # Sample data verification
    print("\n" + "-"*120)
    print("SAMPLE DATA:")
    print("-"*120)
    
    cursor.execute('SELECT name FROM activities LIMIT 3')
    print("\nSample Activities:")
    for (name,) in cursor.fetchall():
        print(f"  • {name}")
    
    cursor.execute('SELECT activity_name, sub_activity_name FROM sub_activities LIMIT 5')
    print("\nSample Sub-Activities:")
    for activity_name, sub_name in cursor.fetchall():
        print(f"  • {activity_name} → {sub_name}")
    
    cursor.execute('''
        SELECT admission_id, activity_name, status FROM registrations 
        GROUP BY admission_id, activity_name 
        LIMIT 5
    ''')
    print("\nSample Registrations:")
    for admission_id, activity_name, status in cursor.fetchall():
        print(f"  • {admission_id} → {activity_name} ({status})")
    
    cursor.execute('''
        SELECT student_admission_id, activity_name, DATE(attendance_date),  status FROM attendance 
        LIMIT 5
    ''')
    print("\nSample Attendance:")
    for adm_id, activity, date, status in cursor.fetchall():
        print(f"  • {adm_id} in {activity} on {date}: {status}")
    
    print("\n" + "="*120)
    print("🎉 DATABASE SEEDING COMPLETE!")
    print("="*120)
    print(f"""
✅ {act_count} Activities
✅ {sub_count} Sub-Activities  
✅ {reg_count} Student Registrations
✅ {att_count} Attendance Records

NOW TEST THE SYSTEM:
  1. Go to http://127.0.0.1:5000/creator-dashboard.html
  2. Go to: http://localhost:5000/pages/creator/creator-dashboard.html
  3. Check Analytics tab → Should show attendance data
  
  4. Or login as COORDINATOR: ruhi@pbsiddhartha.ac.in / password
  5. Check coordinator panel → Attendance records visible
  
  6. Or login as STUDENT: 241101P / password123
  7. Check student dashboard → Your activity registrations visible

The analysis, attendance, and reports pages should now work!
    """)
    print("="*120 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
