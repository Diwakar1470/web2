"""
Migration script to add registration_status column to users table
"""

import os
from sqlalchemy import text
from app import app, db

def add_registration_status_column():
    """Add registration_status column to users table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if column exists and add it if not
            with db.engine.connect() as connection:
                # Check if the column exists
                query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='registration_status'
                """
                result = connection.execute(text(query))
                column_exists = result.fetchone() is not None
                
                if not column_exists:
                    print("[MIGRATING] Adding registration_status column to users table...")
                    alter_query = """
                        ALTER TABLE users 
                        ADD COLUMN registration_status VARCHAR(20) DEFAULT 'PENDING'
                    """
                    connection.execute(text(alter_query))
                    connection.commit()
                    print("[OK] Successfully added registration_status column")
                else:
                    print("[INFO] registration_status column already exists")
                    
        except Exception as e:
            print(f"[ERROR] Failed to add registration_status column: {e}")
            raise

if __name__ == '__main__':
    add_registration_status_column()
