"""Quick demo of the complete flow"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("\n" + "="*70)
print("🎓 STUDENT ACTIVITY APPLICATION SYSTEM - DEMO")
print("="*70 + "\n")

# Test Student
student = {
    "email": "237706p@pbsiddhartha.ac.in",
    "admissionId": "12345",
    "studentName": "John Doe",
    "rollNo": "237706p"
}

print("STEP 1: Register Student")
print("-" * 70)
response = requests.post(f"{BASE_URL}/api/students", json=student)
if response.status_code == 201:
    print("✅ Registration successful!")
    print(f"   Student: {student['studentName']}")
    print(f"   Email: {student['email']}")
elif response.status_code == 409:
    print("ℹ️  Student already registered")
else:
    print(f"❌ Registration failed: {response.text}")

print("\nSTEP 2: Login Student")
print("-" * 70)
response = requests.post(f"{BASE_URL}/api/auth/student", json={
    "email": student["email"],
    "admissionId": student["admissionId"]
})
if response.status_code == 200:
    data = response.json()
    print("✅ Login successful!")
    print(f"   Name: {data['student'].get('studentName', 'N/A')}")
else:
    print(f"❌ Login failed: {response.text}")

print("\nSTEP 3: Apply for NCC Activity")
print("-" * 70)
application = {
    "email": student["email"],
    "admissionId": student["admissionId"],
    "studentName": student["studentName"],
    "activityName": "NCC - Army Wing",
    "activityCategory": "DEFENSE"
}
response = requests.post(f"{BASE_URL}/api/registrations", json=application)
if response.status_code == 201:
    data = response.json()
    reg_id = data['registration']['id']
    print("✅ Application submitted!")
    print(f"   Registration ID: {reg_id}")
    print(f"   Activity: {data['registration']['activityName']}")
    print(f"   Status: {data['registration']['status']}")
elif response.status_code == 409:
    print(f"⚠️  {response.json().get('error')}")
    reg_id = None
else:
    print(f"❌ Application failed: {response.text}")
    reg_id = None

print("\nSTEP 4: Try to Apply for Another Activity (Should Fail)")
print("-" * 70)
application2 = {
    "email": student["email"],
    "admissionId": student["admissionId"],
    "studentName": student["studentName"],
    "activityName": "NSS",
    "activityCategory": "SERVICE"
}
response = requests.post(f"{BASE_URL}/api/registrations", json=application2)
if response.status_code == 409:
    print("✅ CORRECTLY BLOCKED!")
    print(f"   Reason: {response.json().get('error')}")
else:
    print(f"❌ ERROR: Should have been blocked!")

if reg_id:
    print("\nSTEP 5: Coordinator Approves")
    print("-" * 70)
    response = requests.post(
        f"{BASE_URL}/api/registrations/{reg_id}/coordinator-approve",
        json={"action": "approve"}
    )
    if response.status_code == 200:
        data = response.json()
        print("✅ Coordinator approved!")
        print(f"   Status: {data['registration']['status']}")
        print(f"   Coordinator: {data['registration']['coordinatorStatus']}")
    
    print("\nSTEP 6: HOD Approves (Final Approval)")
    print("-" * 70)
    response = requests.post(
        f"{BASE_URL}/api/registrations/{reg_id}/hod-approve",
        json={"action": "approve"}
    )
    if response.status_code == 200:
        data = response.json()
        print("✅ HOD APPROVED - FINAL!")
        print(f"   Final Status: {data['registration']['status']}")
        print(f"   HOD Status: {data['registration']['hodStatus']}")
        print(f"   🔒 Student is now locked to this activity")

print("\nSTEP 7: Check Application Status")
print("-" * 70)
response = requests.post(f"{BASE_URL}/api/students/application-status", json={
    "email": student["email"],
    "admissionId": student["admissionId"]
})
if response.status_code == 200:
    data = response.json()
    print(f"   Can Apply: {data['canApply']}")
    if not data['canApply']:
        print(f"   Reason: {data.get('reason')}")

print("\n" + "="*70)
print("✅ DEMO COMPLETE!")
print("="*70)
print("System Features Demonstrated:")
print("  ✅ Student registration to database")
print("  ✅ Student login authentication")
print("  ✅ Activity application submission")
print("  ✅ One-activity-at-a-time enforcement")
print("  ✅ Coordinator approval workflow")
print("  ✅ HOD approval workflow")
print("  ✅ Application status tracking")
print("="*70 + "\n")
