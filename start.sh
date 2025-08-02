#!/bin/bash

# Exit on error
set -e

# Activate virtual environment
source venv/bin/activate

# Start the server
python manage.py runserver 