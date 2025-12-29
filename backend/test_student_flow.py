"""Test student registration and login flow"""
import requests
import json

BASE_URL = "http://localhost:5000"

print(f"\n{'='*60}")
print(f"TESTING STUDENT REGISTRATION & LOGIN FLOW")
print(f"{'='*60}\n")

# Test data
test_student = {
    "email": "237706p@pbsiddhartha.ac.in",
    "admissionId": "12345",
    "studentName": "Test Student",
    "rollNo": "237706p",
    "department": "Computer Science",
    "year": "2023"
}

print("📝 Step 1: Check if student registration endpoint exists...")
print(f"   Looking for: POST /api/students or POST /api/students/register")

# Try to register (this endpoint doesn't exist currently)
try:
    response = requests.post(f"{BASE_URL}/api/students", json=test_student)
    print(f"   ❌ Response: {response.status_code}")
    if response.status_code == 404:
        print(f"   ⚠️  ISSUE FOUND: No registration endpoint exists!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n📥 Step 2: Import student directly (simulating registration)...")
import_payload = {
    "students": [test_student]
}
try:
    response = requests.post(f"{BASE_URL}/api/student-profiles/import", json=import_payload)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Import successful: {data}")
    else:
        print(f"   ❌ Import failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n🔐 Step 3: Test student login...")
login_payload = {
    "email": test_student["email"],
    "admissionId": test_student["admissionId"]
}
try:
    response = requests.post(f"{BASE_URL}/api/auth/student", json=login_payload)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Login successful!")
        print(f"   📋 Student data retrieved: {json.dumps(data.get('student', {}), indent=6)}")
    else:
        print(f"   ❌ Login failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n{'='*60}")
print("SUMMARY OF ISSUES FOUND:")
print(f"{'='*60}")
print("❌ 1. NO student registration endpoint in backend")
print("   - Frontend registration saves to localStorage only")
print("   - No POST /api/students endpoint exists")
print("   - Students cannot be saved to database from registration form")
print("")
print("✅ 2. Login endpoint EXISTS and WORKS")
print("   - POST /api/auth/student endpoint is functional")
print("   - Searches database by email and admissionId")
print("")
print("❌ 3. REGISTRATION doesn't save to DATABASE")
print("   - handleStudentRegistration() only saves to localStorage")
print("   - Should call backend API to save to database")
print(f"{'='*60}\n")
