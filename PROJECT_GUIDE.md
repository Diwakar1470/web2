# 📋 School Course Registration System - Project Guide Map

**Project Created**: January 2026  
**Last Updated**: January 6, 2026  
**Status**: Active Development

---

## 📌 Quick Reference

| Aspect | Details |
|--------|---------|
| **Project Name** | School Course Registration System |
| **Type** | Web-based Application |
| **Purpose** | Course registration, approval workflows, and student management |
| **Backend** | Python Flask with PostgreSQL |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Database** | PostgreSQL 12+ |
| **Server Port** | 5000 (Backend) |

---

## 🎯 Project Objectives

- ✅ Provide role-based course registration system
- ✅ Implement multi-level approval workflows (Admin → HOD → Coordinator → Student)
- ✅ Manage student profiles and registration records
- ✅ Support extracurricular activities (NCC, Sports, Culturals)
- ✅ Generate analytics and reports

---

## 👥 User Roles & Permissions

| Role | Responsibilities | Access |
|------|------------------|--------|
| **Admin** | System administration, user management, global settings | Full system access |
| **HOD** | Department-level management, approve registrations | Department data only |
| **Coordinator** | Student coordination, manage queues and approvals | Department & activities |
| **Student** | Course registration, profile completion | Own data & available courses |

---

## 🏗️ Project Structure

```
project/web1/
├── backend/                          # Flask API Server
│   ├── app.py                       # Main Flask application
│   ├── create_db.py                 # Database initialization
│   ├── requirements.txt             # Python dependencies
│   ├── departments_and_classes.json # Department configuration
│   ├── SYSTEM_VERIFICATION.py       # Health check script
│   └── __pycache__/
│
├── web/                              # Frontend Files
│   ├── index.html                   # Main page
│   ├── admin-auth.html              # Admin login
│   ├── student-panel.html           # Student dashboard
│   ├── hod-panel.html               # HOD management panel
│   ├── coordinator-panel.html       # Coordinator management
│   ├── LOGIN-PANEL/                 # Login pages
│   ├── pages/                       # Role-based pages
│   │   ├── admin/
│   │   ├── coordinator/
│   │   ├── hod/
│   │   └── student/
│   ├── scripts/                     # JavaScript utilities
│   │   ├── backend-client.js        # API communication
│   │   ├── auth-config.js           # Authentication
│   │   ├── rbac-guard.js            # Access control
│   │   └── [other scripts]
│   ├── CULTURALS/                   # Cultural activities
│   ├── NCC/                         # NCC programs
│   └── SPORTS/                      # Sports programs
│
├── file/                             # Sample Data (CSV)
│   ├── student_info.csv
│   ├── program_info.csv
│   ├── subjects.csv
│   └── user_info.csv
│
├── keep/                             # Important Documentation
│   ├── README_POSTGRESQL.md         # Database setup guide
│   ├── QUICK_COMMANDS.md            # Useful commands
│   ├── VERIFICATION_GUIDE.md        # System checks
│   ├── DEPARTMENT_SETUP_GUIDE.md    # Department config
│   ├── LOGIN_CREDENTIALS.md         # Test credentials
│   ├── START_BACKEND.bat            # Batch script to start
│   └── [other documentation]
│
├── README.md                         # Project overview
├── PROJECT_GUIDE.md                 # This file - Master guide
├── SETUP_POSTGRESQL.bat             # Windows PostgreSQL setup
└── [other config files]
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ (installed and running)
- Git
- Modern web browser

### Quick Start (5 minutes)

1. **Start Backend**
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

2. **Open Frontend**
   - Navigate to `web/index.html` in your browser
   - Or access via: `http://localhost:5000`

3. **Database Setup** (first time only)
   ```powershell
   python create_db.py
   ```

---

## 🔧 Technology Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: PostgreSQL 12+
- **ORM**: SQLAlchemy (if used)
- **API Style**: RESTful

