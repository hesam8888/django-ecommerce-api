#!/usr/bin/env python3
"""
Test script to verify the flexible attribute system is working
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/hesamoddinsaeedi/Desktop/best/backup copy 38/myshop2/myshop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from shop.models import Category, Attribute, SubcategoryAttribute, NewAttributeValue
from django.test import RequestFactory
from shop.views import get_category_attributes
import json

def test_flexible_attributes():
    print("=== Testing Flexible Attribute System ===\n")
    
    # 1. Check if we have clothing categories
    clothing_categories = Category.objects.filter(parent__name='پوشاک')
    print(f"Found {clothing_categories.count()} clothing subcategories:")
    for cat in clothing_categories[:3]:
        print(f"  • {cat.name} (ID: {cat.id})")
    
    if not clothing_categories.exists():
        print("❌ No clothing subcategories found!")
        return
    
    # 2. Test with a specific category
    test_category = clothing_categories.first()
    print(f"\n🧪 Testing with category: {test_category.name} (ID: {test_category.id})")
    
    # 3. Check attributes assigned to this category
    assigned_attrs = SubcategoryAttribute.objects.filter(subcategory=test_category)
    print(f"Assigned attributes: {assigned_attrs.count()}")
    for sa in assigned_attrs:
        print(f"  • {sa.attribute.name} ({sa.attribute.key}) - Required: {sa.is_required}")
    
    # 4. Test the API endpoint
    print(f"\n🌐 Testing API endpoint...")
    factory = RequestFactory()
    request = factory.get(f'/shop/category-attributes/?category_id={test_category.id}')
    
    try:
        response = get_category_attributes(request)
        if response.status_code == 200:
            data = json.loads(response.content)
            print("✅ API Response successful!")
            print(f"   Attributes returned: {len(data.get('attributes', []))}")
            print(f"   HTML length: {len(data.get('html', ''))}")
            
            # Show first few attributes
            for attr in data.get('attributes', [])[:2]:
                print(f"   • {attr['name']} ({attr['key']}) - Values: {len(attr['values'])}")
        else:
            print(f"❌ API failed with status: {response.status_code}")
            print(f"   Response: {response.content}")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    # 5. Test attribute values
    print(f"\n📊 Sample Attribute Values:")
    size_attr = Attribute.objects.filter(key='size').first()
    if size_attr:
        values = size_attr.values.all()[:5]
        print(f"   Size values: {[v.value for v in values]}")
    
    color_attr = Attribute.objects.filter(key='color').first()
    if color_attr:
        values = color_attr.values.all()[:5]
        print(f"   Color values: {[f'{v.value} ({v.color_code})' for v in values]}")
    
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    test_flexible_attributes() 