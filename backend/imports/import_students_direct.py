#!/usr/bin/env python3
"""
Directly import student data from CSV to MySQL students table
"""

import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore
import csv
import os

CSV_PATH = r'd:\web1\web1\file\student_info (3).csv'

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='school_db',
        autocommit=True
    )
    cursor = conn.cursor(dictionary=True)
    
    print(f"📖 Reading CSV: {CSV_PATH}")
    
    count_created = 0
    count_updated = 0
    count_skipped = 0
    
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            roll_no = (row.get('rollno') or '').strip().lower()
            
            if not roll_no:
                count_skipped += 1
                continue
            
            # Check if student exists
            cursor.execute('SELECT id FROM students WHERE lookup_key = %s', (roll_no,))
            existing = cursor.fetchone()
            
            profile_data = {
                'studentName': (row.get('sname') or '').strip(),
                'fatherName': (row.get('fname') or '').strip(),
                'motherName': (row.get('mname') or '').strip(),
                'joiningYear': (row.get('jyear') or '').strip(),
                'caste': (row.get('caste') or '').strip(),
                'pcode': (row.get('pcode') or '').strip(),
                'program': (row.get('pshort') or '').strip(),
                'aadharNo': (row.get('aadharno') or '').strip(),
                'dob': (row.get('dob') or '').strip(),
                'gender': (row.get('gender') or '').strip(),
                'currentSem': (row.get('currsem') or '').strip(),
                'mobileNo': (row.get('mobileno') or '').strip(),
                'rollNo': roll_no,
                'section': (row.get('secl') or '').strip()
            }
            
            import json
            profile_json = json.dumps(profile_data)
            
            if existing:
                cursor.execute('''
                    UPDATE students 
                    SET profile = %s, department = %s
                    WHERE lookup_key = %s
                ''', (profile_json, (row.get('pshort') or '').strip(), roll_no))
                count_updated += 1
            else:
                cursor.execute('''
                    INSERT INTO students (lookup_key, department, profile)
                    VALUES (%s, %s, %s)
                ''', (roll_no, (row.get('pshort') or '').strip(), profile_json))
                count_created += 1
            
            if (count_created + count_updated) % 100 == 0:
                print(f"  Progress: {count_created + count_updated} records processed...")
    
    conn.commit()
    
    # Verify import
    cursor.execute('SELECT COUNT(*) as cnt FROM students')
    total = cursor.fetchone()
    print(f'\n✅ Import Complete!')
    print(f'  📝 Created: {count_created}')
    print(f'  🔄 Updated: {count_updated}')
    print(f'  ⏭️  Skipped: {count_skipped}')
    print(f'  📊 Total in DB: {total["cnt"]}')
    
    # Show sample roll numbers
    cursor.execute('SELECT lookup_key FROM students LIMIT 10')
    print(f'\n📋 Sample Roll Numbers:')
    for row in cursor.fetchall():
        print(f'  - {row["lookup_key"]}')
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f'❌ Database Error: {e}')
except FileNotFoundError as e:
    print(f'❌ File Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
