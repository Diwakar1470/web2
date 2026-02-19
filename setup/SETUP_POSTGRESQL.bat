@echo off
REM Setup script for MySQL database

echo ========================================
echo MySQL Database Setup
echo ========================================
echo.

echo Step 1: Installing Python dependencies...
pip install -r backend\requirements.txt
echo.

echo Step 2: Creating database...
python backend\create_db.py
echo.

echo Step 3: Starting backend server...
echo Backend will run at http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo.
python backend\app.py
