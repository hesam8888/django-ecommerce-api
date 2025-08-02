#!/bin/bash

echo "🚀 Starting Django Development Server"
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check dependencies first
echo "🔍 Checking dependencies..."
python check_dependencies.py

# If dependency check fails, exit
if [ $? -ne 0 ]; then
    echo "❌ Dependency check failed. Please fix the issues above."
    exit 1
fi

# Run migrations if needed
echo "🔄 Checking for pending migrations..."
python manage.py migrate --check --dry-run > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📝 Running migrations..."
    python manage.py migrate
fi

# Start the development server
echo "🌐 Starting Django development server..."
echo "Server will be available at: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver 