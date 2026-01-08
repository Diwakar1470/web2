
import os
from app import app, db, SubActivity, Activity, User

def seed_activities():
    with app.app_context():
        print("[*] Seeding Activity Categories and Sub-Activities...")
        
        # Ensure main categories exist as activities if they don't
        categories = ['NCC', 'NSS', 'Sports', 'Gym', 'Yoga', 'Culturals']
        for cat in categories:
            act = Activity.query.filter_by(name=cat).first()
            if not act:
                act = Activity(name=cat, data={'description': f'{cat} Activity Category'})
                db.session.add(act)
        db.session.commit()

        # Seed Sub-Activities
        sub_activities = [
            # NCC
            {'activity': 'NCC', 'sub': 'Army Wing', 'slots': 50, 'coord': 'ncc@pbsiddhartha.ac.in'},
            {'activity': 'NCC', 'sub': 'Naval Wing', 'slots': 40, 'coord': 'ncc@pbsiddhartha.ac.in'},
            {'activity': 'NCC', 'sub': 'Air Wing', 'slots': 30, 'coord': 'ruhi@pbsiddhartha.ac.in'},
            
            # NSS
            {'activity': 'NSS', 'sub': 'NSS Unit 1', 'slots': 100, 'coord': 'nss@pbsiddhartha.ac.in'},
            {'activity': 'NSS', 'sub': 'NSS Unit 2', 'slots': 100, 'coord': 'nss@pbsiddhartha.ac.in'},
            
            # Sports
            {'activity': 'Sports', 'sub': 'Cricket Academy', 'slots': 25, 'coord': 'sports@pbsiddhartha.ac.in'},
            {'activity': 'Sports', 'sub': 'Athletics Team', 'slots': 30, 'coord': 'sports@pbsiddhartha.ac.in'},
            {'activity': 'Sports', 'sub': 'Volleyball', 'slots': 20, 'coord': 'sports@pbsiddhartha.ac.in'},
            
            # Gym
            {'activity': 'Gym', 'sub': 'Regular Gym', 'slots': 60, 'coord': 'sports@pbsiddhartha.ac.in'},
            
            # Yoga
            {'activity': 'Yoga', 'sub': 'Morning Yoga', 'slots': 40, 'coord': 'sports@pbsiddhartha.ac.in'}
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
                    data={'genderEligibility': 'Both', 'status': 'Active'}
                )
                db.session.add(new_sa)
            else:
                exists.total_slots = sa['slots']
                exists.coordinator_email = sa['coord']
        
        db.session.commit()
        print("[!] Sub-Activities seeded successfully!")

if __name__ == "__main__":
    seed_activities()
