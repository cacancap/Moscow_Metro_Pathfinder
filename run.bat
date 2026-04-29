@echo off
REM Moscow Metro Pathfinder - Windows Batch Runner
REM Starts both backend and frontend servers

echo 🗺️ Moscow Metro Pathfinder
echo ==================================================
echo Starting both backend and frontend servers...
echo Backend (FastAPI): http://localhost:8000
echo Frontend (Flask): http://localhost:5000
echo Press Ctrl+C to stop both servers
echo ==================================================

REM Start backend in background
start "FastAPI Backend" cmd /c "uvicorn api:app --host 127.0.0.1 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
python web/app.py

pause