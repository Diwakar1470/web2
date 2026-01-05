#!/usr/bin/env python
"""Test backend startup without running the server"""
import sys
sys.path.insert(0, '.')

from app import app, db

with app.app_context():
    try:
        # Test database connection
        db.create_all()
        print("✅ Successfully connected to the database and created tables.")
        
        # Test roles
        from app import Role
        roles = Role.query.all()
        print(f"\n✅ Database roles ({len(roles)}):")
        for role in roles:
            print(f"   - {role.name}")
        
        # Test users
        from app import User
        users = User.query.all()
        print(f"\n✅ Database users ({len(users)}):")
        for user in users:
            role = Role.query.get(user.role_id)
            print(f"   - {user.full_name} ({user.email}) - Role: {role.name if role else 'Unknown'}")
        
        print("\n✅ All database objects initialized successfully!")
        print("\n📋 Test Credentials Available:")
        print("=" * 60)
        print("Email: 237706p@pbsiddhartha.ac.in")
        print("Admission ID: 22B91A05L6")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
