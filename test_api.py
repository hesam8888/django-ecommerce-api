#!/usr/bin/env python3
"""
Test script for the flexible attribute system API endpoints
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/hesamoddinsaeedi/Desktop/best/backup copy 38/myshop2/myshop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from django.test import RequestFactory
from shop.api_views import get_category_attributes, filter_products_by_attributes, get_attribute_values_for_category
from shop.models import Category, Product
import json

def test_api():
    print("=== Testing Attribute System APIs ===\n")
    
    # Get a clothing category
    category = Category.objects.filter(name__contains='بلوز').first()
    if not category:
        print("❌ No بلوز category found")
        return
        
    print(f"Testing with category: {category.name} (ID: {category.id})\n")
    
    # Create a request factory
    factory = RequestFactory()
    
    # 1. Test get_category_attributes
    print("1. Testing get_category_attributes API:")
    print(f"   URL: /api/categories/{category.id}/attributes/")
    
    request = factory.get(f'/api/categories/{category.id}/attributes/')
    response = get_category_attributes(request, category.id)
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print("   ✅ Success!")
        print(f"   Category: {data['category']['name']}")
        print(f"   Attributes found: {len(data['attributes'])}")
        for attr in data['attributes'][:3]:  # Show first 3
            print(f"     • {attr['name']} ({attr['key']}) - Required: {attr['is_required']}")
            if attr['values']:
                values = [v['value'] for v in attr['values'][:3]]
                print(f"       Values: {', '.join(values)}...")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
    
    print()
    
    # 2. Test filter_products_by_attributes  
    print("2. Testing filter_products_by_attributes API:")
    print(f"   URL: /api/products/filter/?category={category.id}&color=آبی&size=L")
    
    request = factory.get(f'/api/products/filter/?category={category.id}&color=آبی&size=L')
    response = filter_products_by_attributes(request)
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print("   ✅ Success!")
        print(f"   Total products found: {data['total_products']}")
        print(f"   Filters applied: {data['filters_applied']}")
        for product in data['products'][:2]:  # Show first 2
            print(f"     • {product['name']} - {product['price_toman']:,.0f} تومان")
            for key, value in product['attributes'].items():
                print(f"       {key}: {value}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
    
    print()
    
    # 3. Test get_attribute_values_for_category
    print("3. Testing get_attribute_values_for_category API:")
    print(f"   URL: /api/categories/{category.id}/attributes/color/values/")
    
    request = factory.get(f'/api/categories/{category.id}/attributes/color/values/')
    response = get_attribute_values_for_category(request, category.id, 'color')
    
    if response.status_code == 200:
        data = json.loads(response.content)
        print("   ✅ Success!")
        print(f"   Attribute: {data['attribute']['name']} ({data['attribute']['key']})")
        print(f"   Available values: {len(data['values'])}")
        for value in data['values'][:5]:  # Show first 5
            color_info = f" ({value['color_code']})" if value.get('color_code') else ""
            print(f"     • {value['value']}{color_info}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
    
    print()
    
    # 4. Show how to use in practice
    print("4. Practical Usage Example:")
    print("   Frontend Implementation:")
    print("""
   // 1. Get available filters for a category
   fetch('/api/categories/5/attributes/')
     .then(response => response.json())
     .then(data => {
       // Build filter UI with data.attributes
       data.attributes.forEach(attr => {
         if (attr.is_filterable) {
           createFilterWidget(attr);
         }
       });
     });
   
   // 2. Filter products based on user selection
   const filters = new URLSearchParams({
     category: 5,
     color: 'آبی',
     size: 'L',
     material: 'پنبه'
   });
   
   fetch(`/api/products/filter/?${filters}`)
     .then(response => response.json())
     .then(data => {
       // Display filtered products
       displayProducts(data.products);
     });
    """)

if __name__ == "__main__":
    test_api() 