#!/bin/bash

# Confetti Todo Test Runner

set -e

echo "🧪 Running Confetti Todo Tests..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh --dev first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if test dependencies are installed
if ! pip show pytest >/dev/null 2>&1; then
    echo "📦 Installing test dependencies..."
    pip install -r requirements-dev.txt --quiet
fi

# Move test files to tests directory if needed
mkdir -p tests
for file in test_*.py test_*.html; do
    if [ -f "$file" ]; then
        mv "$file" tests/ 2>/dev/null || true
    fi
done

echo "🔧 Running backend tests..."
echo "=============================="
pytest tests/test_server.py -v --cov=server --cov-report=term-missing

echo ""
echo "📊 Backend test coverage:"
echo "=============================="
coverage report -m server.py

echo ""
echo "🌐 Frontend tests:"
echo "=============================="
echo "Open tests/test_frontend.html in your browser to run frontend tests"
echo "File: file://$(pwd)/tests/test_frontend.html"

echo ""
echo "🎭 E2E tests:"
echo "=============================="
echo "To run E2E tests, ensure the server is running and execute:"
echo "  pytest tests/test_e2e.py -v"

echo ""
echo "✅ Test suite complete!"