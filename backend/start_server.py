"""
SAFE DATABASE STARTUP
This script:
1. Checks if school_db exists - if not, creates it
2. Does NOT drop existing database
3. Starts the Flask server

Use this instead of full_reset.py for normal operation
"""
import mysql.connector
from mysql.connector import Error as MySQLError
import subprocess
import sys
import os

# Configuration
DB_USER = 'root'
DB_PASSWORD = '1234'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'school_db'

def check_and_create_database():
    """Check if database exists, create only if it doesn't"""
    print("=" * 60)
    print("SAFE DATABASE STARTUP")
    print("=" * 60)
    
    try:
        # First try to connect directly to school_db
        print(f"\n[1/2] Checking if '{DB_NAME}' database exists...")
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=int(DB_PORT),
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            conn.close()
            print(f"    ✓ Database '{DB_NAME}' exists! Using existing database.")
            return True
        except MySQLError as e:
            if "does not exist" in str(e):
                print(f"    ⚠ Database '{DB_NAME}' does not exist. Creating...")
            else:
                raise e
        
        # Database doesn't exist, create it
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            autocommit=True
        )
        cur = conn.cursor()
        
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"    ✓ Database '{DB_NAME}' created!")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def start_flask_app():
    """Start the Flask application"""
    print(f"\n[2/2] Starting Flask server...")
    print("=" * 60)
    
    # Run app.py
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, 'app.py'])

if __name__ == '__main__':
    if check_and_create_database():
        start_flask_app()
    else:
        print("\n❌ Failed to initialize database. Check your MySQL connection.")
        print("\nTroubleshooting:")
        print(f"  - Verify MySQL is running on {DB_HOST}:{DB_PORT}")
        print(f"  - Check password for user '{DB_USER}'")
        print(f"  - Current password: '{DB_PASSWORD}'")
