"""
HOD Login Integration Guide for app.py

Add these imports to your app.py:
    from hod_auth_db import HODDatabaseAuth

Initialize HOD Auth Manager:
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'your_password',
        'database': 'college_management'
    }
    hod_auth = HODDatabaseAuth(app, db_config)

Add these routes to your Flask app:
"""

# HOD Login Route
def hod_login_route(app, hod_auth):
    """
    POST /api/hod/login
    Body: {"username": "username", "password": "password"}
    """
    from flask import request, session, jsonify
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    success, result = hod_auth.verify_hod_login(username, password, request.remote_addr)
    
    if success:
        session['hod_session'] = {
            'hod_id': result['hod_id'],
            'name': result['name'],
            'dept_code': result['dept_code'],
            'dept_name': result['dept_name'],
            'phone': result['phone'],
            'status': result['status']
        }
        return jsonify({
            'status': 'success',
            'message': 'HOD login successful',
            'hod_info': session['hod_session']
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': result
        }), 401


# HOD Logout Route
def hod_logout_route():
    """
    POST /api/hod/logout
    """
    from flask import session, jsonify
    
    if 'hod_session' in session:
        del session['hod_session']
    
    return jsonify({
        'status': 'success',
        'message': 'HOD logout successful'
    }), 200


# Get HOD Panel Dashboard
def hod_panel_route():
    """
    GET /api/hod/panel
    Returns HOD dashboard with department info
    """
    from flask import session, jsonify
    
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    hod_info = session['hod_session']
    
    return jsonify({
        'status': 'success',
        'panel_data': {
            'hod_id': hod_info['hod_id'],
            'hod_name': hod_info['name'],
            'department': hod_info['dept_code'],
            'dept_name': hod_info['dept_name'],
            'phone': hod_info['phone'],
            'available_actions': [
                'view_students',
                'view_approvals',
                'manage_requests',
                'generate_reports'
            ]
        }
    }), 200


# Get Department Students
def hod_students_route(hod_auth):
    """
    GET /api/hod/students
    Returns students only from HOD's department
    """
    from flask import session, jsonify, request
    
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    hod_info = session['hod_session']
    hod_id = hod_info['hod_id']
    
    # Get students for this HOD's department
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
        'department': hod_info['dept_code'],
        'dept_name': hod_info['dept_name'],
        'total': len(students),
        'students': students
    }), 200


# Get Department Approvals Queue
def hod_approvals_route():
    """
    GET /api/hod/approvals
    Returns pending approvals for HOD's department students
    """
    from flask import session, jsonify
    
    if 'hod_session' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    hod_info = session['hod_session']
    dept_code = hod_info['dept_code']
    
    # Query approvals for department students
    # approvals = db.execute(f"SELECT * FROM approvals WHERE dept_code = '{dept_code}' AND status = 'pending'")
    
    return jsonify({
        'status': 'success',
        'department': dept_code,
        'dept_name': hod_info['dept_name'],
        'pending_approvals': [],
        'total_pending': 0
    }), 200


"""
SECURITY NOTES:
1. CHANGE DEFAULT PASSWORDS: HODs must change their password on first login (first 4 digits of phone)
2. ENABLE PASSWORD HASHING: Use bcrypt or similar for production
3. ENABLE SESSION TIMEOUT: Add timeout for inactive HOD sessions
4. ENABLE 2FA: Implement two-factor authentication for security
5. AUDIT LOGGING: Log all HOD actions for compliance
6. DATABASE CONSTRAINTS: Add database-level checks to enforce department access

USAGE IN app.py:
    @app.route('/api/hod/login', methods=['POST'])
    def hod_login():
        return hod_login_route()
    
    @app.route('/api/hod/logout', methods=['POST'])
    def hod_logout():
        return hod_logout_route()
    
    @app.route('/api/hod/panel', methods=['GET'])
    @hod_auth.hod_required
    def hod_panel():
        return hod_panel_route()
    
    @app.route('/api/hod/students', methods=['GET'])
    @hod_auth.hod_required
    @hod_auth.hod_department_access
    def hod_students():
        return hod_students_route()
    
    @app.route('/api/hod/approvals', methods=['GET'])
    @hod_auth.hod_required
    def hod_approvals():
        return hod_approvals_route()
"""
