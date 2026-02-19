import mysql.connector
import csv
import os

conn = mysql.connector.connect(
    database='school_db', 
    user='root', 
    password='1234', 
    host='127.0.0.1', 
    port='3306'
)
cur = conn.cursor()

# Check table structure
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'hods'")
cols = [c[0] for c in cur.fetchall()]
print("HODs table columns:", cols)

# Read HOD details from CSV
csv_path = r'd:\web1\web1\structure\hod_details.csv'
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dept_name = row['Department Name']
        dept_code = row['Department Code']
        hod_name = row['HOD Name']
        phone = row['Phone']
        email = row['Email']
        
        # Check if department exists, if not create it
        cur.execute('SELECT id FROM departments WHERE code = %s OR name = %s', (dept_code, dept_name))
        dept = cur.fetchone()
        if not dept:
            cur.execute('INSERT INTO departments (name, code) VALUES (%s, %s)', (dept_name, dept_code))
            dept_id = cur.lastrowid
            print(f'Created department: {dept_name} ({dept_code})')
        else:
            dept_id = dept[0]
        
        # Check if HOD exists
        cur.execute('SELECT id FROM hods WHERE email = %s', (email,))
        existing = cur.fetchone()
        if not existing:
            # Generate employee_id from email
            employee_id = email.split('@')[0].upper().replace('.', '_')
            # Insert HOD with all columns including phone
            cur.execute('''
                INSERT INTO hods (name, email, department, employee_id, phone) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (hod_name, email, dept_name, employee_id, phone))
            print(f'Added HOD: {hod_name} for {dept_name} (Phone: {phone})')
        else:
            # Update phone if missing
            cur.execute('UPDATE hods SET phone = %s WHERE email = %s AND (phone IS NULL OR phone = \'\')', (phone, email))
            print(f'HOD already exists: {hod_name} - updated phone if missing')

conn.commit()
print('\nDone! HODs imported.')
cur.execute('SELECT COUNT(*) FROM hods')
print(f'Total HODs: {cur.fetchone()[0]}')

# Also add B.Sc.-Honours(AI) mapping to Data Science & AI department
print("\n--- Adding B.Sc.-Honours(AI) program mapping ---")
cur.execute("SELECT id FROM departments WHERE code = 'DSAI'")
dsai = cur.fetchone()
if dsai:
    print(f"B.Sc.-Honours(AI) students will be mapped to Data Science & AI department (ID: {dsai[0]})")

conn.close()
