# Backend Setup & Database Verification Report

Generated: December 24, 2025

## File Structure

```
backend/
├── app.py                 # Flask application with SQLAlchemy ORM
├── create_db.py          # Database initialization script
├── requirements.txt      # Python dependencies
├── README.md             # Documentation
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── storage/
│   └── studentProfiles.json  # Legacy JSON data (can be imported)
├── admin-auth.html       # Legacy HTML files
├── coordinator-choice.html
└── hod-panel.html
```

## Database Configuration

### ✅ FIXED Issues:

1. **Requirements Updated**
   - Added: `Flask-SQLAlchemy==3.1.1`
   - Added: `SQLAlchemy==2.0.23`
   - Added: `psycopg2-binary==2.9.9`
   - Added: `python-dotenv==1.0.0`

2. **Environment Variables**
   - Created: `.env.example` with all configuration options
   - Updated: `create_db.py` to use environment variables
   - Updated: `app.py` to load from `.env`

3. **Security**
   - Created: `.gitignore` to protect `.env` credentials
   - Separated: Hardcoded values → Environment variables

### Database Connection String

```
postgresql://postgres:1234@localhost:5432/school_db
```

(Configurable via `.env` file)

## Setup Steps (When Ready)

1. Create `.env` file:
   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

2. Ensure PostgreSQL is running on localhost:5432

3. Create database:
   ```powershell
   python backend/create_db.py
   ```

4. Install dependencies:
   ```powershell
   pip install -r backend/requirements.txt
   ```

5. Run Flask server:
   ```powershell
   python backend/app.py
   ```

## Database Tables

### students
- Stores student profiles with lookup_key (rollNo or email)
- Auto-update timestamp tracking
- JSON profile data storage

### registrations
- Stores course registration submissions
- Automatic timestamp on creation
- Flexible JSON data format

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Check system status |
| GET | `/api/student-profiles` | List all students |
| POST | `/api/student-profiles/import` | Import student batch |
| GET | `/api/registrations` | List all registrations |
| POST | `/api/registrations` | Create new registration |

## Key Features

✅ PostgreSQL database with SQLAlchemy ORM
✅ Auto-migration of tables on startup
✅ Environment variable configuration
✅ CORS enabled for frontend access
✅ Proper error handling with helpful messages
✅ Security: No hardcoded credentials
✅ Git-safe: Credentials excluded from version control

## Migration from JSON Files

If you have existing data in `backend/storage/studentProfiles.json`:

1. Format it as: `{"students": [...]}`
2. POST to `/api/student-profiles/import`
3. Data will be migrated to PostgreSQL

Example:
```powershell
$json = Get-Content backend/storage/studentProfiles.json | ConvertFrom-Json
$body = @{students = $json} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:5000/api/student-profiles/import -Method POST -Body $body -ContentType application/json
```
