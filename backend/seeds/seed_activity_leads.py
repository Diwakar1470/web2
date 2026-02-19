#!/usr/bin/env python3
"""
Seed script: Populate activity head and sub-activity lead information
This script adds sample data for the new fields in sub_activities table
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Import Flask app and models
from app import app, db, SubActivity

# Sample data for activity heads and sub-activity leads
ACTIVITY_LEADS = {
    'SPORTS': {
        'head_name': 'Dr. Kavya Sharma',
        'head_phone': '+91 98765 43210',
        'sub_leads': {
            'CRICKET': {'name': 'Mr. Rajesh Kumar', 'phone': '+91 98765 43211'},
            'BASKETBALL': {'name': 'Mr. Arun Singh', 'phone': '+91 98765 43212'},
            'KABADDI': {'name': 'Ms. Priya Verma', 'phone': '+91 98765 43213'},
            'KHO=KHO': {'name': 'Mr. Vikram Patel', 'phone': '+91 98765 43214'},
            'FOOTBALL': {'name': 'Mr. Nikhil Rao', 'phone': '+91 98765 43215'},
            'BADMINTON': {'name': 'Ms. Anjali Singh', 'phone': '+91 98765 43216'},
        }
    },
    'NCC': {
        'head_name': 'Col. Rajendra Singh',
        'head_phone': '+91 99876 54321',
        'sub_leads': {
            '8 (A) NAVY': {'name': 'Lt. Commander Amit Patel', 'phone': '+91 99876 54323'},
            '3 (A) R&V ARMY': {'name': 'Lt. Rahul Verma', 'phone': '+91 99876 54322'},
            '4 (A) GIRLS BATALLION ARMY': {'name': 'Lt. Priya Sharma', 'phone': '+91 99876 54324'},
            '17 (A) BATALLION ARMY': {'name': 'Capt. Deepak Kumar', 'phone': '+91 99876 54325'},
        }
    },
    'YOGA': {
        'head_name': 'Swami Ananda',
        'head_phone': '+91 97654 32109',
        'sub_leads': {
            'YOGA': {'name': 'Yoga Instructor Meera', 'phone': '+91 97654 32110'},
        }
    },
    'GYM': {
        'head_name': 'Mr. Vijay Kumar',
        'head_phone': '+91 96543 21098',
        'sub_leads': {
            'GYM': {'name': 'Coach Rahul', 'phone': '+91 96543 21099'},
        }
    },
    'GOOD HABITS CLUB': {
        'head_name': 'Dr. Anjali Desai',
        'head_phone': '+91 95432 10987',
        'sub_leads': {
            'Good Habits Club': {'name': 'Ms. Sonia', 'phone': '+91 95432 10988'},
        }
    },
    'NSS': {
        'head_name': 'Prof. Ramesh Kulkarni',
        'head_phone': '+91 94321 09876',
        'sub_leads': {
            'NSS Unit 1': {'name': 'Mr. Aditya', 'phone': '+91 94321 09877'},
            'NSS Unit 2': {'name': 'Ms. Neha', 'phone': '+91 94321 09878'},
        }
    },
}

def seed_leads():
    """Seed activity leads into the database"""
    try:
        print("🔄 Seeding activity lead information...")
        
        updated_count = 0
        total_count = 0
        
        # Get all sub-activities
        sub_activities = SubActivity.query.all()
        total_count = len(sub_activities)
        
        for sub_activity in sub_activities:
            activity_name = sub_activity.activity_name
            sub_activity_name = sub_activity.sub_activity_name
            
            # Check if this activity has lead information
            if activity_name in ACTIVITY_LEADS:
                activity_data = ACTIVITY_LEADS[activity_name]
                
                # Set activity head info
                sub_activity.activity_head_name = activity_data['head_name']
                sub_activity.activity_head_phone = activity_data['head_phone']
                
                # Set sub-activity lead info if available
                if sub_activity_name in activity_data['sub_leads']:
                    lead_data = activity_data['sub_leads'][sub_activity_name]
                    sub_activity.sub_activity_lead_name = lead_data['name']
                    sub_activity.sub_activity_lead_phone = lead_data['phone']
                    print(f"  ✓ {activity_name} → {sub_activity_name}")
                    print(f"    Head: {sub_activity.activity_head_name}")
                    print(f"    Lead: {sub_activity.sub_activity_lead_name}")
                else:
                    # Still set the activity head even if no specific lead
                    print(f"  ⚠ {activity_name} → {sub_activity_name}")
                    print(f"    Head: {sub_activity.activity_head_name}")
                
                updated_count += 1
        
        # Commit changes
        db.session.commit()
        
        print(f"\n✅ Seeding completed!")
        print(f"   Updated: {updated_count}/{total_count} sub-activities with activity head information")
        print(f"   Activity leads added where configured")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    with app.app_context():
        seed_leads()
