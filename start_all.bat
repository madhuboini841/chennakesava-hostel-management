@echo off
start "Frontend" cmd /k "cd /d "%~dp0hostel-food-system\frontend" && npm run dev"
start "Backend" cmd /k "cd /d "%~dp0hostel-food-system\backend" && node server.js"
start "FlaskApp" cmd /k "cd /d "%~dp0hostel_mgmt\hostel_mgmt" && "..\..\venv\Scripts\python.exe" app.py"
