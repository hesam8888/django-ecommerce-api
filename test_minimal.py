#!/usr/bin/env python3
"""
Minimal test to check if Django can start
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')

try:
    # Setup Django
    django.setup()
    print("✅ Django setup successful!")
    
    # Test basic imports
    from django.http import JsonResponse
    from django.conf import settings
    print("✅ Basic Django imports successful!")
    
    # Test settings
    print(f"✅ DEBUG: {settings.DEBUG}")
    print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"✅ DATABASES: {settings.DATABASES}")
    
    print("✅ All tests passed! Django can start successfully.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 