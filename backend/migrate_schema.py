"""
Database Schema Migration Script
Adds new columns to existing tables for enhanced functionality
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
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
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔄 Starting database migration...")
        
        # Add columns to students table
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS department VARCHAR(255);")
            print("✅ Added 'department' column to students table")
        except Exception as e:
            print(f"⚠️  students.department: {e}")
        
        # Add columns to registrations table
        try:
            cursor.execute("ALTER TABLE registrations ADD COLUMN IF NOT EXISTS student_name VARCHAR(255);")
            print("✅ Added 'student_name' column to registrations table")
        except Exception as e:
            print(f"⚠️  registrations.student_name: {e}")
        
        try:
            cursor.execute("ALTER TABLE registrations ADD COLUMN IF NOT EXISTS department VARCHAR(255);")
            print("✅ Added 'department' column to registrations table")
        except Exception as e:
            print(f"⚠️  registrations.department: {e}")
        
        try:
            cursor.execute("ALTER TABLE registrations ADD COLUMN IF NOT EXISTS sub_activity_id INTEGER REFERENCES sub_activities(id);")
            print("✅ Added 'sub_activity_id' column to registrations table")
        except Exception as e:
            print(f"⚠️  registrations.sub_activity_id: {e}")
        
        # Add columns to sub_activities table
        try:
            cursor.execute("ALTER TABLE sub_activities ADD COLUMN IF NOT EXISTS total_slots INTEGER DEFAULT 0;")
            print("✅ Added 'total_slots' column to sub_activities table")
        except Exception as e:
            print(f"⚠️  sub_activities.total_slots: {e}")
        
        try:
            cursor.execute("ALTER TABLE sub_activities ADD COLUMN IF NOT EXISTS filled_slots INTEGER DEFAULT 0;")
            print("✅ Added 'filled_slots' column to sub_activities table")
        except Exception as e:
            print(f"⚠️  sub_activities.filled_slots: {e}")
        
        try:
            cursor.execute("ALTER TABLE sub_activities ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")
            print("✅ Added 'is_active' column to sub_activities table")
        except Exception as e:
            print(f"⚠️  sub_activities.is_active: {e}")
        
        # Add columns to course_registrations table
        try:
            cursor.execute("ALTER TABLE course_registrations ADD COLUMN IF NOT EXISTS department VARCHAR(255);")
            print("✅ Added 'department' column to course_registrations table")
        except Exception as e:
            print(f"⚠️  course_registrations.department: {e}")
        
        try:
            cursor.execute("ALTER TABLE course_registrations ADD COLUMN IF NOT EXISTS sub_activity_id INTEGER REFERENCES sub_activities(id);")
            print("✅ Added 'sub_activity_id' column to course_registrations table")
        except Exception as e:
            print(f"⚠️  course_registrations.sub_activity_id: {e}")
        
        # Create events table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_name VARCHAR(255) NOT NULL,
                    activity_name VARCHAR(255) NOT NULL,
                    sub_activity_id INTEGER REFERENCES sub_activities(id),
                    coordinator_email VARCHAR(255),
                    event_date TIMESTAMP NOT NULL,
                    event_time VARCHAR(50),
                    location VARCHAR(255),
                    description TEXT,
                    assigned_students JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Created 'events' table")
        except Exception as e:
            print(f"⚠️  events table: {e}")
        
        # Create attendance table
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    student_admission_id VARCHAR(255) NOT NULL,
                    student_name VARCHAR(255),
                    activity_name VARCHAR(255) NOT NULL,
                    sub_activity_id INTEGER REFERENCES sub_activities(id),
                    event_id INTEGER REFERENCES events(id),
                    attendance_date DATE NOT NULL,
                    attendance_type VARCHAR(50) DEFAULT 'daily',
                    status VARCHAR(20) DEFAULT 'present',
                    coordinator_email VARCHAR(255),
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Created 'attendance' table")
        except Exception as e:
            print(f"⚠️  attendance table: {e}")
        
        # Create indexes for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_admission_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_activity ON attendance(activity_name);")
            print("✅ Created indexes on attendance table")
        except Exception as e:
            print(f"⚠️  attendance indexes: {e}")
        
        print("\n✅ Database migration completed successfully!")
        print("\n📊 Summary:")
        print("   - Updated students table")
        print("   - Updated registrations table")
        print("   - Updated sub_activities table")
        print("   - Updated course_registrations table")
        print("   - Created events table")
        print("   - Created attendance table")
        print("   - Created indexes")
        
    except Exception as e:
        print(f"❌ Migration Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_database()
