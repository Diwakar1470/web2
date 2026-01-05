#!/usr/bin/env python
"""Test the student login endpoint"""
import json
from app import app, db

def test_student_login():
    """Test the student authentication endpoint"""
    
    # Start the app
    with app.app_context():
        # Create a test client
        client = app.test_client()
        
        # Test with correct credentials
        print("Testing Student Login Endpoint...")
        print("=" * 50)
        
        # Test 1: Correct credentials
        print("\nTest 1: Login with CORRECT credentials")
        response = client.post('/api/auth/student', 
            json={
                'email': '237706p@pbsiddhartha.ac.in',
                'admissionId': '22B91A05L6'
            }
        )
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Test 2: Wrong admission ID
        print("\nTest 2: Login with WRONG admission ID")
        response = client.post('/api/auth/student',
            json={
                'email': '237706p@pbsiddhartha.ac.in',
                'admissionId': '12345'  # Wrong ID
            }
        )
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Test 3: Wrong email
        print("\nTest 3: Login with WRONG email")
        response = client.post('/api/auth/student',
            json={
                'email': 'wrong@pbsiddhartha.ac.in',
                'admissionId': '22B91A05L6'
            }
        )
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        print("\n" + "=" * 50)
        print("Testing Complete!")

if __name__ == '__main__':
    test_student_login()
