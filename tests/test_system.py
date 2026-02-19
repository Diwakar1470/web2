#!/usr/bin/env python3
"""
QUICK TEST SCRIPT - Verify Frontend & Backend Integration
Checks all URLs, redirects, and basic functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = 'http://localhost:5000'
FRONTEND_PATH = 'd:/web1/web1/web'

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

print(f"\n{BLUE}{'='*70}{RESET}")
print(f"{BLUE}SYSTEM VERIFICATION TEST SUITE{RESET}")
print(f"{BLUE}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
print(f"{BLUE}{'='*70}{RESET}\n")

# Tests
tests_passed = 0
tests_failed = 0

def test_backend_health():
    """Test if backend is running"""
    global tests_passed, tests_failed
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"{GREEN}✓ PASS{RESET}: Backend is running on {BACKEND_URL}")
            tests_passed += 1
            return True
        else:
            print(f"{RED}✗ FAIL{RESET}: Backend returned status {response.status_code}")
            tests_failed += 1
            return False
    except requests.exceptions.ConnectionError:
        print(f"{RED}✗ FAIL{RESET}: Cannot connect to backend at {BACKEND_URL}")
        print(f"     Ensure: python start_server.py is running")
        tests_failed += 1
        return False
    except Exception as e:
        print(f"{RED}✗ FAIL{RESET}: Backend health check error - {str(e)}")
        tests_failed += 1
        return False

def test_api_endpoints():
    """Test critical API endpoints"""
    global tests_passed, tests_failed
    endpoints = [
        ('/api/students', 'GET'),
        ('/api/activities', 'GET'),
        ('/api/events', 'GET'),
    ]
    
    print(f"\n{YELLOW}Testing API Endpoints:{RESET}")
    for endpoint, method in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 400]:  # 400 is ok for missing params
                print(f"  {GREEN}✓{RESET} {method} {endpoint}")
                tests_passed += 1
            else:
                print(f"  {RED}✗{RESET} {method} {endpoint} (status: {response.status_code})")
                tests_failed += 1
        except Exception as e:
            print(f"  {RED}✗{RESET} {method} {endpoint} - {str(e)}")
            tests_failed += 1

def test_frontend_structure():
    """Verify frontend folder structure"""
    global tests_passed, tests_failed
    import os
    
    print(f"\n{YELLOW}Checking Frontend Structure:{RESET}")
    
    required_folders = [
        'pages/login',
        'pages/student',
        'pages/hod',
        'pages/faculty-coordinator',
        'pages/student-coordinator',
        'pages/creator',
        'js'
    ]
    
    for folder in required_folders:
        path = os.path.join(FRONTEND_PATH, folder)
        if os.path.isdir(path):
            print(f"  {GREEN}✓{RESET} {folder}/")
            tests_passed += 1
        else:
            print(f"  {RED}✗{RESET} {folder}/ MISSING")
            tests_failed += 1

def test_critical_files():
    """Verify critical files exist"""
    global tests_passed, tests_failed
    import os
    
    print(f"\n{YELLOW}Checking Critical Files:{RESET}")
    
    critical_files = [
        'index.html',
        'js/app-all.js',
        'pages/login/student-login.html',
        'pages/login/hod-login.html',
        'pages/login/faculty-coordinator-login.html',
        'pages/login/student-coordinator-login.html',
        'pages/login/admin-auth.html',
        'pages/student/student-panel.html',
        'pages/hod/hod-panel.html',
        'pages/faculty-coordinator/faculty-coordinator-panel.html',
        'pages/student-coordinator/student-coordinator-panel.html',
    ]
    
    for file in critical_files:
        path = os.path.join(FRONTEND_PATH, file)
        if os.path.isfile(path):
            print(f"  {GREEN}✓{RESET} {file}")
            tests_passed += 1
        else:
            print(f"  {RED}✗{RESET} {file} MISSING")
            tests_failed += 1

def test_javascript_modules():
    """Verify JavaScript modules are in app-all.js"""
    global tests_passed, tests_failed
    import os
    
    print(f"\n{YELLOW}Checking JavaScript Modules:{RESET}")
    
    app_all_path = os.path.join(FRONTEND_PATH, 'js/app-all.js')
    if not os.path.isfile(app_all_path):
        print(f"  {RED}✗{RESET} app-all.js not found")
        tests_failed += 1
        return
    
    with open(app_all_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modules = [
        ('BackendClient', 'Backend API module'),
        ('QueueManager', 'Queue management module'),
        ('getCurrentUser', 'Authentication module'),
        ('getAccessibleForms', 'Access control module'),
        ('updateActivitySlots', 'Activity slots module'),
    ]
    
    for module_name, description in modules:
        if module_name in content:
            print(f"  {GREEN}✓{RESET} {description} ({module_name})")
            tests_passed += 1
        else:
            print(f"  {RED}✗{RESET} {description} ({module_name}) MISSING")
            tests_failed += 1

def print_summary():
    """Print test summary"""
    global tests_passed, tests_failed
    total = tests_passed + tests_failed
    percentage = (tests_passed / total * 100) if total > 0 else 0
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {tests_passed}{RESET}")
    print(f"{RED}Failed: {tests_failed}{RESET}")
    print(f"Success Rate: {percentage:.1f}%")
    
    if tests_failed == 0:
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✓ ALL TESTS PASSED - SYSTEM READY{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}✗ {tests_failed} TEST(S) FAILED - SEE ABOVE FOR DETAILS{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == '__main__':
    try:
        test_backend_health()
        if tests_passed > 0:  # Only test API if backend is running
            test_api_endpoints()
        test_frontend_structure()
        test_critical_files()
        test_javascript_modules()
        exit_code = print_summary()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {str(e)}{RESET}")
        sys.exit(1)
