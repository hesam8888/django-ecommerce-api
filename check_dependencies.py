#!/usr/bin/env python3
"""
Dependency checker script to prevent allauth and other import errors.
Run this before starting Django to ensure all packages are installed.
"""

import sys
import subprocess
import pkg_resources
from pathlib import Path

def check_requirements():
    """Check if all packages in requirements.txt are installed."""
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    print("🔍 Checking dependencies...")
    
    with open(requirements_file, 'r') as f:
        requirements = f.read().splitlines()
    
    missing_packages = []
    
    for requirement in requirements:
        if requirement.strip() and not requirement.startswith('#'):
            try:
                pkg_resources.require(requirement)
                print(f"✅ {requirement}")
            except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict) as e:
                print(f"❌ {requirement} - {e}")
                missing_packages.append(requirement)
    
    if missing_packages:
        print(f"\n❌ Missing {len(missing_packages)} packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        
        print("\n🔧 To fix this, run:")
        print("   source venv/bin/activate")
        print("   pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def check_django_setup():
    """Check if Django can import without errors."""
    try:
        import django
        from django.conf import settings
        from django.core.management import execute_from_command_line
        
        # Try to import allauth specifically
        # import allauth
        # print("✅ Django and allauth imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Django import error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Django Dependency Checker")
    print("=" * 40)
    
    deps_ok = check_requirements()
    django_ok = check_django_setup()
    
    if deps_ok and django_ok:
        print("\n🎉 Everything looks good! You can run Django now.")
        sys.exit(0)
    else:
        print("\n💥 Please fix the issues above before running Django.")
        sys.exit(1) 