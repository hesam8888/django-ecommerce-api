#!/usr/bin/env python3
"""
Diagnostic script to identify why supplier registration is failing on PythonAnywhere.
Copy this to PythonAnywhere and run it to see what's wrong.
"""

import os
import sys
import django

def diagnose_pythonanywhere():
    print("🔍 DIAGNOSING PYTHONANYWHERE SUPPLIER REGISTRATION ISSUE")
    print("=" * 60)
    
    try:
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
        django.setup()
        print("✅ Django setup successful")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False
    
    try:
        # Test 1: Check if suppliers app is installed
        from django.apps import apps
        if apps.is_installed('suppliers'):
            print("✅ Suppliers app is installed")
        else:
            print("❌ Suppliers app is NOT installed")
            return False
    except Exception as e:
        print(f"❌ Error checking suppliers app: {e}")
        return False
    
    try:
        # Test 2: Check if models can be imported
        from suppliers.models import SupplierInvitation, Supplier, SupplierAdmin
        print("✅ Supplier models can be imported")
    except Exception as e:
        print(f"❌ Error importing supplier models: {e}")
        return False
    
    try:
        # Test 3: Check if views can be imported
        from suppliers.views import register_with_token
        print("✅ Supplier views can be imported")
    except Exception as e:
        print(f"❌ Error importing supplier views: {e}")
        return False
    
    try:
        # Test 4: Check if forms can be imported
        from suppliers.forms import SupplierRegistrationForm
        print("✅ Supplier forms can be imported")
    except Exception as e:
        print(f"❌ Error importing supplier forms: {e}")
        return False
    
    try:
        # Test 5: Check URL patterns
        from django.urls import reverse
        url = reverse('suppliers:register', kwargs={'token': 'test'})
        print(f"✅ URL pattern works: {url}")
    except Exception as e:
        print(f"❌ Error with URL pattern: {e}")
        return False
    
    try:
        # Test 6: Check if invitation exists
        invitation = SupplierInvitation.objects.get(token='zSKb4Sj13ErYj7PFMmcCjmzVSyuxexZc')
        print(f"✅ Invitation found: {invitation.email}")
        print(f"   Status: {invitation.status}")
        print(f"   Is valid: {invitation.is_valid()}")
    except SupplierInvitation.DoesNotExist:
        print("❌ Invitation not found in database")
        return False
    except Exception as e:
        print(f"❌ Error checking invitation: {e}")
        return False
    
    print("\n🎉 ALL DIAGNOSTICS PASSED!")
    print("The issue might be with the web server configuration.")
    return True

if __name__ == "__main__":
    success = diagnose_pythonanywhere()
    if not success:
        print("\n❌ DIAGNOSTICS FAILED - Check the specific error above")
        sys.exit(1) 