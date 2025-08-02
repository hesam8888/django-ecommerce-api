#!/bin/bash

# Exit on error
set -e

echo "Setting up Django project environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install django-allauth
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

echo "Setup completed successfully!"
echo "To start the server, run: source venv/bin/activate && python manage.py runserver" 