"""
Test authentication endpoints
"""
import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f'{BASE_URL}/health')
        print(f"✓ Backend Health: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Backend not running: {e}")
        return False

def test_coordinator_auth():
    """Test coordinator authentication"""
    print("\n--- Testing Coordinator Authentication ---")
    
    # Get all coordinators first
    response = requests.get(f'{BASE_URL}/coordinators')
    coordinators = response.json()
    print(f"Total coordinators in database: {len(coordinators)}")
    
    if coordinators:
        coord = coordinators[0]
        print(f"Testing with: {coord['email']} / {coord['id']}")
        
        # Test authentication
        auth_response = requests.post(
            f'{BASE_URL}/auth/coordinator',
            json={'email': coord['email'], 'id': coord['id']}
        )
        
        if auth_response.status_code == 200:
            print(f"✓ Coordinator auth successful: {auth_response.json()}")
        else:
            print(f"✗ Coordinator auth failed: {auth_response.json()}")
    else:
        print("No coordinators found. Add one using admin panel first.")

def test_hod_auth():
    """Test HOD authentication"""
    print("\n--- Testing HOD Authentication ---")
    
    # Get all HODs first
    response = requests.get(f'{BASE_URL}/hods')
    hods = response.json()
    print(f"Total HODs in database: {len(hods)}")
    
    if hods:
        hod = hods[0]
        print(f"Testing with: {hod['email']} / {hod['id']}")
        
        # Test authentication
        auth_response = requests.post(
            f'{BASE_URL}/auth/hod',
            json={'email': hod['email'], 'id': hod['id']}
        )
        
        if auth_response.status_code == 200:
            print(f"✓ HOD auth successful: {auth_response.json()}")
        else:
            print(f"✗ HOD auth failed: {auth_response.json()}")
    else:
        print("No HODs found. Add one using admin panel first.")

def test_student_auth():
    """Test student authentication"""
    print("\n--- Testing Student Authentication ---")
    
    # Get all students first
    response = requests.get(f'{BASE_URL}/student-profiles')
    students = response.json()
    print(f"Total students in database: {len(students)}")
    
    if students:
        student = students[0]
        email = student.get('email', '')
        admission_id = student.get('admissionId', '')
        print(f"Testing with: {email} / {admission_id}")
        
        if email and admission_id:
            # Test authentication
            auth_response = requests.post(
                f'{BASE_URL}/auth/student',
                json={'email': email, 'admissionId': admission_id}
            )
            
            if auth_response.status_code == 200:
                print(f"✓ Student auth successful: {auth_response.json()}")
            else:
                print(f"✗ Student auth failed: {auth_response.json()}")
        else:
            print("Student missing email or admission ID")
    else:
        print("No students found. Import students first.")

if __name__ == '__main__':
    print("=== Testing Authentication System ===\n")
    
    if test_health():
        test_coordinator_auth()
        test_hod_auth()
        test_student_auth()
    else:
        print("\nPlease start the backend server first:")
        print("  python backend/app.py")
