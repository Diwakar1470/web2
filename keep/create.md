✅ Enhanced Prompt for Copilot (Creator / Admin Credential Management)

Project Enhancement:
Add a Creator (Super Admin / College Admin) login module to manage creation of HOD and Faculty Coordinator credentials, assign roles, and link them to departments or activities. Update frontend, backend, database, and logic accordingly.

🔹 1️⃣ Creator / Admin Authentication

Add a Creator (Super Admin) login page.

Only Creator can:

Create HOD accounts

Create Faculty Coordinator accounts

Assign roles, departments, and activities

Creator credentials are pre-seeded in the database (or environment-based).

🔹 2️⃣ Credential Creation by Creator

Creator Dashboard must allow:

➤ Create HOD

Fields:

Full Name

Email (used as login username)

Password (temporary / auto-generated)

Role = HOD

Department (e.g., AI & DS, CSE, ECE)

Logic:

One HOD per department

HOD can view only students of assigned department

➤ Create Faculty Coordinator

Fields:

Full Name

Email

Password (temporary / auto-generated)

Role = FACULTY_COORDINATOR

Assigned Main Activity (e.g., Gym, NCC)

Logic:

One or multiple coordinators per activity (configurable)

Coordinator can manage only assigned activity and its sub-activities

🔹 3️⃣ First-Time Login & Profile Completion

After login using creator-generated credentials:

HOD / Faculty Coordinator must be redirected to Complete Profile page.

Profile fields:

Phone number

Age

Gender

Blood group

Address

Profile photo (optional)

Logic:

profileCompleted = false by default

Access to dashboard blocked until profile is completed

After saving profile → profileCompleted = true

🔹 4️⃣ Role-Based Access Control Updates

Update RBAC rules:

Role	Permissions
CREATOR	Create HOD & Faculty Coordinator, assign departments/activities
HOD	View students of assigned department, analytics
FACULTY_COORDINATOR	Create sub-activities, approve students, events, attendance
STUDENT	Apply for activities, view status

Enforce RBAC in:

Backend middleware

Frontend route guards

Menu visibility logic

🔹 5️⃣ Backend Changes

Add/Update Entities:

User

Role

Department

Activity

FacultyActivityMapping

Fields to add:

assignedDepartmentId (HOD)

assignedActivityId (Faculty Coordinator)

profileCompleted

APIs:

POST /creator/create-hod

POST /creator/create-faculty

GET /me

PUT /profile/update

🔹 6️⃣ Frontend Changes

Add new pages:

Creator Login

Creator Dashboard

Create HOD

Create Faculty Coordinator

First Login Profile Completion Page

Role-based dashboards (update existing)

UI Logic:

Hide dashboards if profile not completed

Show alerts for temporary password usage

Show assigned department/activity details in profile

🔹 7️⃣ Database Updates

Add tables / columns:

roles

departments

activities

users.assigned_department_id

users.assigned_activity_id

users.profile_completed

Seed data:

Creator account

Roles

Departments

Activities

Provide:

Migration scripts

Seed SQL scripts

🔹 8️⃣ Validation & Logic Checks

Ensure:

Creator cannot assign invalid departments/activities

HOD sees only their department data

Faculty sees only their activity data

Profile completion enforced

Login credentials work correctly

🎯 Final Instruction for Copilot

Implement a Creator/Admin module that manages credential creation and role assignment for HODs and Faculty Coordinators.
Update frontend, backend, database schema, API logic, and security rules.
Verify end-to-end flow: credential creation → first login → profile completion → role-based dashboard access.