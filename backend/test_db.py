import psycopg2
import json
from datetime import datetime

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    database='school_db',
    user='postgres',
    password='1234',
    port=5432
)

cur = conn.cursor()

# Check registrations
print("=" * 50)
print("REGISTRATIONS TABLE")
print("=" * 50)
cur.execute('SELECT id, data, timestamp FROM registrations;')
rows = cur.fetchall()
print(f"Total registrations: {len(rows)}\n")
for row in rows:
    print(f"ID: {row[0]}")
    print(f"Data: {json.dumps(row[1], indent=2)}")
    print(f"Timestamp: {row[2]}")
    print("-" * 50)

# Check students
print("\n" + "=" * 50)
print("STUDENTS TABLE")
print("=" * 50)
cur.execute('SELECT id, lookup_key, profile FROM students;')
rows = cur.fetchall()
print(f"Total students: {len(rows)}\n")
for row in rows:
    print(f"ID: {row[0]}")
    print(f"Lookup Key: {row[1]}")
    print(f"Profile: {json.dumps(row[2], indent=2)}")
    print("-" * 50)

# Check HODs
print("\n" + "=" * 50)
print("HODS TABLE")
print("=" * 50)
cur.execute('SELECT id, name, email, employee_id, department FROM hods;')
rows = cur.fetchall()
print(f"Total HODs: {len(rows)}\n")
for row in rows:
    print(f"ID: {row[0]}")
    print(f"Name: {row[1]}")
    print(f"Email: {row[2]}")
    print(f"Employee ID: {row[3]}")
    print(f"Department: {row[4]}")
    print("-" * 50)

cur.close()
conn.close()
print("\n✅ Database check complete!")
