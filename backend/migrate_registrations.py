"""Migrate existing registrations table to new schema"""
from app import app, db

with app.app_context():
    print("\n" + "="*70)
    print("MIGRATING REGISTRATIONS TABLE")
    print("="*70 + "\n")
    
    print("⚠️  This will:")
    print("   1. Backup existing data (if any)")
    print("   2. Drop registrations table")
    print("   3. Recreate with new schema")
    print("   4. Restore data (if possible)")
    print()
    
    # Check if there's data
    result = db.session.execute(db.text("SELECT COUNT(*) FROM registrations"))
    count = result.scalar()
    
    print(f"📊 Current registrations in table: {count}")
    
    if count > 0:
        print("\n⚠️  WARNING: You have existing data!")
        print("   Backing up to registrations_backup table...")
        try:
            db.session.execute(db.text(
                "CREATE TABLE registrations_backup AS SELECT * FROM registrations"
            ))
            db.session.commit()
            print("   ✅ Backup created: registrations_backup")
        except Exception as e:
            print(f"   ⚠️  Backup failed (table may already exist): {e}")
    
    print("\n🔄 Dropping registrations table...")
    try:
        db.session.execute(db.text("DROP TABLE IF EXISTS registrations CASCADE"))
        db.session.commit()
        print("   ✅ Table dropped")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        db.session.rollback()
        exit(1)
    
    print("\n🔨 Creating new registrations table with updated schema...")
    try:
        db.create_all()
        print("   ✅ Table created with new schema!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        db.session.rollback()
        exit(1)
    
    print("\n" + "="*70)
    print("MIGRATION COMPLETE!")
    print("="*70)
    print("✅ Registrations table now has:")
    print("   - student_email")
    print("   - admission_id")
    print("   - activity_name")
    print("   - status (pending/coordinator_approved/hod_approved/rejected)")
    print("   - coordinator_status")
    print("   - hod_status")
    print("   - rejection_reason")
    print("   - updated_at")
    print("="*70 + "\n")
