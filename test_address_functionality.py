#!/usr/bin/env python
"""
Test script to verify address functionality works correctly.
Run this from the myshop2/myshop directory:
python test_address_functionality.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from accounts.models import Customer, Address
from django.urls import reverse

def test_address_creation_with_label():
    """Test that addresses can be created with labels"""
    print("🧪 Testing address creation with label...")
    
    # Create test user
    User = get_user_model()
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    
    # Create customer
    customer = Customer.objects.create(
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Create address with label
    address = Address.objects.create(
        customer=customer,
        label='Home',
        receiver_name='Test User',
        street_address='123 Test Street',
        city='Test City',
        province='Test Province',
        country='Iran',
        phone='09123456789'
    )
    
    print(f"✅ Address created successfully!")
    print(f"   ID: {address.id}")
    print(f"   Label: '{address.label}'")
    print(f"   Receiver: {address.receiver_name}")
    print(f"   Address: {address.street_address}")
    print(f"   Full: {address.full_address}")
    
    # Verify label is saved
    saved_address = Address.objects.get(id=address.id)
    assert saved_address.label == 'Home', f"Expected 'Home', got '{saved_address.label}'"
    print("✅ Label verification passed!")
    
    # Clean up
    address.delete()
    customer.delete()
    user.delete()
    print("🧹 Cleanup completed")

def test_profile_view_access():
    """Test that profile view is accessible"""
    print("\n🧪 Testing profile view access...")
    
    # Create test user
    User = get_user_model()
    user = User.objects.create_user(
        email='profile_test@example.com',
        password='testpass123'
    )
    
    client = Client()
    
    # Test without login (should redirect)
    response = client.get('/accounts/profile/')
    print(f"Without login: Status {response.status_code} (should be 302 redirect)")
    
    # Test with login
    client.login(email='profile_test@example.com', password='testpass123')
    response = client.get('/accounts/profile/')
    print(f"With login: Status {response.status_code} (should be 200)")
    
    if response.status_code == 200:
        print("✅ Profile view accessible!")
        # Check if form elements exist
        content = response.content.decode()
        if 'name="label"' in content:
            print("✅ Label field found in form")
        else:
            print("❌ Label field NOT found in form")
    else:
        print(f"❌ Profile view not accessible: {response.status_code}")
    
    # Clean up
    user.delete()
    print("🧹 Cleanup completed")

if __name__ == '__main__':
    print("🚀 Starting address functionality tests...\n")
    
    try:
        test_address_creation_with_label()
        test_profile_view_access()
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc() 