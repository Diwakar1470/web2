"""
⚠️  WARNING: FULL DATABASE RESET ⚠️
This script DROPS and RECREATES the school_db database!
ALL DATA WILL BE LOST!

For normal operation, use: python start_server.py
Only use this script if you want to completely wipe the database.
"""
import mysql.connector
from mysql.connector import Error as MySQLError
import os

# Configuration
DB_USER = 'root'
DB_PASSWORD = '1234'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'school_db'

def main():
    # Safety confirmation
    print("\n" + "!" * 60)
    print("⚠️  WARNING: THIS WILL DELETE ALL DATA IN school_db! ⚠️")
    print("!" * 60)
    confirm = input("\nType 'YES' to confirm full database reset: ")
    if confirm != 'YES':
        print("\n❌ Reset cancelled. Your data is safe.")
        print("   For normal operation, use: python start_server.py")
        return False
    print("")
    print("=" * 60)
    print("FULL DATABASE RESET")
    print("=" * 60)
    
    # Connect to default mysql database to drop/create school_db
    print("\n[1/5] Connecting to MySQL...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
        cur = conn.cursor()
        print("    ✓ Connected successfully!")
    except Exception as e:
        print(f"    ✗ Connection failed: {e}")
        print("\n    Try one of these passwords:")
        print("    - 1234")
        print("    - postgres")
        print("    - admin")
        print("    - (empty)")
        return False

    # Drop existing database (MySQL handles active connections automatically)
    print(f"\n[2/5] Dropping existing '{DB_NAME}' database...")
    try:
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        print(f"    ✓ Database '{DB_NAME}' dropped!")
    except Exception as e:
        print(f"    ⚠ Warning: {e}")

    # Create fresh database
    print(f"\n[3/5] Creating fresh '{DB_NAME}' database...")
    try:
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"    ✓ Database '{DB_NAME}' created!")
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

    cur.close()
    conn.close()

    # Now run the Flask app to create tables
    print("\n[4/5] Creating tables via Flask app...")
    print("    (Tables will be created when app.py runs)")
    
    print("\n[5/5] Setup complete!")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Run: python app.py")
    print("2. This will create all tables and seed default users")
    print("3. Then run: python import_activities_from_csv.py")
    print("4. To import activity data from AH.csv")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    main()
