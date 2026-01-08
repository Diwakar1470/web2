@echo off
set FLASK_ENV=development
set FLASK_DEBUG=0
echo Starting Flask Backend (Safe Mode - No Socket Error)...
echo.
cd ..
".venv\Scripts\python.exe" backend\app.py
pause
