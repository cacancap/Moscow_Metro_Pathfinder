#!/usr/bin/env python3
"""
Moscow Metro Pathfinder - Combined Backend + Frontend Runner
Starts both FastAPI backend (port 8000) and Flask frontend (port 5000) simultaneously
"""

import subprocess
import sys
import time
import signal
import os

def main():
    """Main function to run both servers"""
    print("🗺️ Moscow Metro Pathfinder")
    print("=" * 50)
    print("Starting both backend and frontend servers...")
    print("Backend (FastAPI): http://localhost:8000")
    print("Frontend (Flask): http://localhost:5000")
    print("Press Ctrl+C to stop both servers")
    print("=" * 50)

    # Start backend server
    print("🚀 Starting FastAPI backend...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn",
        "api:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ])

    # Wait a moment for backend to start
    time.sleep(3)

    # Start frontend server
    print("🌐 Starting Flask frontend...")
    frontend_process = subprocess.Popen([
        sys.executable, "web/app.py"
    ])

    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down servers...")
        try:
            backend_process.terminate()
            frontend_process.terminate()
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
            frontend_process.kill()
        print("✅ Servers stopped")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Wait for both processes
        while True:
            if backend_process.poll() is not None:
                print("❌ Backend server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend server stopped unexpectedly")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()