"""Verify database schema changes"""
from app import app, db, Registration
from sqlalchemy import inspect

with app.app_context():
    print("\n" + "="*70)
    print("DATABASE SCHEMA VERIFICATION")
    print("="*70 + "\n")
    
    # Inspect Registration table
    inspector = inspect(db.engine)
    columns = inspector.get_columns('registrations')
    
    print("Registration Table Columns:")
    print("-" * 70)
    
    expected_columns = [
        'id', 'student_email', 'admission_id', 'activity_name',
        'status', 'coordinator_status', 'hod_status', 'rejection_reason',
        'data', 'timestamp', 'updated_at'
    ]
    
    found_columns = []
    for col in columns:
        col_name = col['name']
        col_type = str(col['type'])
        nullable = 'NULL' if col['nullable'] else 'NOT NULL'
        found_columns.append(col_name)
        
        status = "✅" if col_name in expected_columns else "⚠️ "
        print(f"{status} {col_name:25s} {col_type:20s} {nullable}")
    
    print("\n" + "-" * 70)
    print("Column Check:")
    print("-" * 70)
    
    for expected in expected_columns:
        if expected in found_columns:
            print(f"✅ {expected}")
        else:
            print(f"❌ MISSING: {expected}")
    
    # Check indexes
    indexes = inspector.get_indexes('registrations')
    print("\n" + "-" * 70)
    print("Indexes:")
    print("-" * 70)
    for idx in indexes:
        print(f"✅ {idx['name']}: {idx['column_names']}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    missing = [col for col in expected_columns if col not in found_columns]
    if missing:
        print(f"❌ Missing columns: {', '.join(missing)}")
        print("\n⚠️  You need to:")
        print("   1. Drop existing registrations table")
        print("   2. Restart backend to recreate with new schema")
        print("   Or run: DROP TABLE registrations; in PostgreSQL")
    else:
        print("✅ All required columns present!")
        print("✅ Database schema is up to date")
    
    print("="*70 + "\n")
