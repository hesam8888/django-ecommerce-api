#!/usr/bin/env bash
# Build script for deployment

echo "Building Django application..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

echo "Build completed successfully!" 