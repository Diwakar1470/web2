# School Course Registration System

A comprehensive web-based course registration system for schools with role-based access control (Admin, HOD, Coordinator, Students).

## 📋 Project Structure

```
.
├── backend/                    # Flask API server
│   ├── app.py                 # Main Flask application
│   ├── requirements.txt       # Python dependencies
│   └── [database and utility scripts]
├── web/                        # Frontend HTML/CSS/JS files
│   ├── index.html             # Student dashboard
│   ├── admin-auth.html        # Admin login
│   ├── hod-panel.html         # HOD management panel
│   └── [other pages]
├── file/                       # Sample data (CSVs)
├── keep/                       # Important guides and setup files
│   ├── README_POSTGRESQL.md   # Database setup guide
│   ├── QUICK_COMMANDS.md      # Useful commands
│   ├── VERIFICATION_GUIDE.md  # System verification
│   └── [other documentation]
└── .gitignore                  # Git ignore rules

```

## 🚀 Quick Start

### 1. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database Setup
Ensure PostgreSQL is installed and running, then follow the guide in `keep/README_POSTGRESQL.md`

### 3. Start Backend Server
```powershell
python app.py
```

The backend will run on `http://localhost:5000`

### 4. Open Frontend
Open `web/index.html` in your browser

## 📚 Documentation

- **[README_POSTGRESQL.md](keep/README_POSTGRESQL.md)** - Database setup and configuration
- **[QUICK_COMMANDS.md](keep/QUICK_COMMANDS.md)** - Frequently used commands
- **[VERIFICATION_GUIDE.md](keep/VERIFICATION_GUIDE.md)** - System verification steps
- **[DEPARTMENT_SETUP_GUIDE.md](keep/DEPARTMENT_SETUP_GUIDE.md)** - Department and class configuration
- **[LOGIN_CREDENTIALS.md](keep/LOGIN_CREDENTIALS.md)** - Test user credentials

## 👥 User Roles

- **Admin**: System administration and user management
- **HOD**: Department-level management and approvals
- **Coordinator**: Student coordination and registration
- **Students**: Course registration and tracking

## 🔧 Technology Stack

- **Backend**: Python Flask with PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: PostgreSQL 12+
- **Python**: 3.8+

## 📝 Getting Help

1. Check the guides in the `keep/` folder
2. Review `QUICK_COMMANDS.md` for common issues
3. Run `SYSTEM_VERIFICATION.py` in backend to check system health

## 📅 Last Updated
January 2026

---

For detailed setup instructions, see [keep/README_POSTGRESQL.md](keep/README_POSTGRESQL.md)
