# Flask Backend

Python Flask backend with PostgreSQL database for the course registration system.

## Prerequisites

- **Python 3.8+**
- **PostgreSQL 12+** (must be installed and running)

### Check PostgreSQL Installation

```powershell
# Windows - Check if PostgreSQL is installed
psql --version

# Start PostgreSQL service (Windows)
# Go to: Services > PostgreSQL > Start
# Or use: net start postgresql-x64-15 (replace 15 with your version)
```

## Setup

### 1. Create Environment File

Copy `.env.example` to `.env` and update credentials:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:
```
DB_USER=postgres
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
DB_NAME=school_db
FLASK_ENV=development
PORT=5000
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create Database

```powershell
python create_db.py
```

Expected output:
```
✅ Database 'school_db' created successfully!
```

### 5. Run Flask Server

```powershell
python app.py
```

Server runs on `http://localhost:5000` by default.

## Database Structure

### Tables

#### `students`
- `id` (Integer, Primary Key)
- `lookup_key` (String, Unique) - For identifying by rollNo or email
- `profile` (JSON) - Stores student profile data
- `created_at` (DateTime)
- `updated_at` (DateTime)

#### `registrations`
- `id` (Integer, Primary Key)
- `data` (JSON) - Stores registration data
- `timestamp` (DateTime)

## API Endpoints

### Health Check
- `GET /api/health` — Check server and database connection status

### Student Profiles
- `GET /api/student-profiles` — Get all student profiles
- `POST /api/student-profiles/import` — Import/update student profiles
  ```json
  {
    "students": [
      {"rollNo": "2024001", "name": "John Doe", "email": "john@example.com"},
      ...
    ]
  }
  ```

### Registrations
- `GET /api/registrations` — Get all registrations
- `POST /api/registrations` — Create new registration
  ```json
  {
    "studentName": "John Doe",
    "studentEmail": "john@example.com",
    "status": "pending"
  }
  ```

## Troubleshooting

### "Connection refused" Error
**Problem:** PostgreSQL is not running
**Solution:** Start PostgreSQL service
```powershell
# Windows Services
net start postgresql-x64-15
```

### "Database does not exist" Error
**Problem:** Database wasn't created
**Solution:** Run the create_db.py script
```powershell
python create_db.py
```

### "ModuleNotFoundError: No module named 'flask_sqlalchemy'"
**Problem:** Dependencies not installed
**Solution:** Install requirements again
```powershell
pip install -r requirements.txt
```

## Development Notes

- Tables are auto-created on app startup if they don't exist
- Use `.env` for local development (already in `.gitignore`)
- CORS is enabled for all `/api/*` endpoints during development
- Database URI: `postgresql://user:password@host:port/dbname`

## Data Storage

- Data is persisted in PostgreSQL (not JSON files)
- Previous JSON data in `storage/` folder can be imported via the `/api/student-profiles/import` endpoint

