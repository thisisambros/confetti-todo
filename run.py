#!/usr/bin/env python3
"""
Cross-platform run script for Confetti Todo
"""

import os
import sys
import subprocess
import time
import webbrowser
import platform
from pathlib import Path

def check_venv():
    """Check if virtual environment exists"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("Please run 'python setup.py' first")
        sys.exit(1)
    return venv_path

def create_todos_if_missing():
    """Create todos.md if it doesn't exist"""
    todos_path = Path("todos.md")
    if not todos_path.exists():
        print("📝 Creating todos.md...")
        todos_content = """# today

# ideas

# backlog
"""
        todos_path.write_text(todos_content)

def kill_existing_server():
    """Kill any existing server on port 8000"""
    if platform.system() == "Windows":
        # Windows command to find and kill process on port 8000
        try:
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", ":8000"],
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print("🔄 Stopping existing server on port 8000...")
                # Extract PID and kill
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if "LISTENING" in line:
                        pid = line.split()[-1]
                        subprocess.run(["taskkill", "/F", "/PID", pid], shell=True)
                time.sleep(1)
        except:
            pass
    else:
        # Unix-like command
        try:
            result = subprocess.run(
                ["lsof", "-Pi", ":8000", "-sTCP:LISTEN", "-t"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                print("🔄 Stopping existing server on port 8000...")
                pid = result.stdout.strip()
                subprocess.run(["kill", pid])
                time.sleep(1)
        except:
            pass

def open_browser_delayed():
    """Open browser after a delay"""
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

def get_python_command(venv_path):
    """Get the python command for the virtual environment"""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "python.exe")
    else:
        return str(venv_path / "bin" / "python")

def main():
    """Main run function"""
    print("🎉 Starting Confetti Todo...")
    print("")
    
    # Check virtual environment
    venv_path = check_venv()
    
    # Create todos.md if missing
    create_todos_if_missing()
    
    # Kill existing server
    kill_existing_server()
    
    # Get python command
    python_cmd = get_python_command(venv_path)
    
    print("🚀 Starting server on http://localhost:8000")
    print("📋 Press Ctrl+C to stop")
    print("")
    
    # Start browser opener in background
    import threading
    browser_thread = threading.Thread(target=open_browser_delayed)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run the server
    try:
        subprocess.run([
            python_cmd, "-m", "uvicorn",
            "server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Confetti Todo...")
        sys.exit(0)

if __name__ == "__main__":
    main()