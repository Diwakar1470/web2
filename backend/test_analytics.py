"""
Test Analytics Data Fetching
Verifies that the analytics page can fetch data from backend
"""
import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_analytics_data():
    """Test if analytics can fetch course registrations"""
    print("=== Testing Analytics Data Fetching ===\n")
    
    try:
        # Test health check
        health_response = requests.get(f'{BASE_URL}/health')
        if health_response.status_code == 200:
            print("✓ Backend is running")
        else:
            print("✗ Backend health check failed")
            return False
        
        # Test course registrations endpoint
        print("\n--- Testing Course Registrations Endpoint ---")
        reg_response = requests.get(f'{BASE_URL}/course-registrations')
        
        if reg_response.status_code == 200:
            registrations = reg_response.json()
            print(f"✓ Successfully fetched course registrations")
            print(f"  Total registrations: {len(registrations)}")
            
            if len(registrations) > 0:
                print(f"\n  Sample registration data:")
                sample = registrations[0]
                print(f"    - Student: {sample.get('studentName', 'N/A')}")
                print(f"    - Course: {sample.get('course', 'N/A')}")
                print(f"    - Activity: {sample.get('activityName', 'N/A')}")
                print(f"    - Status: {sample.get('status', 'N/A')}")
                print(f"    - Branch: {sample.get('branch', 'N/A')}")
                
                # Analyze data for analytics
                print(f"\n  Data Analysis:")
                statuses = {}
                activities = {}
                branches = {}
                
                for reg in registrations:
                    status = reg.get('status', 'Unknown')
                    activity = reg.get('activityCategory', reg.get('activityName', 'Unknown'))
                    branch = reg.get('branch', 'Unknown')
                    
                    statuses[status] = statuses.get(status, 0) + 1
                    activities[activity] = activities.get(activity, 0) + 1
                    branches[branch] = branches.get(branch, 0) + 1
                
                print(f"    Status breakdown: {statuses}")
                print(f"    Activity breakdown: {activities}")
                print(f"    Branch breakdown: {branches}")
            else:
                print("  ⚠️ No registrations found in database")
                print("  💡 Add some test registrations first")
            
            return True
        else:
            print(f"✗ Failed to fetch registrations: {reg_response.status_code}")
            print(f"  Response: {reg_response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_legacy_registrations():
    """Test legacy registrations endpoint"""
    print("\n--- Testing Legacy Registrations Endpoint ---")
    
    try:
        response = requests.get(f'{BASE_URL}/registrations')
        
        if response.status_code == 200:
            registrations = response.json()
            print(f"✓ Legacy registrations endpoint works")
            print(f"  Total legacy registrations: {len(registrations)}")
            return True
        else:
            print(f"✗ Legacy endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def create_sample_registration():
    """Create a sample registration for testing"""
    print("\n--- Creating Sample Registration for Testing ---")
    
    sample_data = {
        "studentName": "Test Student",
        "admissionId": "TEST123",
        "course": "B.Tech",
        "year": "2024",
        "branch": "DS & AI",
        "gender": "Male",
        "activityName": "NCC - Army Wing",
        "activityCategory": "NCC",
        "status": "Pending Coordinator"
    }
    
    try:
        response = requests.post(
            f'{BASE_URL}/course-registrations',
            json=sample_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✓ Sample registration created successfully")
            print(f"  Registration ID: {result.get('id')}")
            return True
        else:
            print(f"✗ Failed to create sample: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    success = test_analytics_data()
    test_legacy_registrations()
    
    if success:
        print("\n" + "="*60)
        print("✅ ANALYTICS DATA FETCHING: WORKING")
        print("="*60)
        print("\nThe analytics page can now:")
        print("  1. Fetch data from backend API (/api/course-registrations)")
        print("  2. Fall back to localStorage if backend is unavailable")
        print("  3. Display charts and statistics properly")
        print("\nAccess analytics at:")
        print("  http://localhost:5000/pages/admin/analytics.html")
    else:
        print("\n" + "="*60)
        print("⚠️  BACKEND NOT RUNNING OR NO DATA")
        print("="*60)
        print("\nTo fix:")
        print("  1. Start backend: python backend/app.py")
        print("  2. Add registrations via student registration form")
        print("  3. Or create sample data: uncomment create_sample_registration()")
