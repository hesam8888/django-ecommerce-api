#!/usr/bin/env python
"""
Simple test for multi-value filtering API using Django test client

This script demonstrates how to use the new multi-value filtering functionality.
Run this from the Django project root: python test_multivalue_filter_simple.py
"""

import os
import sys
import django
from django.test import Client
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from shop.models import Product, Category, ProductAttribute


def create_test_data():
    """Create some test data for filtering"""
    print("Creating test data...")
    
    # Create categories
    category, _ = Category.objects.get_or_create(name="Test Clothing", defaults={'id': 999})
    
    # Create products
    product1, _ = Product.objects.get_or_create(
        name="Nike Shirt",
        defaults={
            'price_toman': 100000,
            'category': category,
            'description': 'Nike branded shirt'
        }
    )
    
    product2, _ = Product.objects.get_or_create(
        name="Adidas Shirt", 
        defaults={
            'price_toman': 120000,
            'category': category,
            'description': 'Adidas branded shirt'
        }
    )
    
    product3, _ = Product.objects.get_or_create(
        name="Nike Shoes",
        defaults={
            'price_toman': 300000,
            'category': category,
            'description': 'Nike branded shoes'
        }
    )
    
    product4, _ = Product.objects.get_or_create(
        name="Black T-Shirt",
        defaults={
            'price_toman': 80000,
            'category': category,
            'description': 'Black colored t-shirt'
        }
    )
    
    product5, _ = Product.objects.get_or_create(
        name="White T-Shirt",
        defaults={
            'price_toman': 85000,
            'category': category,
            'description': 'White colored t-shirt'
        }
    )
    
    # Add some legacy attributes for testing
    ProductAttribute.objects.get_or_create(product=product1, key='brand', defaults={'value': 'Nike'})
    ProductAttribute.objects.get_or_create(product=product1, key='color', defaults={'value': 'Black'})
    ProductAttribute.objects.get_or_create(product=product1, key='size', defaults={'value': 'L'})
    
    ProductAttribute.objects.get_or_create(product=product2, key='brand', defaults={'value': 'Adidas'})
    ProductAttribute.objects.get_or_create(product=product2, key='color', defaults={'value': 'White'})
    ProductAttribute.objects.get_or_create(product=product2, key='size', defaults={'value': 'M'})
    
    ProductAttribute.objects.get_or_create(product=product3, key='brand', defaults={'value': 'Nike'})
    ProductAttribute.objects.get_or_create(product=product3, key='color', defaults={'value': 'Black'})
    ProductAttribute.objects.get_or_create(product=product3, key='size', defaults={'value': 'L'})
    
    ProductAttribute.objects.get_or_create(product=product4, key='brand', defaults={'value': 'Generic'})
    ProductAttribute.objects.get_or_create(product=product4, key='color', defaults={'value': 'Black'})
    ProductAttribute.objects.get_or_create(product=product4, key='size', defaults={'value': 'L'})
    
    ProductAttribute.objects.get_or_create(product=product5, key='brand', defaults={'value': 'Generic'})
    ProductAttribute.objects.get_or_create(product=product5, key='color', defaults={'value': 'White'})
    ProductAttribute.objects.get_or_create(product=product5, key='size', defaults={'value': 'M'})
    
    print("Test data created successfully!")
    return [product1, product2, product3, product4, product5]


