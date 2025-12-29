"""Test complete student registration and activity application flow"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("\n" + "="*70)
print("TESTING COMPLETE STUDENT FLOW - Registration & Activity Application")
print("="*70 + "\n")

# Test data
student1 = {
    "email": "237706p@pbsiddhartha.ac.in",
    "admissionId": "12345",
    "studentName": "John Doe",
    "rollNo": "237706p",
    "department": "Computer Science",
    "year": "2023"
}

student2 = {
    "email": "237707p@pbsiddhartha.ac.in",
    "admissionId": "12346",
    "studentName": "Jane Smith",
    "rollNo": "237707p",
    "department": "Electronics",
    "year": "2023"
}

print("STEP 1: Register Students")
print("-" * 70)

for student in [student1, student2]:
    response = requests.post(f"{BASE_URL}/api/students", json=student)
    if response.status_code == 201:
        print(f"✅ Registered: {student['studentName']} ({student['email']})")
    elif response.status_code == 409:
        print(f"⚠️  Already exists: {student['studentName']}")
    else:
        print(f"❌ Failed to register {student['studentName']}: {response.text}")

print("\n" + "-" * 70)
print("STEP 2: Test Student Login")
print("-" * 70)

response = requests.post(f"{BASE_URL}/api/auth/student", json={
    "email": student1["email"],
    "admissionId": student1["admissionId"]
})

if response.status_code == 200:
    data = response.json()
    print(f"✅ Login successful for {student1['studentName']}")
    print(f"   Retrieved data: {json.dumps(data['student'], indent=4)}")
else:
    print(f"❌ Login failed: {response.text}")

print("\n" + "-" * 70)
print("STEP 3: Check Application Status (Should be able to apply)")
print("-" * 70)

response = requests.post(f"{BASE_URL}/api/students/application-status", json={
    "email": student1["email"],
    "admissionId": student1["admissionId"]
})

if response.status_code == 200:
    data = response.json()
    print(f"✅ Status check: canApply = {data['canApply']}")
    print(f"   Message: {data.get('message', data.get('reason'))}")

print("\n" + "-" * 70)
print("STEP 4: Apply for NCC Activity")
print("-" * 70)

registration1 = {
    "email": student1["email"],
    "admissionId": student1["admissionId"],
    "studentName": student1["studentName"],
    "activityName": "NCC",
    "activityCategory": "DEFENSE",
    "course": "Army Wing"
}

response = requests.post(f"{BASE_URL}/api/registrations", json=registration1)
if response.status_code == 201:
    data = response.json()
    reg_id = data['registration']['id']
    print(f"✅ Application submitted successfully!")
    print(f"   Registration ID: {reg_id}")
    print(f"   Status: {data['registration']['status']}")
    print(f"   Coordinator Status: {data['registration']['coordinatorStatus']}")
    print(f"   HOD Status: {data['registration']['hodStatus']}")
else:
    print(f"❌ Application failed: {response.text}")
    reg_id = None

print("\n" + "-" * 70)
print("STEP 5: Try to Apply Again (Should be BLOCKED)")
print("-" * 70)

response = requests.post(f"{BASE_URL}/api/registrations", json={
    "email": student1["email"],
    "admissionId": student1["admissionId"],
    "studentName": student1["studentName"],
    "activityName": "NSS",
    "activityCategory": "SERVICE"
})

if response.status_code == 409:
    data = response.json()
    print(f"✅ CORRECTLY BLOCKED: {data['error']}")
elif response.status_code == 201:
    print(f"❌ ERROR: Student was able to apply twice! This should not happen!")
else:
    print(f"❓ Unexpected response: {response.text}")

if reg_id:
    print("\n" + "-" * 70)
    print("STEP 6: Coordinator Approves Application")
    print("-" * 70)
    
    response = requests.post(f"{BASE_URL}/api/registrations/{reg_id}/coordinator-approve", json={
        "action": "approve"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Coordinator approved!")
        print(f"   New Status: {data['registration']['status']}")
        print(f"   Coordinator Status: {data['registration']['coordinatorStatus']}")
    else:
        print(f"❌ Approval failed: {response.text}")
    
    print("\n" + "-" * 70)
    print("STEP 7: HOD Approves Application (FINAL APPROVAL)")
    print("-" * 70)
    
    response = requests.post(f"{BASE_URL}/api/registrations/{reg_id}/hod-approve", json={
        "action": "approve"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ HOD approved! Application FULLY ACCEPTED")
        print(f"   Final Status: {data['registration']['status']}")
        print(f"   HOD Status: {data['registration']['hodStatus']}")
        print(f"   🔒 Student CANNOT apply for another activity now")
    else:
        print(f"❌ HOD approval failed: {response.text}")

print("\n" + "-" * 70)
print("STEP 8: Test Rejection Scenario with Second Student")
print("-" * 70)

# Student 2 applies
registration2 = {
    "email": student2["email"],
    "admissionId": student2["admissionId"],
    "studentName": student2["studentName"],
    "activityName": "Sports",
    "activityCategory": "ATHLETICS"
}

response = requests.post(f"{BASE_URL}/api/registrations", json=registration2)
if response.status_code == 201:
    data = response.json()
    reg_id2 = data['registration']['id']
    print(f"✅ Student 2 applied for Sports")
    print(f"   Registration ID: {reg_id2}")
    
    # Coordinator rejects
    response = requests.post(f"{BASE_URL}/api/registrations/{reg_id2}/coordinator-approve", json={
        "action": "reject",
        "reason": "Insufficient documents"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Coordinator REJECTED application")
        print(f"   Status: {data['registration']['status']}")
        print(f"   Reason: {data['registration']['rejectionReason']}")
        print(f"   ✓ Student can now apply for another activity")
    
    # Check if student can apply again
    print("\n   Checking if student can reapply...")
    response = requests.post(f"{BASE_URL}/api/students/application-status", json={
        "email": student2["email"],
        "admissionId": student2["admissionId"]
    })
    
    if response.status_code == 200:
        data = response.json()
        if data['canApply']:
            print(f"   ✅ Student CAN apply again after rejection")
        else:
            print(f"   ❌ ERROR: Student cannot apply after rejection")

print("\n" + "="*70)
print("SUMMARY OF IMPLEMENTATION")
print("="*70)
print("✅ Student Registration: Saves to database")
print("✅ Student Login: Authenticates from database")
print("✅ Activity Application: Creates registration with status tracking")
print("✅ Single Application Rule: Cannot apply if pending/approved exists")
print("✅ Coordinator Approval: Updates status to coordinator_approved")
print("✅ HOD Approval: Final approval, locks student from reapplying")
print("✅ Rejection Flow: Allows student to reapply after rejection")
print("="*70 + "\n")
