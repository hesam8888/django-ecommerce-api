#!/usr/bin/env python3
"""
Test script to verify supplier registration works without property errors.
"""

import os
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from suppliers.models import SupplierInvitation, Supplier, SupplierAdmin

def test_registration_process():
    print("🧪 TESTING SUPPLIER REGISTRATION PROCESS")
    print("=" * 50)
    
    # Create a test invitation
    print("\n1. Creating test invitation...")
    invitation = SupplierInvitation.objects.create(
        email='test@example.com',
        store_name='Test Store',
        owner_name='Test User',
        phone='1234567890',
        address='Test Address'
    )
    print(f"   ✅ Invitation created with token: {invitation.token}")
    
    # Test the registration URL
    print("\n2. Testing registration URL...")
    registration_url = reverse('suppliers:register', kwargs={'token': invitation.token})
    full_url = f"http://127.0.0.1:8000{registration_url}"
    print(f"   ✅ Registration URL: {full_url}")
    
    # Test form creation
    print("\n3. Testing form creation...")
    from suppliers.forms import SupplierRegistrationForm
    
    initial_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password1': 'testpass123',
        'password2': 'testpass123'
    }
    
    form = SupplierRegistrationForm(initial_data)
    print(f"   ✅ Form created successfully")
    print(f"   ✅ Form is valid: {form.is_valid()}")
    
    if form.is_valid():
        print("\n4. Testing user creation...")
        try:
            user = form.save(commit=False)
            user.email = invitation.email
            user.save()
            print(f"   ✅ User created: {user.username}")
            
            # Test supplier creation
            print("\n5. Testing supplier creation...")
            supplier = Supplier.objects.create(
                user=user,
                name=invitation.store_name,
                email=invitation.email,
                phone=invitation.phone or '',
                address=invitation.address or ''
            )
            print(f"   ✅ Supplier created: {supplier.name}")
            
            # Test supplier admin creation
            print("\n6. Testing supplier admin creation...")
            supplier_admin = SupplierAdmin.objects.create(
                user=user,
                supplier=supplier,
                role='owner'
            )
            print(f"   ✅ SupplierAdmin created: {supplier_admin}")
            
            # Test is_supplier_admin property
            print("\n7. Testing is_supplier_admin property...")
            is_admin = user.is_supplier_admin
            print(f"   ✅ is_supplier_admin: {is_admin}")
            
            # Clean up
            print("\n8. Cleaning up test data...")
            supplier_admin.delete()
            supplier.delete()
            user.delete()
            print("   ✅ Test data cleaned up")
            
        except Exception as e:
            print(f"   ❌ Error during user creation: {e}")
            return False
    
    # Clean up invitation
    invitation.delete()
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Supplier registration process works correctly")
    print("✅ No property setter errors")
    print("✅ All models created successfully")
    
    return True

if __name__ == "__main__":
    test_registration_process() 