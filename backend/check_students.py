"""Check student records in the database"""
from app import app, db, Student

with app.app_context():
    print(f"\n{'='*60}")
    print(f"STUDENT DATABASE CHECK")
    print(f"{'='*60}\n")
    
    # Count students
    total = Student.query.count()
    print(f"📊 Total students in database: {total}\n")
    
    # Show first 5 students
    if total > 0:
        print(f"First {min(5, total)} students:")
        print(f"{'-'*60}")
        students = Student.query.limit(5).all()
        for i, s in enumerate(students, 1):
            print(f"\n{i}. Student ID: {s.id}")
            print(f"   Lookup Key: {s.lookup_key}")
            print(f"   Profile Data: {s.profile}")
            print(f"   Created: {s.created_at}")
    else:
        print("⚠️  No students found in database!")
        print("\n💡 Students need to be created through:")
        print("   1. Registration form (but endpoint is missing)")
        print("   2. Import endpoint: POST /api/student-profiles/import")
        print("   3. Sample data script: python create_sample_data.py")
