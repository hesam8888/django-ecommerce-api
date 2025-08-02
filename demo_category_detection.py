#!/usr/bin/env python3
"""
Demonstration script showing how category detection works
and what the APIs return
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from shop.models import Category, Product

def demo_detection_logic():
    """Demonstrate how the automatic detection works"""
    
    print("🔍 CATEGORY TYPE DETECTION DEMO")
    print("=" * 50)
    
    # Get some sample categories
    categories = Category.objects.all()[:10]
    
    for category in categories:
        print(f"\nCategory: {category.name} (ID: {category.id})")
        print(f"Current category_type setting: {category.category_type}")
        
        # Show the detection logic step by step
        has_subcategories = category.subcategories.exists()
        has_direct_products = category.product_set.filter(is_active=True).exists()
        detected_type = category.get_effective_category_type()
        
        print(f"├─ Has subcategories: {has_subcategories}")
        print(f"├─ Has direct products: {has_direct_products}")
        print(f"└─ 🎯 Detected type: {detected_type}")
        
        # Show the logic
        if has_subcategories and not has_direct_products:
            print("   Logic: Has subcategories + No direct products → CONTAINER")
        elif not has_subcategories and has_direct_products:
            print("   Logic: No subcategories + Has direct products → DIRECT")
        elif has_subcategories and has_direct_products:
            print("   Logic: Has both → CONTAINER (default)")
        else:
            print("   Logic: Has neither → DIRECT (default)")

def demo_api_response():
    """Show what the API would return"""
    
    print("\n\n🔗 API RESPONSE DEMO")
    print("=" * 50)
    
    # Simulate the enhanced categories API response
    main_categories = Category.objects.filter(parent=None)[:3]
    
    api_response = {
        "success": True,
        "categories": [],
        "usage_guide": {
            "container_categories": "Use subcategories for product loading",
            "direct_categories": "Load products directly from main category"
        }
    }
    
    for category in main_categories:
        effective_type = category.get_effective_category_type()
        
        category_data = {
            "id": category.id,
            "name": category.name,
            "label": category.get_display_name(),
            "parent_id": None,
            "type": effective_type,  # ← THIS IS THE KEY!
            "product_count": category.get_product_count(),
            "subcategories": []
        }
        
        if effective_type == 'container':
            # For container categories, include subcategory details
            for subcategory in category.subcategories.all():
                subcategory_data = {
                    "id": subcategory.id,
                    "name": subcategory.name,
                    "label": subcategory.get_display_name(),
                    "parent_id": category.id,
                    "gender": subcategory.get_gender(),
                    "product_count": subcategory.get_product_count()
                }
                category_data["subcategories"].append(subcategory_data)
        
        api_response["categories"].append(category_data)
    
    print("Sample API Response:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))

def demo_frontend_usage():
    """Show how frontend would use this information"""
    
    print("\n\n📱 FRONTEND USAGE DEMO")
    print("=" * 50)
    
    print("Swift code would handle it like this:")
    print("""
// 1. Load categories from API
let response = await loadCategories() // /api/categories/

// 2. Check category type and handle accordingly
for category in response.categories {
    if category.type == "container" {
        // Show subcategories first, then load products from subcategory
        print("📁 \(category.name) - Container Category")
        print("   Available subcategories:")
        for sub in category.subcategories {
            print("   - \(sub.name) (\(sub.productCount) products)")
        }
        
        // Load products: /api/products/unified/?category_id=\(id)&subcategory_id=\(subId)
        
    } else if category.type == "direct" {
        // Load products directly from this category
        print("📄 \(category.name) - Direct Category")
        print("   Products: \(category.productCount)")
        
        // Load products: /api/products/unified/?category_id=\(id)
    }
}
""")

def demo_detection_examples():
    """Show specific examples of detection"""
    
    print("\n\n📊 DETECTION EXAMPLES")
    print("=" * 50)
    
    examples = [
        {
            "name": "ساعت (Watches)",
            "has_subcategories": True,
            "has_products": False,
            "subcategories": ["ساعت مردانه", "ساعت زنانه", "ساعت یونیسکس"],
            "detected_type": "container",
            "explanation": "Has gender subcategories, no direct products"
        },
        {
            "name": "کتاب (Books)",
            "has_subcategories": False,
            "has_products": True,
            "subcategories": [],
            "detected_type": "direct",
            "explanation": "No subcategories needed, products directly in this category"
        },
        {
            "name": "Test Category",
            "has_subcategories": True,
            "has_products": True,
            "subcategories": ["Sub1", "Sub2"],
            "detected_type": "container",
            "explanation": "Mixed case: defaults to container"
        }
    ]
    
    for example in examples:
        print(f"\n📁 {example['name']}")
        print(f"   Has subcategories: {example['has_subcategories']}")
        print(f"   Has direct products: {example['has_products']}")
        print(f"   Subcategories: {example['subcategories']}")
        print(f"   🎯 Detected type: {example['detected_type']}")
        print(f"   Why: {example['explanation']}")

if __name__ == "__main__":
    try:
        demo_detection_logic()
        demo_api_response()
        demo_frontend_usage()
        demo_detection_examples()
        
        print("\n\n✅ SUMMARY")
        print("=" * 50)
        print("The system automatically detects category types by:")
        print("1. Checking if category has subcategories")
        print("2. Checking if category has direct products")
        print("3. Applying logic rules to determine type")
        print("4. Exposing this information via API 'type' field")
        print("5. Frontend uses 'type' field to handle each category appropriately")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you're running this from the Django project directory") 