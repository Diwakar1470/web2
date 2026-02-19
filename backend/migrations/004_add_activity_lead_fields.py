#!/usr/bin/env python3
"""
Migration Script: Add activity lead fields to sub_activities table
Adds columns for storing sub-activity lead and activity head information
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error as MySQLError

load_dotenv()

# Database configuration
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '1234')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = int(os.getenv('DB_PORT', '3306'))
db_name = os.getenv('DB_NAME', 'school_db')

def run_migration():
    """Run the migration"""
    try:
        print(f"🔄 Connecting to database: {db_name} on {db_host}:{db_port}")
        conn = mysql.connector.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name,
            autocommit=True
        )
        cursor = conn.cursor()
        
        print("📝 Running migration: Adding activity lead fields to sub_activities...")
        
        # Check if columns exist before attempting to add them (MySQL-compatible)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'sub_activities' 
            AND COLUMN_NAME = 'sub_activity_lead_name'
        """)
        
        column_exists = cursor.fetchone()[0] > 0
        
        if not column_exists:
            print("  Adding activity lead columns...")
            migration_sql = """
            ALTER TABLE sub_activities
            ADD COLUMN sub_activity_lead_name VARCHAR(255),
            ADD COLUMN sub_activity_lead_phone VARCHAR(20),
            ADD COLUMN activity_head_name VARCHAR(255),
            ADD COLUMN activity_head_phone VARCHAR(20);
            """
            cursor.execute(migration_sql)
        else:
            print("  ✓ Columns already exist, skipping...")
        
        # Create migration log table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Log the migration using ON DUPLICATE KEY UPDATE
        log_sql = """
        INSERT INTO migration_log (migration_name, executed_at) 
        VALUES ('004_add_activity_lead_fields', NOW())
        ON DUPLICATE KEY UPDATE executed_at=NOW();
        """
        
        cursor.execute(log_sql)
        
        print("✅ Migration completed successfully!")
        print("   - Added: sub_activity_lead_name (VARCHAR 255)")
        print("   - Added: sub_activity_lead_phone (VARCHAR 20)")
        print("   - Added: activity_head_name (VARCHAR 255)")
        print("   - Added: activity_head_phone (VARCHAR 20)")
        
        # Verify the columns were added
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='sub_activities' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Current columns in sub_activities table:")
        for col in columns:
            print(f"   - {col[0]}")
        
        cursor.close()
        conn.close()
        
    except MySQLError as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
