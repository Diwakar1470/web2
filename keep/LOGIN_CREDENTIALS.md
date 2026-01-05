& "C:/Users/Admin/Downloads/New folder/web1/.venv/Scripts/python.exe" backend/app.py


in our project students will first register and create account there data login details are saved to database and then later sued to login
in the student page in the available activities students can see the available activties available slots free or no.of slots free and filled andif that activty i filled comletely itwill not be shown at available sub activties, the sub activties are createed by there repectively asigned roles by creator login for example if i assign gym activty to a faculty coordinator he will be aigned gym role and he cancreate ub activties in hi page with no,of lots available ,no.of fillings etc these are at manage activties and if astudent register for the a sub activty under gym this facultycoordinator can view there details that after student submit application will be sent to approval for faculty coordinator and if he approve it will be ent to the hod of the student elected department course like ai and d dept hod dr k uday sri,gym assigned to rushi and if a student i from ai and ds course and he selects gym activty and gym1 sub activity firt the applicatiuon form will be ent to faculty coordinator for approval here it is ruhi undergym role and if he approve it will be forwarded to the tudent coure hod for apprpoval if bpoth accept the student i accepted and falls under activty7 enrolled list and incae of rejected he enters rejected list and informed activty rejected apply another one and to apply again for actvivty from start , the faculty coordinator have a tudent records page where the faculty rushi can view all the student under hi activty and ubactivty by filtering year and branch and class   he can see the only regitered tudent under his role on those clae and view there data like blood group contact info age etc and then having a page event management wher the faculkty creator will create event and aign tudent to work for that activty by selecting them fi;ltering and aign tem to attend event and alo take attendance and another attendance page to take online attendance daily and also analytics page for viewing students attendance performance and activty performance
hod like udaysri mam can view data of students only under there department like ai and ds hod can also filter data and check analytric and stats of students under her department hod can see how many of students registered in different activties and check there attendance and stats

# Login Credentials Guide

## System Access Credentials

### Creator/Admin Login
**URL:** `http://localhost:5000/LOGIN-PANEL/creator-login.html`
- **Email:** admin@pbsiddhartha.ac.in
- **Password:** admin123
- **Access:** Full system control - manage coordinators and HODs

### HOD (Head of Department) Login
**URL:** `http://localhost:5000/LOGIN-PANEL/hod-login.html`
- **Email:** hod@pbsiddhartha.ac.in
- **Password:** hod123
- **Access:** Approve/reject student registrations for their department

### Coordinator Login
**URL:** `http://localhost:5000/LOGIN-PANEL/coordinator-login.html`
- **Email:** ruhi@pbsiddhartha.ac.in
- **Password:** ruhi123
- **Activity:** NCC
- **Access:** Approve/reject student registrations for their activity

### Student Login (Default)
**URL:** `http://localhost:5000/LOGIN-PANEL/student-login.html`
- **Email:** student@pbsiddhartha.ac.in
- **Password:** student123
- **Access:** Register for courses and activities

## Database Credentials
**Host:** localhost
**Port:** 5432
**Database:** school_db
**Username:** postgres
**Password:** 1234

## Important Notes

1. **Backend Server:** Must be running on `http://localhost:5000`
   - Start with: `START_BACKEND.bat` or `python backend/app.py`

2. **Authentication Flow:**
   - All login pages now authenticate through backend API endpoints
   - Credentials are stored in PostgreSQL database
   - Session management via localStorage

3. **Password Security:**
   - Current implementation uses simple matching (no hashing)
   - For production, implement proper password hashing (bcrypt/argon2)

## Quick Access Links

- **Creator Management:** http://localhost:5000/LOGIN-PANEL/admin-auth.html (requires authentication)
- **Analytics Dashboard:** http://localhost:5000/pages/admin/analytics.html
- **Coordinator Panel:** http://localhost:5000/pages/coordinator/coordinator-panel.html
- **HOD Panel:** http://localhost:5000/LOGIN-PANEL/hod-panel.html
- **Student Panel:** http://localhost:5000/student-panel.html

## Backend API Endpoints

Authentication:
- POST `/api/auth/student` - Student authentication
- POST `/api/auth/coordinator` - Coordinator authentication  
- POST `/api/auth/hod` - HOD authentication

For complete API documentation, see `BACKEND_ENDPOINTS_ANALYSIS.md`
