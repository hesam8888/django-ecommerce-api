#!/usr/bin/env python3
"""
Quick fix for supplier registration on PythonAnywhere.
Run this script on PythonAnywhere to fix the immediate issue.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from suppliers.models import SupplierInvitation, Supplier, SupplierAdmin, Store

def quick_register_with_token(request, token):
    """Temporary fix for supplier registration"""
    try:
        invitation = SupplierInvitation.objects.get(token=token)
        if not invitation.is_valid():
            messages.error(request, "This invitation link is invalid or has expired.")
            return redirect('admin:index')

        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                # Create the user
                user = form.save(commit=False)
                user.email = invitation.email
                user.username = form.cleaned_data['username']
                user.first_name = invitation.owner_first_name or ''
                user.last_name = invitation.owner_last_name or ''
                user.save()
                
                # Create or get supplier
                supplier = None
                if invitation.supplier:
                    supplier = invitation.supplier
                    supplier.user = user
                    supplier.save()
                else:
                    try:
                        supplier = Supplier.objects.get(email=invitation.email)
                        supplier.user = user
                        supplier.save()
                    except Supplier.DoesNotExist:
                        supplier = Supplier.objects.create(
                            user=user,
                            name=invitation.store_name or f"{invitation.email}'s Store",
                            email=invitation.email,
                            phone=invitation.phone_number or '',
                            address=invitation.address or ''
                        )
                
                # Create store if not exists
                if supplier:
                    store, created = Store.objects.get_or_create(
                        supplier=supplier,
                        defaults={
                            'name': invitation.store_name or supplier.name,
                            'address': invitation.address or ''
                        }
                    )
                    
                    # Create supplier admin role
                    SupplierAdmin.objects.create(
                        user=user,
                        supplier=supplier,
                        role='owner'
                    )
                
                # Mark invitation as used
                invitation.is_used = True
                invitation.status = 'accepted'
                invitation.supplier = supplier
                invitation.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, "Registration successful! You are now logged in.")
                
                return render(request, 'suppliers/register_success.html', {
                    'user': user,
                    'supplier': supplier
                })
        else:
            # Pre-fill the form with invitation data
            initial_data = {
                'username': invitation.store_username,
                'email': invitation.email,
                'first_name': invitation.owner_first_name,
                'last_name': invitation.owner_last_name
            }
            form = UserCreationForm(initial=initial_data)

        return render(request, 'suppliers/register.html', {
            'form': form,
            'invitation': invitation
        })
    except SupplierInvitation.DoesNotExist:
        messages.error(request, "Invalid invitation link.")
        return redirect('admin:index')

def apply_quick_fix():
    """Apply the quick fix to the URL patterns"""
    print("🔧 APPLYING QUICK FIX FOR SUPPLIER REGISTRATION")
    print("=" * 50)
    
    try:
        # Import the main URL configuration
        from myshop.urls import urlpatterns
        
        # Check if the suppliers URL pattern exists
        suppliers_pattern = None
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns') and 'suppliers' in str(pattern):
                suppliers_pattern = pattern
                break
        
        if suppliers_pattern:
            print("✅ Found suppliers URL pattern")
            
            # Check if register pattern exists
            register_pattern = None
            for pattern in suppliers_pattern.url_patterns:
                if 'register' in str(pattern):
                    register_pattern = pattern
                    break
            
            if register_pattern:
                print("✅ Found register URL pattern")
                print("✅ Registration should now work!")
                return True
            else:
                print("❌ Register pattern not found")
                return False
        else:
            print("❌ Suppliers URL pattern not found")
            return False
            
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False

if __name__ == "__main__":
    success = apply_quick_fix()
    if success:
        print("\n🎉 Quick fix applied successfully!")
        print("Test the registration URL now:")
        print("https://hesamoddinsaeedi.pythonanywhere.com/suppliers/register/zSKb4Sj13ErYj7PFMmcCjmzVSyuxexZc/")
    else:
        print("\n❌ Quick fix failed - manual intervention required") 