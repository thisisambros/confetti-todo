#!/bin/bash

# Confetti Todo Run Script

set -e

echo "🎉 Starting Confetti Todo..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if todos.md exists
if [ ! -f "todos.md" ]; then
    echo "📝 Creating todos.md..."
    cat > todos.md << 'EOF'
# today

# ideas

# backlog
EOF
fi

# Kill any existing server on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "🔄 Stopping existing server on port 8000..."
    kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null || true
    sleep 1
fi

# Start the server
echo "🚀 Starting server on http://localhost:8000"
echo "📋 Press Ctrl+C to stop"
echo ""

# Open browser after a short delay
(sleep 2 && python3 -m webbrowser http://localhost:8000) &

# Run the server
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload