"""
Database Migration Script: Unified User System with RBAC
Creates users, roles, departments tables and migrates existing data
"""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt
from datetime import datetime

load_dotenv()

db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', '1234')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'school_db')

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def migrate_database():
    """Run the migration"""
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
        
        # Step 1: Create roles table
        print("\n📋 Creating roles table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Roles table created")
        
        # Step 2: Create departments table
        print("\n📋 Creating departments table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                code VARCHAR(50),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Departments table created")
        
        # Step 3: Create unified users table
        print("\n📋 Creating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                role_id INTEGER REFERENCES roles(id),
                employee_id VARCHAR(100) UNIQUE,
                
                -- Department/Activity assignment
                assigned_department_id INTEGER REFERENCES departments(id),
                assigned_activity_name VARCHAR(255),
                
                -- Profile information
                phone VARCHAR(50),
                age INTEGER,
                gender VARCHAR(20),
                blood_group VARCHAR(10),
                address TEXT,
                profile_photo VARCHAR(500),
                
                -- Profile completion tracking
                profile_completed BOOLEAN DEFAULT FALSE,
                is_temp_password BOOLEAN DEFAULT TRUE,
                
                -- Metadata
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                
                CONSTRAINT chk_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
            );
        """)
        print("✅ Users table created")
        
        # Step 4: Create indexes for performance
        print("\n📋 Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id);
            CREATE INDEX IF NOT EXISTS idx_users_department ON users(assigned_department_id);
            CREATE INDEX IF NOT EXISTS idx_users_activity ON users(assigned_activity_name);
        """)
        print("✅ Indexes created")
        
        # Step 5: Insert default roles
        print("\n📋 Inserting roles...")
        roles_data = [
            ('CREATOR', 'Super Admin - Can create HODs and Coordinators'),
            ('HOD', 'Head of Department - Manages department students'),
            ('FACULTY_COORDINATOR', 'Activity Coordinator - Manages activities'),
            ('STUDENT', 'Student - Can apply for activities')
        ]
        
        for role_name, description in roles_data:
            cursor.execute("""
                INSERT INTO roles (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (role_name, description))
        print(f"✅ Inserted {len(roles_data)} roles")
        
        # Step 6: Insert default departments
        print("\n📋 Inserting departments...")
        departments_data = [
            ('AI & DS', 'AIDS', 'Artificial Intelligence & Data Science'),
            ('CSE', 'CSE', 'Computer Science Engineering'),
            ('ECE', 'ECE', 'Electronics & Communication Engineering'),
            ('EEE', 'EEE', 'Electrical & Electronics Engineering'),
            ('MECH', 'MECH', 'Mechanical Engineering'),
            ('CIVIL', 'CIVIL', 'Civil Engineering'),
            ('IT', 'IT', 'Information Technology'),
            ('CSE(AI&ML)', 'CSEAIML', 'CSE (AI & ML)'),
        ]
        
        for dept_name, code, description in departments_data:
            cursor.execute("""
                INSERT INTO departments (name, code, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING;
            """, (dept_name, code, description))
        print(f"✅ Inserted {len(departments_data)} departments")
        
        # Step 7: Get role IDs for migration
        cursor.execute("SELECT id FROM roles WHERE name = 'CREATOR'")
        creator_role_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM roles WHERE name = 'HOD'")
        hod_role_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM roles WHERE name = 'FACULTY_COORDINATOR'")
        coordinator_role_id = cursor.fetchone()[0]
        
        # Step 8: Create default creator account
        print("\n📋 Creating creator account...")
        creator_email = 'admin@pbsiddhartha.ac.in'
        creator_password = 'admin123'
        creator_hash = hash_password(creator_password)
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, role_id, employee_id, profile_completed, is_temp_password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                role_id = EXCLUDED.role_id;
        """, (creator_email, creator_hash, 'System Administrator', creator_role_id, 'ADMIN001', True, False))
        print(f"✅ Creator account created: {creator_email} / {creator_password}")
        
        # Step 9: Migrate existing HODs
        print("\n📋 Migrating existing HODs...")
        cursor.execute("SELECT id, name, email, employee_id, department FROM hods")
        hods = cursor.fetchall()
        
        migrated_hods = 0
        for hod_id, name, email, emp_id, department in hods:
            # Get department ID
            cursor.execute("SELECT id FROM departments WHERE name = %s", (department,))
            dept_result = cursor.fetchone()
            dept_id = dept_result[0] if dept_result else None
            
            # Generate temporary password
            temp_password = f"HOD{emp_id}@123"
            password_hash = hash_password(temp_password)
            
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role_id, employee_id, 
                                   assigned_department_id, profile_completed, is_temp_password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    role_id = EXCLUDED.role_id,
                    assigned_department_id = EXCLUDED.assigned_department_id;
            """, (email, password_hash, name, hod_role_id, emp_id, dept_id, False, True))
            migrated_hods += 1
        
        print(f"✅ Migrated {migrated_hods} HODs (temp password format: HOD<emp_id>@123)")
        
        # Step 10: Migrate existing Coordinators
        print("\n📋 Migrating existing Coordinators...")
        cursor.execute("SELECT id, name, email, coordinator_id, role FROM coordinators")
        coordinators = cursor.fetchall()
        
        migrated_coords = 0
        for coord_id, name, email, coord_emp_id, activity_role in coordinators:
            # Generate temporary password
            temp_password = f"COORD{coord_emp_id}@123"
            password_hash = hash_password(temp_password)
            
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role_id, employee_id, 
                                   assigned_activity_name, profile_completed, is_temp_password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    role_id = EXCLUDED.role_id,
                    assigned_activity_name = EXCLUDED.assigned_activity_name;
            """, (email, password_hash, name, coordinator_role_id, coord_emp_id, activity_role, False, True))
            migrated_coords += 1
        
        print(f"✅ Migrated {migrated_coords} Coordinators (temp password format: COORD<id>@123)")
        
        # Step 11: Create activity_users mapping table for many-to-many relationship
        print("\n📋 Creating activity_users mapping table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_users (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                activity_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, activity_name)
            );
        """)
        print("✅ Activity-users mapping table created")
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   • Roles: 4 (CREATOR, HOD, FACULTY_COORDINATOR, STUDENT)")
        print(f"   • Departments: {len(departments_data)}")
        print(f"   • Creator Account: {creator_email} / {creator_password}")
        print(f"   • Migrated HODs: {migrated_hods}")
        print(f"   • Migrated Coordinators: {migrated_coords}")
        print(f"\n🔑 Default Credentials:")
        print(f"   Creator: admin@pbsiddhartha.ac.in / admin123")
        print(f"   HODs: <email> / HOD<employee_id>@123")
        print(f"   Coordinators: <email> / COORD<coordinator_id>@123")
        print(f"\n⚠️  All HODs and Coordinators must complete their profile on first login!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    migrate_database()
