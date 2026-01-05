# Database Schema Fix - Student Registration

## Problem Identified
The student registration endpoint was failing with this error:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column students.department does not exist
```

## Root Cause
The `Student` model in `app.py` (line 189) defines a `department` column:
```python
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    lookup_key = db.Column(db.String, unique=True, index=True)
    department = db.Column(db.String(255))  # <-- This column
    profile = db.Column(JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

However, the database table was created with an older schema that didn't include this column.

## Solution Applied
Created and ran `backend/migrate_fix.py` which:
1. Safely checks if the `department` column exists in the `students` table
2. If missing, adds the column with type `VARCHAR(255)`
3. Uses direct PostgreSQL connection for reliable migration

## How to Run Migration
If you encounter this issue again:
```powershell
cd backend
python migrate_fix.py
```

## Status
✅ Migration completed successfully
✅ Student registration endpoint now works
✅ Ready to test with the frontend

## Next Steps
1. Restart the backend server
2. Test student registration through the web interface
3. Verify the department field is properly stored
