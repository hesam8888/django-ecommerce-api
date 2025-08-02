# Flexible Attribute System Usage Guide

## Overview
The flexible attribute system allows you to create reusable attributes and assign them to multiple product subcategories. This means you can define attributes like "سایز" (size), "رنگ" (color), "جنس" (material) once and then use them across different clothing categories.

## Key Components

### 1. **Attribute** - Reusable attributes
- **Name**: Display name (e.g., "سایز", "رنگ")
- **Key**: Unique identifier for API use (e.g., "size", "color")
- **Type**: Input type (select, color, size, etc.)
- **Is Filterable**: Can be used in search filters

### 2. **NewAttributeValue** - Values for each attribute
- **Value**: The actual value (e.g., "L", "آبی", "پنبه")
- **Display Order**: Sort order
- **Color Code**: Hex color for color attributes

### 3. **SubcategoryAttribute** - Assigns attributes to subcategories
- **Subcategory**: Which category gets this attribute
- **Attribute**: Which attribute to assign
- **Is Required**: Whether it's mandatory for products
- **Display Order**: Order in forms

### 4. **ProductAttributeValue** - Links products to attribute values
- **Product**: The product
- **Attribute**: Which attribute
- **Attribute Value**: Predefined value OR
- **Custom Value**: Free text value

## How to Use

### A. Django Admin Interface

1. **Create/Manage Attributes** (`/admin/shop/attribute/`)
   - Add new attributes like "وزن" (weight), "طول" (length)
   - Set the type and whether it's filterable

2. **Add Attribute Values** (`/admin/shop/newattributevalue/`)
   - Add values for your attributes
   - Set display order and color codes if needed

3. **Assign to Subcategories** (`/admin/shop/subcategoryattribute/`)
   - Choose which attributes each subcategory should have
   - Mark required attributes

4. **Set Product Attributes** (`/admin/shop/product/`)
   - When editing products, you'll see attribute inlines
   - Set values for each product's attributes

### B. Programmatic Usage

```python
from shop.models import Product, Attribute, Category

# Get a product
product = Product.objects.get(id=1)

# Set attribute values
product.set_attribute_value('size', 'L')
product.set_attribute_value('color', 'آبی')
product.set_attribute_value('material', 'پنبه')

# Get attribute values
size = product.get_attribute_value('size')  # Returns 'L'
all_attrs = product.get_attributes_dict()   # Returns {'size': 'L', 'color': 'آبی', ...}

# Get available attributes for a product
available = product.get_available_attributes()
```

### C. API Usage

The system includes API endpoints for frontend integration:

```python
# Get attributes for a category
GET /api/categories/5/attributes/

# Filter products by attributes
GET /api/products/filter/?category=5&color=آبی&size=L

# Get values for a specific attribute in a category
GET /api/categories/5/attributes/color/values/
```

## Current Setup

Your system currently has:
- **7 clothing attributes**: سایز, رنگ, جنس, استایل, قد لباس, نوع یقه, مناسبت
- **34 attribute values** across these attributes
- **65 subcategory assignments** (attributes assigned to clothing subcategories)

### Clothing Categories with Attributes:
- **پالتو و کاپشن**: سایز, رنگ, جنس, استایل, مناسبت
- **بلوز و شومیز**: سایز, رنگ, جنس, استایل, مناسبت, نوع یقه  
- **پیراهن**: سایز, رنگ, جنس, استایل, قد لباس, نوع یقه, مناسبت
- **تی‌شرت و تاپ**: سایز, رنگ, جنس, استایل, مناسبت
- **شلوار و لگ**: سایز, رنگ, جنس, استایل, مناسبت
- **دامن**: سایز, رنگ, جنس, استایل, قد لباس, مناسبت
- **کت و جلیقه**: سایز, رنگ, جنس, استایل, مناسبت
- **لباس بافتنی**: سایز, رنگ, جنس, استایل, مناسبت
- **ست لباس راحتی**: سایز, رنگ, جنس, استایل, مناسبت

## Benefits

1. **Reusability**: Create "سایز" once, use across all clothing categories
2. **Consistency**: Same size values (XS, S, M, L, XL, XXL) across all products
3. **Flexibility**: Easy to add new attributes or modify existing ones
4. **Scalability**: System works for any product category (electronics, home goods, etc.)
5. **API Ready**: Built-in filtering and search capabilities

## Adding New Product Categories

To extend to other categories (shoes, bags, electronics):

1. **Create new attributes** (e.g., "اندازه صفحه نمایش" for electronics)
2. **Add attribute values** (e.g., "13 اینچ", "15 اینچ")
3. **Create subcategories** (e.g., "لپ‌تاپ", "موبایل")
4. **Assign attributes** to subcategories via SubcategoryAttribute

## Example Workflow

1. **Customer visits website** → Selects "بلوز و شومیز" category
2. **Frontend calls API** → `/api/categories/5/attributes/` → Gets available filters
3. **Customer sets filters** → رنگ=آبی, سایز=L
4. **Frontend calls API** → `/api/products/filter/?category=5&color=آبی&size=L`
5. **System returns** → Filtered products with those exact attributes

This creates a powerful, flexible e-commerce attribute system that scales with your business needs. 