### Frontend
- **HTML5**: Page structure
- **CSS3**: Styling and responsive design
- **JavaScript**: Client-side logic and API communication
- **AJAX**: Asynchronous server communication

### Database
- **Type**: Relational (PostgreSQL)
- **Tables**: students, registrations, users, departments, etc.

---

## 📊 Database Schema

### Key Tables

**students**
- `id` (Primary Key)
- `lookup_key` (Unique - rollNo or email)
- `profile` (JSON - student details)
- `created_at`, `updated_at`

**registrations**
- `id` (Primary Key)
- `student_id` (Foreign Key)
- `data` (JSON - registration details)
- `timestamp`

**departments**
- `id` (Primary Key)
- `name`
- `hod_id`
- `created_at`

**users**
- `id` (Primary Key)
- `username`
- `password` (hashed)
- `role` (admin, hod, coordinator, student)
- `department_id`

---

## 🔌 API Endpoints

### Health & Status
- `GET /api/health` — Server and database status

### Student Management
- `GET /api/student-profiles` — Get all student profiles
- `POST /api/student-profiles/import` — Import student data
- `GET /api/student-profiles/<id>` — Get specific student
- `PUT /api/student-profiles/<id>` — Update student profile

### Registrations
- `GET /api/registrations` — Get all registrations
- `POST /api/registrations` — Create new registration
- `GET /api/registrations/<id>` — Get specific registration

### Authentication
- `POST /api/auth/login` — User login
- `POST /api/auth/logout` — User logout
- `GET /api/auth/verify` — Verify current session

### Approvals & Queues
- `GET /api/approvals` — Get pending approvals
- `POST /api/approvals/<id>/approve` — Approve item
- `POST /api/approvals/<id>/reject` — Reject item
- `GET /api/queues` — Get registration queues

---

## 📁 Important Files & Locations

| File | Purpose | Location |
|------|---------|----------|
| `app.py` | Main Flask application | `backend/` |
| `create_db.py` | Database creation script | `backend/` |
| `requirements.txt` | Python dependencies | `backend/` |
| `backend-client.js` | API communication helper | `web/scripts/` |
| `auth-config.js` | Authentication configuration | `web/scripts/` |
| `rbac-guard.js` | Access control | `web/scripts/` |
| `departments_and_classes.json` | Department settings | `backend/` |

---

## 🔐 Authentication & Access Control

### Login Flow
1. User enters credentials at login page
2. Backend validates credentials against database
3. Session token/JWT created
4. Role-based access control (RBAC) applied
5. User redirected to role-specific dashboard

### Session Management
- Check `auth-config.js` for authentication settings
- RBAC logic in `rbac-guard.js`
- Protected endpoints require valid session

---

## 📝 Useful Commands

```powershell
# Navigate to backend
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install/update dependencies
pip install -r requirements.txt

# Start Flask server
python app.py

# Check system health
python SYSTEM_VERIFICATION.py

# Reset database (if needed)
python create_db.py

# Deactivate virtual environment
deactivate
```

For more commands, see `keep/QUICK_COMMANDS.md`

---

## ✅ Verification Checklist

Before deploying or after setup, verify:

- [ ] PostgreSQL is running
- [ ] Backend server starts without errors
- [ ] Can access frontend pages
- [ ] Can login with test credentials
- [ ] Database tables exist
- [ ] All API endpoints respond
- [ ] RBAC is working (roles have correct access)

Run: `python SYSTEM_VERIFICATION.py` for automated checks

---

## 🐛 Common Issues & Solutions

### PostgreSQL Connection Failed
**Solution**: Ensure PostgreSQL service is running
```powershell
# Windows: Check services or restart PostgreSQL
net start postgresql-x64-15  # Replace 15 with your version
```

### Port 5000 Already in Use
**Solution**: Change port in `app.py` or kill process using port 5000

### Module Import Errors
**Solution**: Reinstall dependencies
```powershell
pip install --upgrade -r requirements.txt
```

