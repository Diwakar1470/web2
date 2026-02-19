
import os
from app import app, db, SubActivity, Activity, User

def seed_activities():
    with app.app_context():
        print("[*] Seeding Activity Categories and Sub-Activities...")
        
        # Ensure main categories exist as activities if they don't
        categories = ['NCC', 'SPORTS', 'YOGA', 'GYM', 'GOOD HABITS CLUB', 'NSS', 'Culturals']
        ma_details = {
            'NCC': {'head': 'Lt. Dr. M. Dhadurya Naik', 'phone': '+91 98482 80815'},
            'SPORTS': {'head': 'Dr. Bala Krishna Reddy', 'phone': '0866 - 2475966'},
            'YOGA': {'head': 'Dr. Bala Krishna Reddy', 'phone': ''},
            'GYM': {'head': 'Dr. Bala Krishna Reddy', 'phone': ''},
            'GOOD HABITS CLUB': {'head': 'Lt. Dr. Rohini Kusuma', 'phone': '+91 98482 31214'},
            'NSS': {'head': 'NSS Program Officer', 'phone': ''},
            'Culturals': {'head': 'Cultural Coordinator', 'phone': ''}
        }

        for cat in categories:
            act = Activity.query.filter_by(name=cat).first()
            details = ma_details.get(cat, {})
            if not act:
                act = Activity(name=cat, data={
                    'description': f'{cat} Activity Category',
                    'head': details.get('head', ''),
                    'phone': details.get('phone', '')
                })
                db.session.add(act)
            else:
                act.data = {
                    'description': f'{cat} Activity Category',
                    'head': details.get('head', ''),
                    'phone': details.get('phone', '')
                }
        db.session.commit()

        # Seed Sub-Activities
        sub_activities = [
            # NCC
            {'activity': 'NCC', 'sub': '8 (A) NAVY', 'slots': 50, 'coord': 'gdiwakar@pbsiddhartha.ac.in', 'lead': 'G DIWAKAR'},
            {'activity': 'NCC', 'sub': '3 (A) R&V ARMY', 'slots': 40, 'coord': 'klnarendra@pbsiddhartha.ac.in', 'lead': 'KL NARENDRA'},
            {'activity': 'NCC', 'sub': '4 (A) GIRLS BATALLION ARMY', 'slots': 30, 'coord': 'chyasaswi@pbsiddhartha.ac.in', 'lead': 'CH YASASWI'},
            {'activity': 'NCC', 'sub': '17 (A) BATALLION ARMY', 'slots': 30, 'coord': 'sandeeper@pbsiddhartha.ac.in', 'lead': 'SANDEEP R'},
            
            # NSS
            {'activity': 'NSS', 'sub': 'NSS Unit 1', 'slots': 100, 'coord': 'nss1@pbsiddhartha.ac.in', 'lead': 'NSS Unit 1 Lead'},
            {'activity': 'NSS', 'sub': 'NSS Unit 2', 'slots': 100, 'coord': 'nss2@pbsiddhartha.ac.in', 'lead': 'NSS Unit 2 Lead'},
            
            # Sports
            {'activity': 'SPORTS', 'sub': 'CRICKET', 'slots': 50, 'coord': 'sports@pbsiddhartha.ac.in', 'lead': 'Cricket Coach'},
            {'activity': 'SPORTS', 'sub': 'BASKETBALL', 'slots': 30, 'coord': 'sports@pbsiddhartha.ac.in', 'lead': 'Basketball Coach'},
            {'activity': 'SPORTS', 'sub': 'KABADDI', 'slots': 25, 'coord': 'sports@pbsiddhartha.ac.in', 'lead': 'Kabaddi Coach'},
            {'activity': 'SPORTS', 'sub': 'KHO=KHO', 'slots': 25, 'coord': 'sports@pbsiddhartha.ac.in', 'lead': 'Kho-Kho Coach'},
            {'activity': 'SPORTS', 'sub': 'FOOTBALL', 'slots': 30, 'coord': 'sports@pbsiddhartha.ac.in', 'lead': 'Football Coach'},
            {'activity': 'SPORTS', 'sub': 'BADMINTON', 'slots': 20, 'coord': 'sports@pbsiddhartha.ac.in', 'lead': 'Badminton Coach'},
            
            # Gym
            {'activity': 'GYM', 'sub': 'GYM', 'slots': 60, 'coord': 'gym@pbsiddhartha.ac.in', 'lead': 'Gym Instructor'},
            
            # Yoga
            {'activity': 'YOGA', 'sub': 'YOGA', 'slots': 40, 'coord': 'yoga@pbsiddhartha.ac.in', 'lead': 'Yoga Instructor'},

            # Good Habits Club
            {'activity': 'GOOD HABITS CLUB', 'sub': 'Good Habits Club', 'slots': 50, 'coord': 'ghc@pbsiddhartha.ac.in', 'lead': 'GHC Lead'}
        ]

        for sa in sub_activities:
            exists = SubActivity.query.filter_by(activity_name=sa['activity'], sub_activity_name=sa['sub']).first()
            if not exists:
                new_sa = SubActivity(
                    activity_name=sa['activity'],
                    sub_activity_name=sa['sub'],
                    total_slots=sa['slots'],
                    filled_slots=0,
                    coordinator_email=sa['coord'],
                    is_active=True,
                    data={'genderEligibility': 'Both', 'status': 'Active', 'lead': sa['lead']}
                )
                db.session.add(new_sa)
            else:
                exists.total_slots = sa['slots']
                exists.coordinator_email = sa['coord']
                exists.data = {'genderEligibility': 'Both', 'status': 'Active', 'lead': sa['lead']}
        
        db.session.commit()
        print("[!] Sub-Activities seeded successfully!")

if __name__ == "__main__":
    seed_activities()
