"""
Seed initial program-to-department mappings into the database
"""
import mysql.connector

conn = mysql.connector.connect(
    database='school_db',
    user='root',
    password='1234',
    host='127.0.0.1',
    port='3306'
)
cur = conn.cursor()

# Create the table if it doesn't exist
cur.execute('''
    CREATE TABLE IF NOT EXISTS program_department_mappings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        program_name VARCHAR(255) UNIQUE NOT NULL,
        department_name VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Initial mappings (previously hardcoded)
mappings = [
    ('B.Sc.-Honours(AI)', 'Data Science & AI'),
    ('B.Sc.(AI)', 'Data Science & AI'),
    ('B.Sc. AI', 'Data Science & AI'),
    ('B.Sc. Data Science', 'Data Science & AI'),
    ('B.Sc.-Honours(Computer Science)', 'Computer Science'),
    ('B.Sc.(Computer Science)', 'Computer Science'),
    ('B.Com.', 'Commerce'),
    ('B.Com', 'Commerce'),
    ('B.A.', 'English'),
    ('B.B.A.', 'Business Administration'),
    ('BBA', 'Business Administration'),
    ('MBA', 'Master of Business Administration'),
    ('M.B.A.', 'Master of Business Administration'),
    ('B.C.A.', 'Computer Science'),
    ('BCA', 'Computer Science'),
]

print("Seeding program-department mappings...")
for program_name, department_name in mappings:
    try:
        cur.execute('''
            INSERT INTO program_department_mappings (program_name, department_name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE department_name = VALUES(department_name)
        ''', (program_name, department_name))
        print(f"  ✓ {program_name} -> {department_name}")
    except Exception as e:
        print(f"  ✗ {program_name}: {e}")

conn.commit()

# Verify
cur.execute('SELECT COUNT(*) FROM program_department_mappings')
count = cur.fetchone()[0]
print(f"\nTotal mappings in database: {count}")

conn.close()
print("Done!")
