#!/bin/bash
# Moscow Metro Pathfinder - Shell Script Runner
# Starts both backend and frontend servers

echo "🗺️ Moscow Metro Pathfinder"
echo "=================================================="
echo "Starting both backend and frontend servers..."
echo "Backend (FastAPI): http://localhost:8000"
echo "Frontend (Flask): http://localhost:5000"
echo "Press Ctrl+C to stop both servers"
echo "=================================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill 0
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start backend in background
echo "🚀 Starting FastAPI backend..."
uvicorn api:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🌐 Starting Flask frontend..."
python web/app.py &
FRONTEND_PID=$!

# Wait for both processes
wait