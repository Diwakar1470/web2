"""
Import Activity and Sub-Activity data from AH.csv
This replaces the default/dummy data with real activity data
"""
import mysql.connector
import csv
import os

def main():
    # Connect to database
    conn = mysql.connector.connect(
        host='localhost', 
        database='school_db', 
        user='root', 
        password='1234'
    )
    cur = conn.cursor()
    
    # Read the AH.csv file
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'keep', 'AH.csv')
    
    print("=" * 80)
    print("IMPORTING ACTIVITY DATA FROM AH.csv")
    print("=" * 80)
    
    # Parse the CSV data
    activities = {}  # main_activity -> {head_name, head_phone}
    sub_activities = []  # list of {main_activity, sub_activity, sa_lead}
    
    with open(csv_path, 'r', encoding='latin-1') as f:
        # Read raw to handle special characters
        content = f.read()
        # Clean up the content (remove special chars)
        content = content.replace('\ufffd', ' ')
        content = content.replace('\xa0', ' ')
        lines = content.strip().split('\n')
    
    # Skip header
    for line in lines[1:]:
        if not line.strip():
            continue
        
        parts = line.split(',')
        if len(parts) < 5:
            parts.extend([''] * (5 - len(parts)))
        
        sub_activity = parts[0].strip()
        sa_lead = parts[1].strip()
        main_activity = parts[2].strip().upper()
        ma_head = parts[3].strip()
        ma_phone = parts[4].strip() if len(parts) > 4 else ''
        
        # Clean up ma_head
        if ma_head == 'None':
            ma_head = ''
        
        # Track main activities
        if main_activity:
            if main_activity not in activities:
                activities[main_activity] = {
                    'head_name': ma_head,
                    'head_phone': ma_phone
                }
            # Update if this row has head info
            if ma_head and not activities[main_activity]['head_name']:
                activities[main_activity]['head_name'] = ma_head
            if ma_phone and not activities[main_activity]['head_phone']:
                activities[main_activity]['head_phone'] = ma_phone
        
        # Track sub-activities
        if sub_activity:
            sub_activities.append({
                'main_activity': main_activity,
                'sub_activity': sub_activity,
                'sa_lead': sa_lead
            })
    
    print("\nParsed Main Activities:")
    for name, info in activities.items():
        print(f"  {name}: Head={info['head_name']}, Phone={info['head_phone']}")
    
    print("\nParsed Sub-Activities:")
    for sa in sub_activities:
        print(f"  {sa['main_activity']} -> {sa['sub_activity']} (Lead: {sa['sa_lead']})")
    
    # Clear existing sub-activities
    print("\n" + "=" * 80)
    print("UPDATING DATABASE")
    print("=" * 80)
    
    # First, check existing activities to avoid duplicates
    cur.execute("SELECT id, name FROM activities WHERE name IN ('NCC', 'NSS', 'Sports', 'Gym', 'Yoga', 'Culturals', 'SPORTS', 'YOGA', 'GYM', 'GOOD HABITS CLUB')")
    existing_activities = {row[1].upper(): row[0] for row in cur.fetchall()}
    print(f"\nExisting activity IDs: {existing_activities}")
    
    # Delete existing sub-activities for these main activities
    cur.execute("DELETE FROM sub_activities WHERE activity_name IN ('NCC', 'NSS', 'Sports', 'Gym', 'Yoga', 'SPORTS', 'YOGA', 'GYM')")
    print(f"Deleted {cur.rowcount} old sub-activities")
    
    # Normalize activity names for database (use consistent capitalization)
    activity_name_map = {
        'NCC': 'NCC',
        'NSS': 'NSS',
        'SPORTS': 'Sports',
        'GYM': 'Gym',
        'YOGA': 'Yoga',
        'GOOD HABITS CLUB': 'Good Habits Club'
    }
    
    # Insert or update main activities
    for raw_name, info in activities.items():
        name = activity_name_map.get(raw_name, raw_name)
        
        if raw_name in existing_activities or name.upper() in existing_activities:
            # Update existing
            key = raw_name if raw_name in existing_activities else name.upper()
            activity_id = existing_activities.get(key)
            if activity_id:
                # Get current data first
                cur.execute("SELECT data FROM activities WHERE id = %s", (activity_id,))
                row = cur.fetchone()
                current_data = row[0] if row and row[0] else {}
                if isinstance(current_data, str):
                    import json
                    current_data = json.loads(current_data)
                
                current_data['ma_head_name'] = info['head_name']
                current_data['ma_head_phone'] = info['head_phone']
                
                import json
                cur.execute("""
                    UPDATE activities 
                    SET data = %s
                    WHERE id = %s
                """, (json.dumps(current_data), activity_id))
                print(f"Updated activity: {name} (ID: {activity_id})")
        else:
            # Insert new activity
            import json
            cur.execute("""
                INSERT INTO activities (name, data, created_at, updated_at)
                VALUES (%s, %s, NOW(), NOW())
            """, (name, json.dumps({
                "description": f"{name} Activity",
                "ma_head_name": info['head_name'],
                "ma_head_phone": info['head_phone']
            })))
            new_id = cur.lastrowid
            existing_activities[raw_name] = new_id
            print(f"Inserted new activity: {name} (ID: {new_id})")
    
    # Insert sub-activities
    print("\nInserting sub-activities...")
    
    # Coordinator email mapping (can be updated as needed)
    coordinator_emails = {
        'NCC': 'ncc@pbsiddhartha.ac.in',
        'NSS': 'nss@pbsiddhartha.ac.in',
        'SPORTS': 'sports@pbsiddhartha.ac.in',
        'GYM': 'sports@pbsiddhartha.ac.in',
        'YOGA': 'sports@pbsiddhartha.ac.in',
        'GOOD HABITS CLUB': 'clubs@pbsiddhartha.ac.in'
    }
    
    for sa in sub_activities:
        main_activity = activity_name_map.get(sa['main_activity'], sa['main_activity'])
        ma_info = activities.get(sa['main_activity'], {'head_name': '', 'head_phone': ''})
        coord_email = coordinator_emails.get(sa['main_activity'], 'coordinator@pbsiddhartha.ac.in')
        
        cur.execute("""
            INSERT INTO sub_activities (
                activity_name, 
                sub_activity_name, 
                coordinator_email,
                total_slots,
                filled_slots,
                is_active,
                activity_head_name,
                activity_head_phone,
                sub_activity_lead_name,
                sub_activity_lead_phone,
                data,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            main_activity,
            sa['sub_activity'],
            coord_email,
            50,  # default slots
            0,
            True,
            ma_info['head_name'],
            ma_info['head_phone'],
            sa['sa_lead'],
            '',  # SA lead phone not in CSV
            '{"capacity": 50, "filled": 0, "genderEligibility": "Both", "status": "Active"}'
        ))
        print(f"  Inserted: {main_activity} -> {sa['sub_activity']} (Lead: {sa['sa_lead']})")
    
    conn.commit()
    
    # Verify the import
    print("\n" + "=" * 80)
    print("VERIFICATION - Current Sub-Activities in Database")
    print("=" * 80)
    
    cur.execute("""
        SELECT activity_name, sub_activity_name, activity_head_name, activity_head_phone, 
               sub_activity_lead_name, coordinator_email
        FROM sub_activities 
        ORDER BY activity_name, sub_activity_name
    """)
    
    for row in cur.fetchall():
        print(f"  {row[0]} -> {row[1]}")
        print(f"      MA Head: {row[2] or 'None'} | Phone: {row[3] or 'None'}")
        print(f"      SA Lead: {row[4] or 'None'} | Coordinator: {row[5]}")
    
    conn.close()
    print("\n✅ Import completed successfully!")

if __name__ == '__main__':
    # main()
    print("Skipping activity import as AH.csv is missing.")
