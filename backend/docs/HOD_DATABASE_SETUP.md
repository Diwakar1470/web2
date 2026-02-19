# HOD Database Setup Guide

## Files Created

1. **hod_database_schema.sql** - Database schema definition
2. **hod_migration.py** - Migration script to load HOD data into database
3. **hod_auth_db.py** - Database-backed authentication module

## Database Tables

### 1. hod_credentials
Stores HOD login credentials
```
- hod_id: Primary key
- hod_user_id: Reference to user_info table
- name: HOD full name
- dept_code: Department code
- dept_name: Department name
- email: Email address
- phone: Phone number
- username: Login username (unique)
- password_hash: Bcrypt hashed password
- password_temp: Temporary password (first 4 digits of phone)
- status: active/inactive/suspended
- created_date, last_login, updated_date: Timestamps
```

### 2. department_access
Stores HOD permissions per department
```
- hod_id: Foreign key to hod_credentials
- dept_code: Department code
- student_filter: SQL WHERE clause for filtering students
- can_view_students: Permission flag
- can_approve_requests: Permission flag
- can_view_reports: Permission flag
- can_manage_courses: Permission flag
```

### 3. hod_login_history
Audit log for HOD login attempts
```
- login_id: Primary key
- hod_id: HOD who attempted login
- username: Username used
- ip_address: IP address of login
- login_time: When login occurred
- status: success/failed
- failure_reason: Why login failed (if applicable)
```

### 4. hod_audit_log
Audit trail for HOD actions
```
- audit_id: Primary key
- hod_id: HOD who performed action
- action: Type of action (view_students, approve_request, etc.)
- resource_type: What was accessed (student, request, etc.)
- resource_id: ID of resource accessed
- details: JSON with additional details
- ip_address: IP address of action
- action_time: When action occurred
```

## Setup Instructions

### Step 1: Create Database Tables

```bash
mysql -u root -p college_management < hod_database_schema.sql
```

Or copy-paste the SQL into your MySQL client.

### Step 2: Install Required Package

```bash
pip install bcrypt
```

### Step 3: Configure Migration Script

Edit `hod_migration.py` and update database credentials:

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "your_password"  # Change this
DB_NAME = "college_management"  # Change this
```

### Step 4: Run Migration

```bash
python hod_migration.py
```

Output should show:
```
============================================================
HOD DATABASE MIGRATION
============================================================
✓ Connected to database
✓ HOD credentials table created/verified
✓ Department access table created/verified
✓ Login history table created/verified
✓ Audit log table created/verified
✓ Loaded 19 HOD records from CSV
✓ Inserted perachary_eng (ENG)
✓ Inserted krishna_phy (PHY)
...
✓ Migration completed: 19 inserted, 0 skipped
✓ Database connection closed
```

## Integration with Flask App

### Step 1: Update imports in app.py

```python
from hod_auth_db import HODDatabaseAuth
```

### Step 2: Initialize HOD Auth

```python
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'college_management'
}

hod_auth = HODDatabaseAuth(app, db_config)
```

### Step 3: Add HOD Routes

```python
@app.route('/api/hod/login', methods=['POST'])
def hod_login():
    from flask import request, session, jsonify
    
    data = request.get_json()
    success, result = hod_auth.verify_hod_login(
        data['username'], 
        data['password'],
        request.remote_addr
    )
    
    if success:
        session['hod_session'] = result
        return jsonify({
            'status': 'success',
            'message': 'HOD login successful',
            'hod_info': result
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': result
        }), 401


@app.route('/api/hod/logout', methods=['POST'])
def hod_logout():
    from flask import session, jsonify
    
    if 'hod_session' in session:
        del session['hod_session']
    
    return jsonify({
        'status': 'success',
        'message': 'HOD logout successful'
    }), 200


@app.route('/api/hod/panel', methods=['GET'])
@hod_auth.hod_required
def hod_panel():
    from flask import session, jsonify
    
    hod_info = session['hod_session']
    
    return jsonify({
        'status': 'success',
        'panel_data': {
            'hod_id': hod_info['hod_id'],
            'hod_name': hod_info['name'],
            'department': hod_info['dept_code'],
            'dept_name': hod_info['dept_name'],
            'permissions': hod_info['permissions']
        }
    }), 200


