#!/bin/bash

# Confetti Todo Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "🎉 Setting up Confetti Todo..."
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.9 or higher is required (found $python_version)"
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi
echo "✅ Python $python_version found"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists"
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"

# Install dev dependencies if requested
if [ "$1" == "--dev" ]; then
    echo ""
    echo "📦 Installing development dependencies..."
    pip install -r requirements-dev.txt --quiet
    echo "✅ Development dependencies installed"
    
    # Install playwright browsers
    echo ""
    echo "🌐 Installing Playwright browsers..."
    playwright install chromium --quiet
    echo "✅ Playwright browsers installed"
fi

# Create sample todos.md if it doesn't exist
if [ ! -f "todos.md" ]; then
    echo ""
    echo "📝 Creating sample todos.md..."
    cat > todos.md << 'EOF'
# today
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
EOF
    echo "✅ Sample todos.md created"
fi

# Create backups directory
if [ ! -d "backups" ]; then
    mkdir -p backups
    echo "✅ Backups directory created"
fi

# Make scripts executable
chmod +x run.sh test.sh 2>/dev/null || true

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the app, run:"
echo "  ./run.sh"
echo ""
echo "To run tests, use:"
echo "  ./test.sh"
echo ""
echo "Happy task managing! 🚀"