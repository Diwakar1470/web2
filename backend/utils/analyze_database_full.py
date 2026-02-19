#!/usr/bin/env python3
"""
Comprehensive Database Analysis
Shows what's stored in each table and data statistics
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
    
    print("\n" + "="*120)
    print("🗄️  DATABASE STRUCTURE & DATA ANALYSIS")
    print("="*120)
    
    # Get all tables
    cursor.execute("SHOW TABLES")
    tables = [row['Tables_in_school_db'] for row in cursor.fetchall()]
    
    print(f"\n📊 Total Tables: {len(tables)}\n")
    
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) as cnt FROM `{table}`")
        count = cursor.fetchone()['cnt']
        
        # Get column info
        cursor.execute(f"DESCRIBE `{table}`")
        columns = cursor.fetchall()
        col_names = [col['Field'] for col in columns]
        
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📋 {table.upper()}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   Records: {count}")
        print(f"   Columns: {', '.join(col_names)}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM `{table}` LIMIT 3")
            rows = cursor.fetchall()
            print(f"   Sample Data:")
            for i, row in enumerate(rows, 1):
                print(f"     [{i}] {dict(row)}")
        else:
            print(f"   ⚠️  TABLE IS EMPTY - NO DATA")
        print()
    
    # Summary
    print("\n" + "="*120)
    print("📊 DATA SUMMARY")
    print("="*120)
    
    stats = {
        'users': 'SELECT COUNT(*) as cnt FROM users',
        'students': 'SELECT COUNT(*) as cnt FROM students',
        'roles': 'SELECT COUNT(*) as cnt FROM roles',
        'departments': 'SELECT COUNT(*) as cnt FROM departments',
        'activities': 'SELECT COUNT(*) as cnt FROM activities',
        'sub_activities': 'SELECT COUNT(*) as cnt FROM sub_activities',
        'registrations': 'SELECT COUNT(*) as cnt FROM registration',
        'attendance': 'SELECT COUNT(*) as cnt FROM attendance',
        'hods': 'SELECT COUNT(*) as cnt FROM hods',
        'program_department_map': 'SELECT COUNT(*) as cnt FROM program_department_map',
    }
    
    print("\n")
    for table_name, query in stats.items():
        try:
            cursor.execute(query)
            count = cursor.fetchone()['cnt']
            status = "✅" if count > 0 else "⚠️ "
            print(f"  {status} {table_name:30} : {count:6} records")
        except:
            print(f"  ❌ {table_name:30} : TABLE NOT FOUND")
    
    cursor.close()
    conn.close()
    
except Error as e:
    print(f'❌ Database Error: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
