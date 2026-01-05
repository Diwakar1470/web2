#!/usr/bin/env python
"""
Database Migration Script: Add missing department column to students table
Run this script to fix the schema mismatch
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    """Add missing department column to students table"""
    
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '1234')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'school_db')
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='students' AND column_name='department'
            )
        """)
        
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("⏳ Adding 'department' column to students table...")
            cursor.execute("""
                ALTER TABLE students
                ADD COLUMN department VARCHAR(255)
            """)
            conn.commit()
            print("✅ Successfully added 'department' column to students table!")
        else:
            print("ℹ️  'department' column already exists in students table.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Make sure PostgreSQL is running at {db_host}:{db_port}")
        return False
    
    return True

if __name__ == "__main__":
    migrate_database()
