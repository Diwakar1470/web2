"""Test auto-fetch functionality with sample data"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("\n" + "="*70)
print("🧪 TESTING AUTO-FETCH FUNCTIONALITY")
print("="*70 + "\n")

# Create test coordinator for NCC
coordinator = {
    "name": "Dr. NCC Coordinator",
    "email": "ncc.coord@pbsiddhartha.ac.in",
    "id": "NCC_COORD_001",
    "role": "NCC"
}

print("1️⃣  Creating Coordinator...")
response = requests.post(f"{BASE_URL}/api/coordinators", json=coordinator)
if response.status_code in [201, 409]:
    print(f"✅ Coordinator ready: {coordinator['name']}")
    print(f"   Role: {coordinator['role']}")
    print(f"   Email: {coordinator['email']}")
else:
    print(f"❌ Failed: {response.text}")

# Create test HOD for CS department
hod = {
    "name": "Dr. CS HOD",
    "email": "cs.hod@pbsiddhartha.ac.in",
    "id": "HOD_CS_001",
    "department": "CS"
}

print("\n2️⃣  Creating HOD...")
response = requests.post(f"{BASE_URL}/api/hods", json=hod)
if response.status_code in [201, 409]:
    print(f"✅ HOD ready: {hod['name']}")
    print(f"   Department: {hod['department']}")
    print(f"   Email: {hod['email']}")
else:
    print(f"❌ Failed: {response.text}")

# Verify they can be fetched
print("\n3️⃣  Verifying Coordinator Fetch...")
response = requests.get(f"{BASE_URL}/api/coordinators")
if response.status_code == 200:
    coordinators = response.json()
    ncc = [c for c in coordinators if c.get('role') == 'NCC']
    if ncc:
        print(f"✅ Found {len(ncc)} NCC coordinator(s)")
        for c in ncc:
            print(f"   📋 Name: {c.get('name')}")
            print(f"   📋 Role: {c.get('role')}")
            print(f"   📋 Email: {c.get('email')}")
    else:
        print(f"⚠️  No NCC coordinators found")
else:
    print(f"❌ Failed to fetch coordinators")

print("\n4️⃣  Verifying HOD Fetch...")
response = requests.get(f"{BASE_URL}/api/hods")
if response.status_code == 200:
    hods = response.json()
    cs_hods = [h for h in hods if h.get('department') == 'CS']
    if cs_hods:
        print(f"✅ Found {len(cs_hods)} CS HOD(s)")
        for h in cs_hods:
            print(f"   📋 Name: {h.get('name')}")
            print(f"   📋 Department: {h.get('department')}")
            print(f"   📋 Email: {h.get('email')}")
    else:
        print(f"⚠️  No CS HODs found")
else:
    print(f"❌ Failed to fetch HODs")

print("\n" + "="*70)
print("FORM 2 AUTO-FETCH TEST INSTRUCTIONS")
print("="*70)
print("\n📝 To test on the frontend:")
print("\n1. Open browser console (F12)")
print("2. Navigate to: http://localhost:5000/pages/student/course-details.html")
print("3. Check console logs for:")
print("   - 🔍 Fetching coordinator for activity: NCC")
print("   - 📋 All coordinators from DB: [...]")
print("   - ✓ Found coordinator: {...}")
print("   - 🎯 Coordinator result: {name: 'Dr. NCC Coordinator', phone: ''}")
print("   - 🔍 Fetching HOD for branch: CS")
print("   - 📋 All HODs from DB: [...]")
print("   - ✓ Found HOD: {...}")
print("   - 🎯 HOD result: {name: 'Dr. CS HOD', phone: ''}")
print("\n4. Verify auto-filled fields:")
print("   ✅ Coordinator Name (Auto): Dr. NCC Coordinator")
print("   ✅ Coordinator Phone (Auto): (fetched if available)")
print("   ✅ HOD Name (Auto): Dr. CS HOD")
print("   ✅ HOD Phone (Auto): (fetched if available)")
print("\n" + "="*70 + "\n")