### Database Table Not Found
**Solution**: Recreate database
```powershell
python create_db.py
```

For more troubleshooting, see `keep/VERIFICATION_GUIDE.md`

---

## 📅 Development Roadmap

### Phase 1: Core Features ✅
- [x] User authentication (multi-role)
- [x] Student profile management
- [x] Basic course registration
- [x] Database schema

### Phase 2: Approval Workflows
- [ ] Admin approval system
- [ ] HOD approval queue
- [ ] Coordinator assignment
- [ ] Status tracking

### Phase 3: Extracurricular Activities
- [ ] NCC management
- [ ] Sports coordination
- [ ] Cultural events
- [ ] Activity registration

### Phase 4: Analytics & Reporting
- [ ] Registration statistics
- [ ] Department reports
- [ ] Student analytics
- [ ] Export functionality

### Phase 5: Advanced Features
- [ ] Email notifications
- [ ] Mobile responsiveness
- [ ] Advanced filtering
- [ ] Batch operations

---

## 📋 Configuration Files

### `.env` (Backend Configuration)
Location: `backend/.env`
```
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
DB_NAME=school_db
FLASK_ENV=development
PORT=5000
```

### `departments_and_classes.json`
Location: `backend/departments_and_classes.json`
- Contains department list
- Contains class/program information
- Update this to add new departments

---

## 🔗 Important Documentation Files

| File | Description | Location |
|------|-------------|----------|
| README.md | Project overview | Root |
| README_POSTGRESQL.md | Database setup guide | `keep/` |
| QUICK_COMMANDS.md | Common commands & tips | `keep/` |
| VERIFICATION_GUIDE.md | System verification steps | `keep/` |
| DEPARTMENT_SETUP_GUIDE.md | Department configuration | `keep/` |
| LOGIN_CREDENTIALS.md | Test user credentials | `keep/` |
| backend/README.md | Backend-specific docs | `backend/` |

---

## 👤 Test Credentials

For test logins, see `keep/LOGIN_CREDENTIALS.md`

Common test accounts:
- **Admin**: admin@school.edu / admin123
- **HOD**: hod@school.edu / hod123
- **Coordinator**: coord@school.edu / coord123
- **Student**: Check student info CSV

---

## 📞 Important Notes

- **Database**: PostgreSQL must be installed and running before starting backend
- **Port**: Backend runs on port 5000 by default (configurable)
- **Sessions**: Clear browser cache if experiencing login issues
- **CORS**: Backend should allow frontend requests
- **Deployment**: Test all API endpoints before deploying to production

---

## 🔄 Making Changes to This Project

### To Update This Guide:
1. Open this file: `PROJECT_GUIDE.md`
2. Update relevant sections
3. Save and commit to version control
4. Notify team members of changes

### Common Updates:
- **New endpoint added?** → Update "API Endpoints" section
- **New user role?** → Update "User Roles" section
- **Database schema changed?** → Update "Database Schema" section
- **New file added?** → Update "Project Structure" section
- **Setup instructions changed?** → Update "Getting Started" section

---

## 🚨 Emergency Contacts & Resources

- **Project Location**: `c:\Users\Admin\Downloads\project\web1`
- **Backend**: `backend/app.py` - Main application
- **Database Guide**: `keep/README_POSTGRESQL.md`
- **Quick Help**: `keep/QUICK_COMMANDS.md`

---

## 📌 Next Steps

1. Review the project structure
2. Check `keep/LOGIN_CREDENTIALS.md` for test accounts
3. Follow setup in `README_POSTGRESQL.md` if database not set up
4. Run `python app.py` to start backend
5. Open `web/index.html` in browser
6. Login with test credentials
7. Explore each role's functionality

---

**Last Modified**: January 6, 2026  
**Created By**: Development Team  
**Status**: Ready for Reference

*This file serves as the master guide for all project information. Update this file whenever major changes occur.*
