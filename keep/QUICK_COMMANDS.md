# Quick Command Reference - Department Consolidation

## Essential Commands

### Setup Department Configuration
```bash
cd backend
python setup_departments.py
```

### Verify System Health
```bash
cd backend
python SYSTEM_VERIFICATION.py
```

### Test API Endpoints
```bash
# Get all departments
curl http://localhost:5000/api/departments

# Get departments with classes
curl http://localhost:5000/api/departments-with-classes

# Get specific department classes
curl http://localhost:5000/api/departments/1/classes
```

## Database Operations

### Check Current Departments
```bash
# Using Python
cd backend
python -c "
from app import app, Department
with app.app_context():
    depts = Department.query.all()
    for d in sorted(depts, key=lambda x: x.id):
        print(f'{d.id}: {d.name} ({d.code})')
"
```

### Check Current Departments (Direct SQL)
```bash
# Using PostgreSQL
psql -U postgres -h localhost -d school_db -c \
"SELECT id, name, code FROM departments ORDER BY id;"
```

### Find Users Assigned to Deprecated Departments
```bash
# Using Python
cd backend
python -c "
from app import app, User
with app.app_context():
    users = User.query.filter(User.assigned_department_id.in_([2,3])).all()
    for u in users:
        print(f'{u.full_name}: assigned_dept_id={u.assigned_department_id}')
"
```

### Find Users in Deprecated Departments (Direct SQL)
```bash
# Using PostgreSQL
psql -U postgres -h localhost -d school_db -c \
"SELECT id, email, full_name, assigned_department_id FROM users \
WHERE assigned_department_id IN (2, 3) ORDER BY id;"
```

### Reassign Users from CSE to AIDT
```bash
# Using PostgreSQL
psql -U postgres -h localhost -d school_db -c \
"UPDATE users SET assigned_department_id = 1 \
WHERE assigned_department_id = 2;
SELECT 'Updated CSE users to AIDT';"
```

### Reassign Users from ECE to AIDT
```bash
# Using PostgreSQL
psql -U postgres -h localhost -d school_db -c \
"UPDATE users SET assigned_department_id = 1 \
WHERE assigned_department_id = 3;
SELECT 'Updated ECE users to AIDT';"
```

## Backup and Restore

### Create Database Backup
```bash
pg_dump -U postgres -h localhost school_db > \
backup_school_db_$(date +%Y%m%d_%H%M%S).sql
```

### Restore from Backup
```bash
psql -U postgres -h localhost -d school_db < backup_file.sql
```

### Create Full System Backup (including data)
```bash
pg_dump -U postgres -h localhost --verbose school_db | \
gzip > backup_school_db_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from Compressed Backup
```bash
gunzip -c backup_file.sql.gz | \
psql -U postgres -h localhost -d school_db
```

## Testing and Verification

### Test Department Endpoint
```bash
# Bash/Linux
curl -s http://localhost:5000/api/departments | python -m json.tool

# PowerShell
$response = Invoke-WebRequest http://localhost:5000/api/departments
$response.Content | ConvertFrom-Json | ConvertTo-Json
```

### Test Department with Classes Endpoint
```bash
# Get AIDT department (ID 1) with classes
curl -s http://localhost:5000/api/departments/1/classes | python -m json.tool
```

### Count Departments
```bash
# Using Python
cd backend
python -c "
from app import app, Department
with app.app_context():
    count = Department.query.count()
    print(f'Total departments: {count}')
"
```

### Count Activities by Department
```bash
# Using Python
cd backend
python -c "
from app import app, Activity
from collections import defaultdict
with app.app_context():
    activities = Activity.query.all()
    by_dept = defaultdict(int)
    for a in activities:
        dept = a.data.get('department', 'Unknown') if a.data else 'Unknown'
        by_dept[dept] += 1
    for dept in sorted(by_dept.keys()):
        print(f'{dept}: {by_dept[dept]} activities')
"
```

## Application Control

### Start Backend Server
```bash
cd backend
python app.py
```

### Start Backend with Debug Mode
```bash
cd backend
FLASK_ENV=development python app.py
```

### Stop Backend (Ctrl+C in terminal)
```
Use: Ctrl+C
```

### Check if Port 5000 is Available
```bash
# Linux/Mac
lsof -i :5000

