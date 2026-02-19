#!/usr/bin/env python3
"""
Import Activity Leads data from AH.csv into SubActivity table
Updates sub_activity_lead_name, sub_activity_lead_phone, activity_head_name, activity_head_phone
"""

import os
import csv
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, SubActivity
from sqlalchemy import func

# Path to AH.csv
AH_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'keep', 'AH.csv')

def clean_phone(phone):
    """Clean phone number - remove special chars except digits and +"""
    if not phone:
        return ''
    # Remove common artifacts
    phone = phone.strip()
    # Keep only digits, +, and space
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+' or c == ' ')
    return cleaned.strip()

def import_activity_leads():
    """Import activity leads from AH.csv"""
    
    if not os.path.exists(AH_CSV_PATH):
        print(f"❌ File not found: {AH_CSV_PATH}")
        return False
    
    print(f"📂 Reading from: {AH_CSV_PATH}")
    
    updated_count = 0
    created_count = 0
    
    with open(AH_CSV_PATH, newline='', encoding='cp1252') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            sub_activity_name = row.get('sub activity', '').strip()
            sa_lead = row.get(' sa lead', '').strip()  # Note: space before key
            main_activity = row.get('main activity', '').strip()
            ma_head = row.get('ma head', '').strip()
            ma_phone = clean_phone(row.get('ma phone no', ''))
            
            if not main_activity:
                continue
            
            # Find or create sub-activity
            if sub_activity_name:
                # Find existing sub-activity
                sub = SubActivity.query.filter(
                    func.lower(SubActivity.sub_activity_name) == func.lower(sub_activity_name),
                    func.lower(SubActivity.activity_name) == func.lower(main_activity)
                ).first()
                
                if sub:
                    # Update existing
                    sub.sub_activity_lead_name = sa_lead or sub.sub_activity_lead_name
                    sub.activity_head_name = ma_head or sub.activity_head_name
                    sub.activity_head_phone = ma_phone or sub.activity_head_phone
                    updated_count += 1
                    print(f"  ✓ Updated: {sub_activity_name} ({main_activity})")
                else:
                    # Create new sub-activity
                    new_sub = SubActivity(
                        activity_name=main_activity,
                        sub_activity_name=sub_activity_name,
                        sub_activity_lead_name=sa_lead,
                        activity_head_name=ma_head,
                        activity_head_phone=ma_phone,
                        total_slots=50,
                        filled_slots=0,
                        is_active=True
                    )
                    db.session.add(new_sub)
                    created_count += 1
                    print(f"  + Created: {sub_activity_name} ({main_activity})")
            else:
                # Just main activity info - update all matching sub-activities
                subs = SubActivity.query.filter(
                    func.lower(SubActivity.activity_name) == func.lower(main_activity)
                ).all()
                
                for sub in subs:
                    if ma_head and not sub.activity_head_name:
                        sub.activity_head_name = ma_head
                    if ma_phone and not sub.activity_head_phone:
                        sub.activity_head_phone = ma_phone
                    updated_count += 1
                
                if subs:
                    print(f"  ✓ Updated {len(subs)} sub-activities for {main_activity}")
    
    db.session.commit()
    print(f"\n✅ Import complete: {created_count} created, {updated_count} updated")
    return True


if __name__ == '__main__':
    with app.app_context():
        print("=" * 60)
        print("IMPORTING ACTIVITY LEADS")
        print("=" * 60)
        import_activity_leads()
