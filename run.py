#!/usr/bin/env python3
"""Moscow Metro Pathfinder runner."""

import importlib.util
import subprocess
import sys


def main():
    has_fastapi_stack = importlib.util.find_spec("fastapi") and importlib.util.find_spec("uvicorn")
    command = (
        [
            sys.executable,
            "-m",
            "uvicorn",
            "server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "5000",
            "--reload",
        ]
        if has_fastapi_stack
        else [sys.executable, "web/app.py"]
    )

    print("Moscow Metro Pathfinder")
    print("=" * 50)
    print("Web app: http://127.0.0.1:5000")
    if has_fastapi_stack:
        print("API docs: http://127.0.0.1:5000/docs")
    print("Data source: data/processed/outputs")
    if not has_fastapi_stack:
        print("FastAPI/uvicorn not found, running Flask fallback.")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    subprocess.run(command, check=False)


if __name__ == "__main__":
    main()