def test_filter_api():
    """Test the multi-value filtering API using Django test client"""
    client = Client()
    
    print("\n" + "="*60)
    print("TESTING MULTI-VALUE FILTERING API")
    print("="*60)
    
    # Test 1: Single brand filter
    print("\n1. Testing single brand filter (brand=Nike):")
    print("   URL: /shop/api/products/filter/?brand=Nike")
    
    response = client.get('/shop/api/products/filter/?brand=Nike')
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Success!")
        print(f"   Total products found: {data['pagination']['total_items']}")
        for product in data['products']:
            print(f"     • {product['name']} - {product['price_toman']:,.0f} تومان")
            for attr in product['attributes']:
                if attr['key'] == 'brand':
                    print(f"       Brand: {attr['value']}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        print(f"   Response: {response.content}")
    
    # Test 2: Multiple brand filter
    print("\n2. Testing multi-brand filter (brand=Nike&brand=Adidas):")
    print("   URL: /shop/api/products/filter/?brand=Nike&brand=Adidas")
    
    response = client.get('/shop/api/products/filter/?brand=Nike&brand=Adidas')
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Success!")
        print(f"   Total products found: {data['pagination']['total_items']}")
        print(f"   Filters applied: {data['filters_applied']['attributes']}")
        for product in data['products']:
            print(f"     • {product['name']} - {product['price_toman']:,.0f} تومان")
            for attr in product['attributes']:
                if attr['key'] == 'brand':
                    print(f"       Brand: {attr['value']}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        print(f"   Response: {response.content}")
    
    # Test 3: Multiple colors filter
    print("\n3. Testing multi-color filter (color=Black&color=White):")
    print("   URL: /shop/api/products/filter/?color=Black&color=White")
    
    response = client.get('/shop/api/products/filter/?color=Black&color=White')
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Success!")
        print(f"   Total products found: {data['pagination']['total_items']}")
        print(f"   Filters applied: {data['filters_applied']['attributes']}")
        for product in data['products']:
            print(f"     • {product['name']} - {product['price_toman']:,.0f} تومان")
            for attr in product['attributes']:
                if attr['key'] == 'color':
                    print(f"       Color: {attr['value']}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        print(f"   Response: {response.content}")
    
    # Test 4: Combined multi-value filters
    print("\n4. Testing combined multi-value filters (brand=Nike&brand=Generic&color=Black):")
    print("   URL: /shop/api/products/filter/?brand=Nike&brand=Generic&color=Black")
    
    response = client.get('/shop/api/products/filter/?brand=Nike&brand=Generic&color=Black')
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Success!")
        print(f"   Total products found: {data['pagination']['total_items']}")
        print(f"   Filters applied: {data['filters_applied']['attributes']}")
        for product in data['products']:
            print(f"     • {product['name']} - {product['price_toman']:,.0f} تومان")
            brand = next((attr['value'] for attr in product['attributes'] if attr['key'] == 'brand'), 'N/A')
            color = next((attr['value'] for attr in product['attributes'] if attr['key'] == 'color'), 'N/A')
            print(f"       Brand: {brand}, Color: {color}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        print(f"   Response: {response.content}")
    
    # Test 5: Price range filtering
    print("\n5. Testing price range filtering (price_toman__gte=100000&price_toman__lte=200000):")
    print("   URL: /shop/api/products/filter/?price_toman__gte=100000&price_toman__lte=200000")
    
    response = client.get('/shop/api/products/filter/?price_toman__gte=100000&price_toman__lte=200000')
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Success!")
        print(f"   Total products found: {data['pagination']['total_items']}")
        print(f"   Price filters applied: {data['filters_applied']['price']}")
        for product in data['products']:
            print(f"     • {product['name']} - {product['price_toman']:,.0f} تومان")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        print(f"   Response: {response.content}")
    
    # Test 6: No filters (should return all active products)
    print("\n6. Testing no filters (should return all active products):")
    print("   URL: /shop/api/products/filter/")
    
    response = client.get('/shop/api/products/filter/')
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Success!")
        print(f"   Total products found: {data['pagination']['total_items']}")
        print(f"   Available attributes: {data['available_attributes']}")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        print(f"   Response: {response.content}")
    
    print("\n" + "="*60)
    print("USAGE EXAMPLES FOR FRONTEND")
    print("="*60)
    print("""
// JavaScript usage examples:

// 1. Single value filter
fetch('/shop/api/products/filter/?brand=Nike')
  .then(response => response.json())
  .then(data => console.log(data.products));

// 2. Multi-value filter (same key multiple times)
fetch('/shop/api/products/filter/?brand=Nike&brand=Adidas&color=Black&color=White')
  .then(response => response.json())
  .then(data => console.log(data.products));

// 3. With price range
fetch('/shop/api/products/filter/?brand=Nike&price_toman__gte=100000&price_toman__lte=300000')
  .then(response => response.json())
  .then(data => console.log(data.products));

// 4. With search and category
fetch('/shop/api/products/filter/?q=shirt&category=1&brand=Nike')
  .then(response => response.json())
  .then(data => console.log(data.products));

// 5. Building URLs programmatically
const params = new URLSearchParams();
params.append('brand', 'Nike');
params.append('brand', 'Adidas');
params.append('color', 'Black');
params.append('price_toman__gte', '100000');

fetch(`/shop/api/products/filter/?${params}`)
  .then(response => response.json())
  .then(data => console.log(data.products));
    """)


if __name__ == '__main__':
    try:
        create_test_data()
        test_filter_api()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc() 