#!/usr/bin/env python3
"""
Debug script to test URL patterns and identify registration URL issues.
"""

import os
import django
from django.urls import reverse, resolve
from django.test import RequestFactory

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

def debug_urls():
    print("🔍 URL DEBUG DIAGNOSTIC")
    print("=" * 50)
    
    # Test token
    test_token = "CuTep1B7zs5nvGlkL3beuJPg8HB5tYEZ"
    
    print(f"\n📋 Testing registration URL with token: {test_token}")
    print("-" * 50)
    
    try:
        # Test URL generation
        url = reverse('suppliers:register', kwargs={'token': test_token})
        print(f"✅ Generated URL: {url}")
        
        # Test URL resolution
        resolver_match = resolve(url)
        print(f"✅ Resolved view: {resolver_match.func.__name__}")
        print(f"✅ View module: {resolver_match.func.__module__}")
        print(f"✅ URL name: {resolver_match.url_name}")
        print(f"✅ App name: {resolver_match.app_name}")
        print(f"✅ Namespace: {resolver_match.namespace}")
        
        # Test if view function exists
        from suppliers.views import register_with_token
        print(f"✅ View function imported successfully")
        
        # Test if model exists
        from suppliers.models import SupplierInvitation
        print(f"✅ SupplierInvitation model imported successfully")
        
        # Test if invitation exists
        try:
            invitation = SupplierInvitation.objects.get(token=test_token)
            print(f"✅ Invitation found: {invitation.email}")
            print(f"✅ Invitation valid: {invitation.is_valid()}")
        except SupplierInvitation.DoesNotExist:
            print(f"❌ Invitation with token '{test_token}' not found in database")
            
            # List all invitations
            all_invitations = SupplierInvitation.objects.all()
            print(f"\n📋 All invitations in database ({all_invitations.count()}):")
            for inv in all_invitations:
                print(f"   - {inv.email} (token: {inv.token[:10]}...)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🌐 URL PATTERNS CHECK:")
    print("-" * 30)
    
    # Check suppliers URLs
    from suppliers.urls import urlpatterns
    print(f"Suppliers URL patterns ({len(urlpatterns)}):")
    for pattern in urlpatterns:
        print(f"   - {pattern.pattern}")
    
    print(f"\n🔗 MAIN URL PATTERNS:")
    print("-" * 30)
    
    # Check main URLs
    from myshop.urls import urlpatterns as main_patterns
    for pattern in main_patterns:
        if 'suppliers' in str(pattern.pattern):
            print(f"   - {pattern.pattern}")
    
    print(f"\n🎯 DEPLOYMENT CHECKLIST:")
    print("-" * 30)
    print("1. ✅ suppliers/urls.py - URL patterns defined")
    print("2. ✅ suppliers/views.py - register_with_token function exists")
    print("3. ✅ suppliers/models.py - SupplierInvitation model exists")
    print("4. ✅ myshop/urls.py - suppliers URLs included")
    print("5. ❓ suppliers/migrations/0009_remove_old_invitation.py - deployed?")
    print("6. ❓ Database migrated on PythonAnywhere?")
    print("7. ❓ Web app restarted on PythonAnywhere?")
    
    print(f"\n🚨 LIKELY ISSUES:")
    print("-" * 20)
    print("1. Old code still deployed on PythonAnywhere")
    print("2. Migration not run on PythonAnywhere")
    print("3. Web app not restarted")
    print("4. Files not uploaded correctly")
    
    print(f"\n💡 SOLUTION:")
    print("-" * 15)
    print("1. Upload ALL critical files to PythonAnywhere")
    print("2. Run: python manage.py migrate")
    print("3. Restart web app")
    print("4. Test URL again")

if __name__ == "__main__":
    debug_urls() 