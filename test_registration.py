#!/usr/bin/env python3
"""
Test script to verify supplier registration is working after deployment.
Run this on PythonAnywhere after uploading the updated files.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from django.urls import reverse
from suppliers.models import SupplierInvitation
from suppliers.views import register_with_token
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

def test_registration():
    print("🧪 TESTING SUPPLIER REGISTRATION")
    print("=" * 40)
    
    # Test 1: Check if invitation exists
    try:
        invitation = SupplierInvitation.objects.get(token='zSKb4Sj13ErYj7PFMmcCjmzVSyuxexZc')
        print(f"✅ Invitation found for: {invitation.email}")
        print(f"   Status: {invitation.status}")
        print(f"   Is used: {invitation.is_used}")
        print(f"   Is valid: {invitation.is_valid()}")
    except SupplierInvitation.DoesNotExist:
        print("❌ Invitation not found!")
        return False
    
    # Test 2: Check URL generation
    try:
        url = reverse('suppliers:register', kwargs={'token': invitation.token})
        print(f"✅ URL generated: {url}")
    except Exception as e:
        print(f"❌ URL generation failed: {e}")
        return False
    
    # Test 3: Test the view function
    try:
        rf = RequestFactory()
        request = rf.get(url)
        request.user = AnonymousUser()
        response = register_with_token(request, invitation.token)
        print(f"✅ View function works: Status {response.status_code}")
    except Exception as e:
        print(f"❌ View function failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("The registration should now work on PythonAnywhere.")
    return True

if __name__ == "__main__":
    success = test_registration()
    if not success:
        print("\n❌ TESTS FAILED - Check the deployment!")
        sys.exit(1) 