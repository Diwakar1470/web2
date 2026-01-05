# Quick Reference: Department Setup and Management

## Running the Department Setup Script

### Basic Setup (Recommended for first-time installations)
```bash
cd backend
python setup_departments.py
```

This will:
1. ✅ Remove deprecated CSE and ECE departments (if they exist)
2. ✅ Create AI and Data Science (AIDT) department
3. ✅ Ensure all academic departments exist (BA, BCom, BBA, BCA, BSc)
4. ✅ Verify all departments are properly configured

### Expected Output
```
================================================================================
DEPARTMENT SETUP AND CLEANUP UTILITY
================================================================================

================================================================================
REMOVING DEPRECATED DEPARTMENTS (CSE, ECE)
================================================================================
  [NOT FOUND] Department with code: CSE
  [NOT FOUND] Department with code: ECE

[OK] No deprecated departments found
================================================================================

================================================================================
ENSURING AI AND DATA SCIENCE DEPARTMENT EXISTS
================================================================================
  [CREATED] AI and Data Science (AIDT)
  [OK] Department created with ID: 1
================================================================================

================================================================================
ENSURING ACADEMIC DEPARTMENTS EXIST
================================================================================
  [CREATED] Bachelor of Arts (BA)
  [CREATED] Bachelor of Commerce (BCom)
  [CREATED] Bachelor of Business Administration (BBA)
  [CREATED] Bachelor of Computer Applications (BCA)
  [CREATED] Bachelor of Science (BSc)

[OK] 5 new academic departments created
================================================================================

================================================================================
DEPARTMENT VERIFICATION
================================================================================

Total Departments: 6

Academic Departments:
  ✓ Bachelor of Arts (BA)
  ✓ Bachelor of Business Administration (BBA)
  ✓ Bachelor of Commerce (BCom)
  ✓ Bachelor of Computer Applications (BCA)
  ✓ Bachelor of Science (BSc)

Engineering Departments:
  ✓ AI and Data Science (AIDT)

✅ All departments configured correctly!
================================================================================

[SUCCESS] Department setup completed successfully!
```

## Using the Setup Functions Programmatically

### In Python Code
```python
from setup_departments import (
    remove_deprecated_departments,
    create_ai_department,
    create_academic_departments,
    verify_departments,
    main
)

# Run all setup steps
if main():
    print("Setup successful!")
else:
    print("Setup failed - check errors above")
```

### Individual Operations
```python
from setup_departments import verify_departments

# Just verify current state
if verify_departments():
    print("All departments are properly configured")
```

## Checking Department Status from Database

### Using Flask Shell
```bash
cd backend
python -c "from app import app, db, Department; ctx = app.app_context(); ctx.push(); depts = Department.query.all(); [print(f'{d.id}: {d.name} ({d.code})') for d in sorted(depts, key=lambda x: x.id)]"
```

### Using Database Query Tool
```bash
# Connect to your PostgreSQL database
psql -U postgres -h localhost -d school_db

# Run query
SELECT id, name, code, description FROM departments ORDER BY id;
```

## Troubleshooting

### Problem: "Department not found" when accessing admin dashboard
**Solution:**
1. Run: `python backend/setup_departments.py`
2. Ensure PostgreSQL is running
3. Check API endpoint: `http://localhost:5000/api/departments`

### Problem: CSE or ECE still appearing in dropdown
**Solution:**
1. Check if they exist in database:
   ```bash
   python -c "from app import app, Department; ctx = app.app_context(); ctx.push(); print([d.code for d in Department.query.all()])"
   ```
2. If CSE/ECE exist, run: `python backend/setup_departments.py`
3. Refresh browser (hard refresh: Ctrl+Shift+R)
4. Clear localStorage: Open DevTools → Application → Clear All

### Problem: Users still assigned to CSE/ECE departments
**When running setup_departments.py**, the script will:
- Warn you which users are assigned
- NOT automatically delete the department if users are assigned
- Tell you to reassign users manually

**To reassign users:**
```bash
# Connect to database
psql -U postgres -h localhost -d school_db

# Find users assigned to CSE (department_id = 2)
SELECT id, email, full_name FROM users WHERE assigned_department_id = 2;

# Update them to AIDT (department_id = 1)
UPDATE users SET assigned_department_id = 1 WHERE assigned_department_id = 2;

# Find users assigned to ECE (department_id = 3)
SELECT id, email, full_name FROM users WHERE assigned_department_id = 3;

# Update them to AIDT
UPDATE users SET assigned_department_id = 1 WHERE assigned_department_id = 3;
```

Then run setup again: `python backend/setup_departments.py`

## Complete Setup Flow

### For Fresh Installation
```bash
# 1. Create database
python backend/create_db.py

# 2. Setup departments
python backend/setup_departments.py

# 3. Import academic programs (if CSV available)
python backend/import_departments_and_classes.py

# 4. Verify everything
python backend/SYSTEM_VERIFICATION.py
```

### For Existing System (with CSE/ECE)
```bash
# 1. Backup database
pg_dump -U postgres school_db > backup_before_consolidation.sql

# 2. Run department setup
python backend/setup_departments.py

# 3. If warnings about assigned users:
#    - Manually reassign users (see Troubleshooting section)
#    - Run setup again

# 4. Verify
python backend/SYSTEM_VERIFICATION.py
```

## API Endpoints (Updated)

### Get All Departments
```bash
curl http://localhost:5000/api/departments
```

Response:
```json
[
  {
    "id": 1,
    "name": "AI and Data Science",
    "code": "AIDT",
    "description": "B.Tech - Artificial Intelligence and Data Science"
  },
  {
    "id": 4,
    "name": "Bachelor of Arts",
    "code": "BA",
    "description": "Bachelor of Arts Programs"
  },
  ...
]
```

### Get Department with Classes
```bash
curl http://localhost:5000/api/departments/1/classes
```

Response:
```json
{
  "department": {
    "id": 1,
    "name": "AI and Data Science",
    "code": "AIDT",
    "description": "..."
  },
  "classes": [
    {
      "id": 1,
      "name": "AI",
      "description": "Artificial Intelligence",
      ...
    },
    ...
  ],
  "total": 3
}
```

## Department IDs Reference

| ID | Name | Code | Type |
|----|------|------|------|
| 1 | AI and Data Science | AIDT | Engineering |
| 4 | Bachelor of Arts | BA | Academic |
| 5 | Bachelor of Commerce | BCom | Academic |
| 6 | Bachelor of Business Admin | BBA | Academic |
| 7 | Bachelor of Computer Apps | BCA | Academic |
| 8 | Bachelor of Science | BSc | Academic |

**Note:** IDs 2-3 (CSE/ECE) are intentionally removed and will not be recreated by the setup script.

## FAQ

**Q: Why remove CSE and ECE?**
A: To consolidate engineering programs under a single AI and Data Science (AIDT) department.

**Q: Can I restore CSE/ECE if needed?**
A: Yes, restore from database backup or manually re-add them (not recommended).

**Q: Do existing student records break?**
A: The script updates department mappings. Run SYSTEM_VERIFICATION.py to check.

**Q: What happens to users assigned to CSE/ECE?**
A: The script warns you and requires manual reassignment before deletion.

**Q: Is this reversible?**
A: Yes, restore from database backup. The code changes keep the old mappings in comments.

## More Information

See `DEPARTMENT_CONSOLIDATION.md` for:
- Detailed change log
- Database schema information
- Rollback instructions
- Migration notes for existing systems
