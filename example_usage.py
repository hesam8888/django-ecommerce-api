#!/usr/bin/env python3
"""
Example script showing how to use the flexible attribute system
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/hesamoddinsaeedi/Desktop/best/backup copy 38/myshop2/myshop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from shop.models import *

def main():
    print("=== Flexible Attribute System Usage Example ===\n")
    
    # 1. Show available attributes
    print("1. Available Attributes:")
    for attr in Attribute.objects.all():
        print(f"   • {attr.name} ({attr.key}) - Type: {attr.type}")
        values = [v.value for v in attr.values.all()[:3]]
        if values:
            print(f"     Values: {', '.join(values)}{'...' if attr.values.count() > 3 else ''}")
    
    # 2. Show a clothing subcategory and its attributes
    print("\n2. Subcategory Example - بلوز و شومیز:")
    category = Category.objects.filter(name__contains='بلوز').first()
    if category:
        print(f"   Category: {category.name}")
        print("   Assigned Attributes:")
        for sa in category.category_attributes.all():
            required = "✓ Required" if sa.is_required else "○ Optional"
            print(f"     • {sa.attribute.name} ({required})")
    
    # 3. Create a sample product with attributes
    print("\n3. Creating a Product with Attributes:")
    
    # Check if product already exists
    existing_product = Product.objects.filter(name='بلوز شیک زنانه نمونه').first()
    if existing_product:
        print(f"   Using existing product: {existing_product.name}")
        product = existing_product
    else:
        # Get supplier
        supplier = Supplier.objects.first()
        
        product = Product.objects.create(
            name='بلوز شیک زنانه نمونه',
            description='بلوز زیبا و راحت برای خانم‌ها - نمونه استفاده از سیستم ویژگی‌ها',
            price_toman=150000,
            category=category,
            supplier=supplier
        )
        print(f"   Created product: {product.name}")
    
    # 4. Set attribute values
    print("\n4. Setting Attribute Values:")
    
    # سایز = L
    product.set_attribute_value('size', 'L')
    print("   ✓ Set سایز = L")
    
    # رنگ = آبی  
    product.set_attribute_value('color', 'آبی')
    print("   ✓ Set رنگ = آبی")
    
    # جنس = پنبه
    product.set_attribute_value('material', 'پنبه')
    print("   ✓ Set جنس = پنبه")
    
    # استایل = کژوال
    product.set_attribute_value('style', 'کژوال')
    print("   ✓ Set استایل = کژوال")
    
    # 5. Retrieve and display all attributes
    print("\n5. Product Attributes:")
    attrs = product.get_attributes_dict()
    for key, value in attrs.items():
        print(f"   • {key}: {value}")
    
    # 6. Show how to get available attributes for a product
    print("\n6. Available Attributes for this Product:")
    available_attrs = product.get_available_attributes()
    for attr in available_attrs:
        print(f"   • {attr.name} ({attr.key}) - Type: {attr.type}")
    
    # 7. Example of filtering products by attributes (simulation)
    print("\n7. Example: Find all products with specific attributes")
    print("   Query: Products in بلوز category with رنگ=آبی and سایز=L")
    
    # This is how you would filter in real scenarios
    matching_products = Product.objects.filter(
        category=category,
        attribute_values__attribute__key='color',
        attribute_values__attribute_value__value='آبی'
    ).filter(
        attribute_values__attribute__key='size', 
        attribute_values__attribute_value__value='L'
    ).distinct()
    
    print(f"   Found {matching_products.count()} matching products:")
    for p in matching_products:
        print(f"     • {p.name}")
        # Show attributes
        for key, value in p.get_attributes_dict().items():
            print(f"       {key}: {value}")

if __name__ == "__main__":
    main() 