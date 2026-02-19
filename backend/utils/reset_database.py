"""
Database reset script - clears all data and recreates from scratch
"""

import os
from sqlalchemy import text
from app import app, db

def reset_database():
    """Reset database by dropping all tables and recreating them"""
    with app.app_context():
        try:
            print("[RESET] Starting database reset...")
            
            # Drop all tables
            print("[STEP 1] Dropping all existing tables...")
            with db.engine.connect() as connection:
                # Get all table names from MySQL information_schema
                inspector_query = """
                    SELECT TABLE_NAME FROM information_schema.tables 
                    WHERE TABLE_SCHEMA = DATABASE()
                """
                result = connection.execute(text(inspector_query))
                tables = [row[0] for row in result]
                
                # Disable foreign key checks for MySQL
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                
                # Drop all tables
                for table in tables:
                    try:
                        connection.execute(text(f"DROP TABLE IF EXISTS {table}"))
                        print(f"  ✓ Dropped table: {table}")
                    except Exception as e:
                        print(f"  ⚠ Failed to drop {table}: {e}")
                
                # Re-enable foreign key checks
                connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                connection.commit()
            print("[OK] All tables dropped")
            
            # Create all tables
            print("\n[STEP 2] Creating all database tables...")
            db.create_all()
            print("[OK] All tables created successfully")
            
            print("\n[SUCCESS] Database reset complete!")
            print("\nNow run: python backend/init_database.py")
            
        except Exception as e:
            print(f"\n[ERROR] Database reset failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    reset_database()
