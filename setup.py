#!/usr/bin/env python3
"""
Cross-platform setup script for Confetti Todo
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(message, emoji=""):
    """Print a formatted header message"""
    print(f"\n{emoji} {message}")
    if not emoji:
        print("-" * len(message))

def check_python_version():
    """Check if Python version is 3.9 or higher"""
    print_header("Checking Python version...", "📌")
    version = sys.version_info
    if version < (3, 9):
        print(f"❌ Error: Python 3.9 or higher is required (found {version.major}.{version.minor})")
        print("Please install Python 3.9+ from https://www.python.org/")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} found")

def create_virtual_environment():
    """Create a virtual environment"""
    print_header("Creating virtual environment...", "📦")
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("   Virtual environment already exists")
    else:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    
    return venv_path

def get_pip_command(venv_path):
    """Get the pip command for the virtual environment"""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "pip.exe")
    else:
        return str(venv_path / "bin" / "pip")

def get_python_command(venv_path):
    """Get the python command for the virtual environment"""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "python.exe")
    else:
        return str(venv_path / "bin" / "python")

def install_dependencies(venv_path, dev=False):
    """Install project dependencies"""
    pip_cmd = get_pip_command(venv_path)
    
    # Upgrade pip
    print_header("Upgrading pip...", "📦")
    subprocess.run([pip_cmd, "install", "--upgrade", "pip", "--quiet"], check=True)
    print("✅ Pip upgraded")
    
    # Install main dependencies
    print_header("Installing dependencies...", "📦")
    subprocess.run([pip_cmd, "install", "-r", "requirements.txt", "--quiet"], check=True)
    print("✅ Dependencies installed")
    
    # Install dev dependencies if requested
    if dev:
        print_header("Installing development dependencies...", "📦")
        subprocess.run([pip_cmd, "install", "-r", "requirements-dev.txt", "--quiet"], check=True)
        print("✅ Development dependencies installed")
        
        # Install playwright browsers
        print_header("Installing Playwright browsers...", "🌐")
        python_cmd = get_python_command(venv_path)
        subprocess.run([python_cmd, "-m", "playwright", "install", "chromium"], check=True)
        print("✅ Playwright browsers installed")

def create_sample_todos():
    """Create a sample todos.md file"""
    todos_path = Path("todos.md")
    
    if not todos_path.exists():
        print_header("Creating sample todos.md...", "📝")
        todos_content = """# today
- [ ] Welcome to Confetti Todo! @admin !5m %1
- [ ] Try adding a new task with N @admin !5m %1
- [ ] Complete this task for confetti! @admin !5m %1
  - [ ] Click the checkbox
  - [ ] Enjoy the celebration

# ideas
- [ ] ? Explore all the keyboard shortcuts
- [ ] ? Customize categories for your workflow

# backlog
- [ ] Read the documentation @admin !30m %1
"""
        todos_path.write_text(todos_content)
        print("✅ Sample todos.md created")

def create_directories():
    """Create necessary directories"""
    dirs_to_create = ["backups", "tests"]
    
    for dir_name in dirs_to_create:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✅ {dir_name}/ directory created")

def organize_test_files():
    """Move test files to tests directory"""
    test_files = ["test_server.py", "test_frontend.html", "test_e2e.py", "test_summary.py"]
    tests_dir = Path("tests")
    
    for test_file in test_files:
        src = Path(test_file)
        if src.exists():
            dst = tests_dir / test_file
            if not dst.exists():
                src.rename(dst)
                print(f"✅ Moved {test_file} to tests/")

def make_scripts_executable():
    """Make shell scripts executable on Unix-like systems"""
    if platform.system() != "Windows":
        scripts = ["setup.sh", "run.sh", "test.sh"]
        for script in scripts:
            if Path(script).exists():
                os.chmod(script, 0o755)

def print_completion_message(venv_path):
    """Print setup completion message"""
    print_header("Setup complete!", "🎉")
    
    if platform.system() == "Windows":
        activate_cmd = f"venv\\Scripts\\activate"
        run_cmd = "python run.py"
        test_cmd = "python test.py"
    else:
        activate_cmd = "source venv/bin/activate"
        run_cmd = "./run.sh"
        test_cmd = "./test.sh"
    
    print("\nTo activate the virtual environment:")
    print(f"  {activate_cmd}")
    print("\nTo start the app:")
    print(f"  {run_cmd}")
    print("\nTo run tests:")
    print(f"  {test_cmd}")
    print("\nHappy task managing! 🚀")

def main():
    """Main setup function"""
    print_header("Setting up Confetti Todo...", "🎉")
    
    # Parse arguments
    dev_mode = "--dev" in sys.argv
    
    # Run setup steps
    check_python_version()
    venv_path = create_virtual_environment()
    install_dependencies(venv_path, dev=dev_mode)
    create_sample_todos()
    create_directories()
    organize_test_files()
    make_scripts_executable()
    print_completion_message(venv_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)