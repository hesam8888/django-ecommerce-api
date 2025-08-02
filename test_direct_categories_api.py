#!/usr/bin/env python3
"""
Test script for the new direct categories API
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from shop.models import Category

def test_direct_categories_api():
    """Test the new direct categories API"""
    
    print("🔍 TESTING DIRECT CATEGORIES API")
    print("=" * 50)
    
    # Test the API endpoint
    try:
        response = requests.get('http://127.0.0.1:8000/shop/api/categories/direct/')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            print(f"\n📊 Summary:")
            print(f"• Total direct categories: {data.get('count', 0)}")
            print(f"• Success: {data.get('success', False)}")
            
            # Show each direct category
            print(f"\n📋 Direct Categories:")
            for category in data.get('categories', []):
                print(f"• {category['name']} (ID: {category['id']})")
                print(f"  - Product count: {category['product_count']}")
                print(f"  - Parent: {category['parent_name'] or 'None'}")
                print(f"  - Type: {category['category_type']}")
                print()
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_all_categories_for_comparison():
    """Show all categories and their container status for comparison"""
    
    print("\n\n🔍 ALL CATEGORIES COMPARISON")
    print("=" * 50)
    
    categories = Category.objects.filter(is_visible=True).order_by('name')
    
    print("All categories and their container status:")
    for category in categories:
        is_container = category.is_container_category()
        product_count = category.get_product_count()
        effective_type = category.get_effective_category_type()
        
        status = "📁 CONTAINER" if is_container else "📄 DIRECT"
        print(f"{status} | {category.name} (ID: {category.id})")
        print(f"     Products: {product_count} | Type: {effective_type}")
        if category.parent:
            print(f"     Parent: {category.parent.name}")
        print()

if __name__ == "__main__":
    show_all_categories_for_comparison()
    test_direct_categories_api() 