# Windows PowerShell
netstat -ano | findstr :5000
```

### Kill Process on Port 5000 (if stuck)
```bash
# Linux/Mac
kill -9 $(lsof -t -i :5000)

# Windows PowerShell
Get-Process | Where-Object {$_.Port -eq 5000} | Stop-Process -Force
```

## Troubleshooting Commands

### Check Python Version
```bash
python --version
```

### Check Flask Installation
```bash
cd backend
python -c "import flask; print(flask.__version__)"
```

### Check PostgreSQL Connection
```bash
psql -U postgres -h localhost -c "SELECT version();"
```

### List All PostgreSQL Databases
```bash
psql -U postgres -h localhost -l
```

### Test Database Connection from Python
```bash
cd backend
python -c "
from app import app, db
try:
    with app.app_context():
        db.session.execute('SELECT 1')
    print('✅ Database connection OK')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

## Browser Testing

### Test Admin Login
```
http://localhost:5000/web/LOGIN-PANEL/admin-auth.html
```

### Test Student Login
```
http://localhost:5000/web/LOGIN-PANEL/student-login.html
```

### Test Admin Dashboard
```
http://localhost:5000/web/pages/admin/admin-dashboard.html
```

### Test Course Registration
```
http://localhost:5000/web/pages/student/course-registration.html
```

## Log Analysis

### View Application Logs (if using logging)
```bash
# Check for Flask debug output
# Logs should appear in the terminal running app.py
```

### Clear Browser Cache and LocalStorage
```javascript
// Run in browser console (F12 → Console)
localStorage.clear();
sessionStorage.clear();
console.log('Cache cleared');
```

## Performance Commands

### Count All Database Records
```bash
cd backend
python -c "
from app import app, User, Student, Role, Department, Coordinator, HOD
with app.app_context():
    print(f'Users: {User.query.count()}')
    print(f'Students: {Student.query.count()}')
    print(f'Departments: {Department.query.count()}')
    print(f'Roles: {Role.query.count()}')
    print(f'Coordinators: {Coordinator.query.count()}')
    print(f'HODs: {HOD.query.count()}')
"
```

### Database Size
```bash
psql -U postgres -h localhost -c \
"SELECT pg_size_pretty(pg_database_size('school_db'));"
```

## Documentation Files to Review

```
Quick Start:       DEPARTMENT_SETUP_GUIDE.md
Full Details:      DEPARTMENT_CONSOLIDATION.md
Structure Diagram: DEPARTMENT_STRUCTURE.md
Summary:          DEPARTMENT_UPDATES_SUMMARY.md
Checklist:        IMPLEMENTATION_CHECKLIST.md
Commands (this):  QUICK_COMMANDS.md
```

## Common Scenarios

### Scenario 1: Fresh Setup
```bash
python backend/create_db.py
python backend/setup_departments.py
python backend/app.py
# Test at http://localhost:5000
```

### Scenario 2: System Already Running
```bash
python backend/setup_departments.py
# Restart: Ctrl+C then python backend/app.py
```

### Scenario 3: Database Issue
```bash
# Backup first
pg_dump -U postgres school_db > backup.sql

# Check status
psql -U postgres -l

# If database corrupted, restore
psql -U postgres -d school_db < backup.sql
```

### Scenario 4: Need to Reassign Users
```bash
# Check who needs reassignment
psql -U postgres -h localhost -d school_db -c \
"SELECT email, assigned_department_id FROM users \
WHERE assigned_department_id IN (2, 3);"

# Reassign them
python backend/setup_departments.py
# Script will warn and provide guidance
```

## Environment Variables

```bash
# .env file location: backend/.env
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
DB_NAME=school_db
SECRET_KEY=<your-secret-key>
```

## Port Availability Check

```bash
# Linux/Mac - Check what's using port 5000
lsof -i :5000

# Windows PowerShell - Check what's using port 5000
Get-NetTCPConnection -LocalPort 5000

# Test if port is open
python -c "
import socket
sock = socket.socket()
try:
    sock.connect(('localhost', 5000))
    print('Port 5000 is open')
except:
    print('Port 5000 is available')
finally:
    sock.close()
"
```

---

**Tip**: Save this file for quick reference during troubleshooting
**Last Updated**: [Current Date]
**Status**: Complete and Ready for Use
