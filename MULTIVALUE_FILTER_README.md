# Multi-Value Filtering API

This documentation describes the new multi-value filtering functionality implemented for the Django products API.

## Overview

The multi-value filtering API allows filtering products using multiple values for the same filter key, enabling more flexible product searches.

## Endpoints

### 1. General Products Filter (Recommended)
**URL:** `/shop/api/products/filter/`
**Method:** `GET`
**Description:** Filters all active products with support for multi-value filtering.

### 2. Category-Specific Filter 
**URL:** `/shop/api/category/<int:category_id>/filter/`
**Method:** `GET`
**Description:** Filters products within a specific category with multi-value support.

## Features

✅ **Multi-value filtering** using `request.GET.getlist("key")`
✅ **Single and multiple values** for the same filter key
✅ **Price range filtering** (price__gte, price__lte, price_toman__gte, etc.)
✅ **Category filtering**
✅ **Text search** (searches name, description, SKU, model)
✅ **Optional filters** (works when filters are missing)
✅ **Legacy and new attribute system** support
✅ **Pagination** support
✅ **Scalable for new attribute types**

## Usage Examples

### Single Value Filter
```javascript
// Filter by single brand
fetch('/shop/api/products/filter/?brand=Nike')
  .then(response => response.json())
  .then(data => console.log(data.products));
```

### Multi-Value Filter (Same Key Multiple Times)
```javascript
// Filter by multiple brands
fetch('/shop/api/products/filter/?brand=Nike&brand=Adidas&color=Black&color=White')
  .then(response => response.json())
  .then(data => console.log(data.products));
```

### Price Range Filtering
```javascript
// Filter by price range
fetch('/shop/api/products/filter/?brand=Nike&price_toman__gte=100000&price_toman__lte=300000')
  .then(response => response.json())
  .then(data => console.log(data.products));
```

### Combined Filters
```javascript
// Combine search, category, and attribute filters
fetch('/shop/api/products/filter/?q=shirt&category=1&brand=Nike&color=Black')
  .then(response => response.json())
  .then(data => console.log(data.products));
```

### Building URLs Programmatically
```javascript
// Using URLSearchParams for multiple values
const params = new URLSearchParams();
params.append('brand', 'Nike');
params.append('brand', 'Adidas');
params.append('color', 'Black');
params.append('price_toman__gte', '100000');

fetch(`/shop/api/products/filter/?${params}`)
  .then(response => response.json())
  .then(data => console.log(data.products));
```

## Supported Filter Keys

### Attribute Filters
- Any attribute key (brand, color, size, material, etc.)
- Uses both legacy (`ProductAttribute`) and new (`ProductAttributeValue`) systems
- Supports single values: `?brand=Nike`
- Supports multiple values: `?brand=Nike&brand=Adidas`

### Price Filters
- `price__gte` - Price greater than or equal
- `price__lte` - Price less than or equal  
- `price_toman__gte` - Toman price greater than or equal
- `price_toman__lte` - Toman price less than or equal
- `price_usd__gte` - USD price greater than or equal
- `price_usd__lte` - USD price less than or equal

### Special Filters
- `category` - Filter by category ID
- `q` or `search` - Text search in name, description, SKU, model
- `page` - Pagination page number
- `per_page` - Items per page

## Response Format

```json
{
  "products": [
    {
      "id": 1,
      "name": "Nike Shirt",
      "price_toman": 100000,
      "price_usd": null,
      "description": "Nike branded shirt",
      "model": "",
      "sku": "",
      "stock_quantity": 0,
      "created_at": "2025-01-24T08:38:11Z",
      "images": [],
      "attributes": [
        {"key": "brand", "value": "Nike"},
        {"key": "color", "value": "Black"},
        {"key": "size", "value": "L"}
      ],
      "category": {
        "id": 999,
        "name": "Test Clothing"
      }
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 2,
    "has_next": false,
    "has_previous": false
  },
  "filters_applied": {
    "attributes": {
      "brand": ["Nike"]
    },
    "price": {},
    "special": {}
  },
  "available_attributes": ["brand", "color", "size", "material"]
}
```

## Implementation Details

### Multi-Value Logic
- **Single value**: Uses exact match filtering
- **Multiple values**: Uses `__in` filtering for OR logic
- **Cross-attribute**: Uses AND logic between different attributes

### Example Behavior
- `?brand=Nike&brand=Adidas` → Returns products where brand is Nike OR Adidas
- `?brand=Nike&color=Black` → Returns products where brand is Nike AND color is Black
- `?brand=Nike&brand=Adidas&color=Black&color=White` → Returns products where brand is (Nike OR Adidas) AND color is (Black OR White)

### Backward Compatibility
- Works with existing single-value filters
- Supports both legacy and new attribute systems
- Handles missing filters gracefully

## Testing

A test script is available at `test_multivalue_filter_simple.py` to verify functionality:

```bash
python3 test_multivalue_filter_simple.py
```

## Scalability

The implementation is designed to be scalable:

1. **Auto-discovery**: Automatically detects available attribute keys from the database
2. **Flexible filtering**: Works with any attribute key without code changes
3. **Dual system support**: Handles both legacy and new attribute systems
4. **Performance optimized**: Uses efficient database queries with `__in` filtering
5. **Extensible**: Easy to add new filter types or modify existing logic

## URL Structure Examples

```
# No filters - returns all active products
/shop/api/products/filter/

# Single brand
/shop/api/products/filter/?brand=Nike

# Multiple brands (OR logic)
/shop/api/products/filter/?brand=Nike&brand=Adidas

# Multiple attributes (AND logic between different keys)
/shop/api/products/filter/?brand=Nike&color=Black

# Complex multi-value (Nike OR Adidas) AND (Black OR White)
/shop/api/products/filter/?brand=Nike&brand=Adidas&color=Black&color=White

# With price range
/shop/api/products/filter/?brand=Nike&price_toman__gte=100000&price_toman__lte=200000

# With search and category
/shop/api/products/filter/?q=shirt&category=1&brand=Nike

# Category-specific filtering
/shop/api/category/1/filter/?brand=Nike&brand=Adidas
```

## Notes

- All filters are optional
- Empty filter values are automatically filtered out
- The API returns active products only
- Results are ordered by creation date (newest first)
- Pagination is supported via `page` and `per_page` parameters
- The `available_attributes` field in the response shows all possible filter keys 