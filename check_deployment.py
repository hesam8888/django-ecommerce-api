#!/usr/bin/env python3
"""
Deployment checker for supplier invitation system.
Run this to verify what needs to be deployed to PythonAnywhere.
"""

import os
import hashlib

def get_file_hash(filepath):
    """Get MD5 hash of a file"""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def check_deployment():
    print("🔍 DEPLOYMENT CHECKER - SUPPLIER INVITATION SYSTEM")
    print("=" * 60)
    
    # Critical files that must be deployed
    critical_files = [
        "suppliers/models.py",
        "suppliers/admin.py", 
        "suppliers/views.py",
        "suppliers/forms.py",
        "suppliers/urls.py",
        "suppliers/templates/suppliers/register.html",
        "suppliers/templates/suppliers/base.html",
        "suppliers/templates/suppliers/register_success.html",
        "suppliers/management/commands/create_invitation.py",
        "suppliers/migrations/0009_remove_old_invitation.py",
        "myshop/urls.py",
        "myshop/settings.py"
    ]
    
    print("\n📁 CRITICAL FILES TO UPLOAD:")
    print("-" * 40)
    
    all_files_exist = True
    for filepath in critical_files:
        if os.path.exists(filepath):
            file_hash = get_file_hash(filepath)
            print(f"✅ {filepath}")
            print(f"   Hash: {file_hash[:8]}...")
        else:
            print(f"❌ {filepath} (MISSING)")
            all_files_exist = False
    
    print(f"\n📊 SUMMARY:")
    print(f"   Files found: {sum(1 for f in critical_files if os.path.exists(f))}/{len(critical_files)}")
    
    if all_files_exist:
        print("✅ All critical files are ready for deployment!")
    else:
        print("❌ Some files are missing. Please check the list above.")
    
    print("\n🚀 DEPLOYMENT PRIORITY:")
    print("1. suppliers/models.py (MOST IMPORTANT)")
    print("2. suppliers/admin.py (CRITICAL)")
    print("3. suppliers/views.py (CRITICAL)")
    print("4. suppliers/migrations/0009_remove_old_invitation.py (NEW)")
    print("5. suppliers/management/commands/create_invitation.py (NEW)")
    print("6. All other files")
    
    print("\n📧 EMAIL SETTINGS CHECK:")
    print("-" * 30)
    
    # Check email settings
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
        django.setup()
        
        from django.conf import settings
        
        email_settings = [
            ('DEFAULT_FROM_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', None)),
            ('EMAIL_HOST', getattr(settings, 'EMAIL_HOST', None)),
            ('EMAIL_PORT', getattr(settings, 'EMAIL_PORT', None)),
            ('EMAIL_USE_TLS', getattr(settings, 'EMAIL_USE_TLS', None)),
            ('SITE_URL', getattr(settings, 'SITE_URL', None)),
        ]
        
        for setting, value in email_settings:
            if value:
                print(f"✅ {setting}: {value}")
            else:
                print(f"⚠️  {setting}: Not set")
                
    except Exception as e:
        print(f"❌ Error checking email settings: {e}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Upload all critical files to PythonAnywhere")
    print("2. Run: python manage.py migrate")
    print("3. Test: python manage.py create_invitation test@example.com 'Test Store' 'Test User'")
    print("4. Restart your web app")
    print("5. Test the registration URL")

if __name__ == "__main__":
    check_deployment() 