& "C:/Users/Admin/Downloads/New folder/web1/.venv/Scripts/python.exe" backend/app.py

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
- **HOD ID:** 12345
- **Access:** Approve/reject student registrations for their department

### Coordinator Login
**URL:** `http://localhost:5000/LOGIN-PANEL/coordinator-login.html`
- **Email:** ruhi@pbsiddhartha.ac.in
- **Coordinator ID:** 123
- **Activity:** NCC
- **Access:** Approve/reject student registrations for their activity

### Student Login (Default)
**URL:** `http://localhost:5000/LOGIN-PANEL/student-login.html`
- **Email:** student@pbsiddhartha.ac.in
- **Roll Number:** 22B91A05L6
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
