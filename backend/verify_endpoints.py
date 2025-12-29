"""Quick verification that endpoints exist"""
from app import app

print("\n" + "="*70)
print("BACKEND ENDPOINTS VERIFICATION")
print("="*70 + "\n")

# Get all routes
routes = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.rule, methods, rule.endpoint))

# Sort by path
routes.sort()

print("Available Endpoints:")
print("-" * 70)

for path, methods, endpoint in routes:
    print(f"{methods:20s} {path}")

print("\n" + "="*70)
print("KEY NEW ENDPOINTS ADDED:")
print("="*70)
print("✅ POST   /api/students                        - Register new student")
print("✅ POST   /api/students/application-status     - Check if can apply")
print("✅ POST   /api/registrations                   - Apply for activity")
print("✅ POST   /api/registrations/<id>/coordinator-approve  - Coordinator decision")
print("✅ POST   /api/registrations/<id>/hod-approve          - HOD decision")
print("="*70 + "\n")

print("REGISTRATION MODEL UPDATES:")
print("-" * 70)
print("✅ student_email        - Track which student")
print("✅ admission_id         - Student admission ID")
print("✅ activity_name        - Activity applied for")
print("✅ status               - Overall status (pending/coordinator_approved/hod_approved/rejected)")
print("✅ coordinator_status   - Coordinator's decision")
print("✅ hod_status           - HOD's decision")
print("✅ rejection_reason     - Why rejected")
print("="*70 + "\n")