@app.route('/api/hod/students', methods=['GET'])
@hod_auth.hod_required
@hod_auth.hod_department_access
def get_hod_students():
    from flask import session, jsonify, request
    
    hod_id = session['hod_session']['hod_id']
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int)
    
    students = hod_auth.get_department_students(hod_id, limit, offset)
    
    # Log the action
    hod_auth.log_hod_action(
        hod_id,
        'view_students',
        'student_list',
        None,
        {'count': len(students)},
        request.remote_addr
    )
    
    return jsonify({
        'status': 'success',
        'department': session['hod_session']['dept_code'],
        'dept_name': session['hod_session']['dept_name'],
        'total': len(students),
        'students': students
    }), 200


@app.route('/api/hod/approvals', methods=['GET'])
@hod_auth.hod_required
def get_hod_approvals():
    from flask import session, jsonify
    
    hod_id = session['hod_session']['hod_id']
    status = request.args.get('status', 'pending')
    
    approvals = hod_auth.get_hod_approvals(hod_id, status)
    
    return jsonify({
        'status': 'success',
        'department': session['hod_session']['dept_code'],
        'dept_name': session['hod_session']['dept_name'],
        'total_pending': len(approvals),
        'approvals': approvals
    }), 200
```

## Testing

### 1. Test HOD Login

```bash
curl -X POST http://localhost:5000/api/hod/login \
  -H "Content-Type: application/json" \
  -d '{"username": "perachary_eng", "password": "9963"}'
```

Expected response:
```json
{
  "status": "success",
  "message": "HOD login successful",
  "hod_info": {
    "hod_id": 1,
    "hod_user_id": 2001,
    "name": "Sri K.Perachary",
    "dept_code": "ENG",
    "dept_name": "English",
    "phone": "9963043362",
    "email": "",
    "status": "active",
    "permissions": [...]
  }
}
```

### 2. Check Database

```sql
-- Verify HOD credentials loaded
SELECT * FROM hod_credentials;

-- Check login history
SELECT * FROM hod_login_history ORDER BY login_time DESC;

-- Check audit log
SELECT * FROM hod_audit_log ORDER BY action_time DESC;

-- Verify department access
SELECT * FROM department_access;
```

## Security Features

✓ **Password Hashing**: Bcrypt hashing for password storage
✓ **Database Constraints**: Foreign keys and unique constraints
✓ **Audit Trail**: All login attempts and actions logged
✓ **IP Logging**: IP addresses tracked for security
✓ **Department Isolation**: HODs can only access their department's students
✓ **Decorator-Based Security**: Automatic authorization checks

## Production Checklist

- [ ] Change database password from default
- [ ] Set up SSL/TLS for database connection
- [ ] Enable database backups
- [ ] Implement database user roles (separate read/write users)
- [ ] Set up monitoring for failed login attempts
- [ ] Enable database activity logging
- [ ] Configure firewall to restrict database access
- [ ] Implement session timeout (30-60 minutes)
- [ ] Add 2FA for HOD accounts
- [ ] Regular security audits

## Troubleshooting

### Connection Error
```
Error: mysql.connector.errors.ProgrammingError
```
Solution: Check MySQL is running and credentials are correct

### Password Hash Error
```
Error: TypeError: 'str' object cannot be interpreted as an integer
```
Solution: Ensure bcrypt is installed: `pip install bcrypt`

### Migration Fails
```
Error: Duplicate entry for key 'username'
```
Solution: Drop old tables: `DROP TABLE IF EXISTS hod_credentials;` and re-run

## Database Queries

### Get all active HODs
```sql
SELECT * FROM hod_credentials WHERE status = 'active';
```

### Get HOD login history
```sql
SELECT * FROM hod_login_history 
WHERE hod_id = 1 
ORDER BY login_time DESC 
LIMIT 10;
```

### Get HOD audit trail
```sql
SELECT * FROM hod_audit_log 
WHERE hod_id = 1 
ORDER BY action_time DESC 
LIMIT 50;
```

### Get failed login attempts
```sql
SELECT * FROM hod_login_history 
WHERE status = 'failed' 
ORDER BY login_time DESC 
LIMIT 20;
```

### Get department students accessible to HOD
```sql
SELECT s.* FROM student_info s
WHERE s.pcode IN (SELECT CAST(SUBSTRING(student_filter, -2) AS UNSIGNED) FROM department_access WHERE hod_id = 1);
```
