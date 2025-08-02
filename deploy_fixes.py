#!/usr/bin/env python3
"""
Deployment script to identify files that need to be updated on PythonAnywhere
to fix the supplier registration issue.
"""

import os
import shutil
from pathlib import Path

def main():
    print("🔧 SUPPLIER REGISTRATION FIX - DEPLOYMENT GUIDE")
    print("=" * 60)
    
    # Files that need to be updated on PythonAnywhere
    critical_files = [
        "suppliers/views.py",
        "suppliers/forms.py", 
        "suppliers/models.py",
        "suppliers/urls.py",
        "suppliers/admin.py",
        "suppliers/templates/suppliers/register.html",
        "suppliers/templates/suppliers/base.html",
        "suppliers/templates/suppliers/register_success.html",
        "myshop/urls.py",
        "myshop/settings.py"
    ]
    
    print("\n📁 FILES THAT NEED TO BE UPDATED ON PYTHONANYWHERE:")
    print("-" * 50)
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (MISSING)")
    
    print("\n🚀 DEPLOYMENT STEPS:")
    print("-" * 30)
    print("1. Upload these files to your PythonAnywhere server")
    print("2. Run: python manage.py migrate")
    print("3. Restart your web app on PythonAnywhere")
    print("4. Test the registration URL")
    
    print("\n🔍 CRITICAL FIXES IN THIS UPDATE:")
    print("-" * 40)
    print("• Fixed imports in suppliers/views.py")
    print("• Added missing SupplierRegistrationForm import")
    print("• Fixed is_supplier_admin property usage")
    print("• Ensured all URL patterns are properly configured")
    
    print("\n📧 TESTING:")
    print("-" * 15)
    print("After deployment, test this URL:")
    print("https://hesamoddinsaeedi.pythonanywhere.com/suppliers/register/zSKb4Sj13ErYj7PFMmcCjmzVSyuxexZc/")
    
    print("\n⚠️  IMPORTANT:")
    print("-" * 15)
    print("• The current invitation is still valid")
    print("• No need to create a new invitation")
    print("• Just deploy the code and test the existing URL")

if __name__ == "__main__":
    main() 