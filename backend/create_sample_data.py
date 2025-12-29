"""
Create Sample Registration Data for Analytics Testing
"""
import requests
import json

BASE_URL = 'http://localhost:5000/api'

def create_sample_registrations():
    """Create diverse sample registrations for analytics testing"""
    
    sample_registrations = [
        {
            "studentName": "Rajesh Kumar",
            "admissionId": "237701",
            "email": "237701p@pbsiddhartha.ac.in",
            "course": "B.Tech",
            "year": "2023",
            "branch": "DS & AI",
            "gender": "Male",
            "activityName": "NCC - Army Wing",
            "activityCategory": "NCC",
            "status": "Approved by Coordinator"
        },
        {
            "studentName": "Priya Sharma",
            "admissionId": "237702",
            "email": "237702p@pbsiddhartha.ac.in",
            "course": "B.Tech",
            "year": "2023",
            "branch": "DS & AI",
            "gender": "Female",
            "activityName": "NSS - Social Work",
            "activityCategory": "NSS",
            "status": "Pending Coordinator"
        },
        {
            "studentName": "Anil Reddy",
            "admissionId": "237703",
            "email": "237703p@pbsiddhartha.ac.in",
            "course": "B.Tech",
            "year": "2024",
            "branch": "CS",
            "gender": "Male",
            "activityName": "Sports - Cricket",
            "activityCategory": "Sports",
            "status": "Approved by HOD"
        },
        {
            "studentName": "Sneha Rao",
            "admissionId": "237704",
            "email": "237704p@pbsiddhartha.ac.in",
            "course": "B.Tech",
            "year": "2023",
            "branch": "CS",
            "gender": "Female",
            "activityName": "Culturals - Dance",
            "activityCategory": "Culturals",
            "status": "Pending Coordinator"
        },
        {
            "studentName": "Vijay Krishna",
            "admissionId": "237705",
            "email": "237705p@pbsiddhartha.ac.in",
            "course": "B.Com",
            "year": "2023",
            "branch": "BCOM",
            "gender": "Male",
            "activityName": "NCC - Navy Wing",
            "activityCategory": "NCC",
            "status": "Approved by Coordinator"
        },
        {
            "studentName": "Lakshmi Devi",
            "admissionId": "237706",
            "email": "237706p@pbsiddhartha.ac.in",
            "course": "B.Com",
            "year": "2024",
            "branch": "BCOM",
            "gender": "Female",
            "activityName": "Gym - Fitness",
            "activityCategory": "Gym",
            "status": "Approved by HOD"
        },
        {
            "studentName": "Karthik Varma",
            "admissionId": "237707",
            "email": "237707p@pbsiddhartha.ac.in",
            "course": "B.Tech",
            "year": "2024",
            "branch": "DS & AI",
            "gender": "Male",
            "activityName": "Sports - Football",
            "activityCategory": "Sports",
            "status": "Pending HOD"
        },
        {
            "studentName": "Divya Menon",
            "admissionId": "237708",
            "email": "237708p@pbsiddhartha.ac.in",
            "course": "B.Tech",
            "year": "2023",
            "branch": "CS",
            "gender": "Female",
            "activityName": "Culturals - Music",
            "activityCategory": "Culturals",
            "status": "Approved by Coordinator"
        }
    ]
    
    print("=== Creating Sample Registrations ===\n")
    created = 0
    failed = 0
    
    for reg in sample_registrations:
        try:
            response = requests.post(
                f'{BASE_URL}/course-registrations',
                json=reg,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                result = response.json()
                created += 1
                print(f"✓ Created: {reg['studentName']} - {reg['activityName']} ({reg['status']})")
            else:
                failed += 1
                print(f"✗ Failed: {reg['studentName']} - {response.status_code}")
        except Exception as e:
            failed += 1
            print(f"✗ Error creating {reg['studentName']}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {created} created, {failed} failed")
    print(f"{'='*60}")
    
    if created > 0:
        print(f"\n✅ Sample data created successfully!")
        print(f"\nYou can now view analytics at:")
        print(f"  http://localhost:5000/pages/admin/analytics.html")
        print(f"\nData breakdown:")
        
        # Show statistics
        statuses = {}
        activities = {}
        branches = {}
        
        for reg in sample_registrations[:created]:
            statuses[reg['status']] = statuses.get(reg['status'], 0) + 1
            activities[reg['activityCategory']] = activities.get(reg['activityCategory'], 0) + 1
            branches[reg['branch']] = branches.get(reg['branch'], 0) + 1
        
        print(f"  Statuses: {statuses}")
        print(f"  Activities: {activities}")
        print(f"  Branches: {branches}")
        
        return True
    else:
        print(f"\n⚠️ No sample data could be created")
        print(f"Please check if backend is running: python backend/app.py")
        return False

if __name__ == '__main__':
    # Check if backend is running
    try:
        health = requests.get(f'{BASE_URL}/health', timeout=2)
        if health.status_code == 200:
            print("✓ Backend is running\n")
            create_sample_registrations()
        else:
            print("✗ Backend health check failed")
    except Exception as e:
        print("✗ Backend is not running!")
        print(f"  Error: {e}")
        print("\nPlease start the backend first:")
        print("  python backend/app.py")
