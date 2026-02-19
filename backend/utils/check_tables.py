#!/usr/bin/env python3
"""Check what tables exist in the database"""

import mysql.connector  # type: ignore

try:
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='1234',
        database='school_db'
    )
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'school_db'
        ORDER BY TABLE_NAME
    """)
    
    print("\n📊 EXISTING TABLES IN school_db:\n")
    tables = cursor.fetchall()
    for (table_name,) in tables:
        # Get record count
        try:
            cursor.execute(f'SELECT COUNT(*) as cnt FROM `{table_name}`')
            count = cursor.fetchone()[0]
            print(f"  ✅ {table_name:35} : {count:6} records")
        except:
            print(f"  ⚠️  {table_name:35} : (error counting)")
    
    print(f"\nTotal: {len(tables)} tables\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
