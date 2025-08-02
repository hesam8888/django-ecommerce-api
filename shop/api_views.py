from django.http import JsonResponse
from django.db.models import Q
from django.db import models
from .models import Product, Attribute, NewAttributeValue, Category, ProductAttributeValue
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator


# Remove the filter_products_by_attributes function and any related code


def get_attribute_values_for_category(request, category_id, attribute_key):
    """
    Get all possible values for a specific attribute in a category
    Useful for populating filter dropdowns
    """
    try:
        category = Category.objects.get(id=category_id)
        attribute = Attribute.objects.get(key=attribute_key)
        
        # Check if this attribute is assigned to this category
        # This part of the code is no longer relevant as SubcategoryAttribute model is removed.
        # The attributes are now directly linked to the category.
        # For now, we'll return an error.
        # In a real scenario, you would check if the attribute is directly linked to the category.
        if not category.attributes.filter(key=attribute_key).exists():
            return JsonResponse({
                'error': f'Attribute {attribute_key} is not available for category {category.name}'
            }, status=400)
        
        # Get all values for this attribute
        values = NewAttributeValue.objects.filter(attribute=attribute).order_by('display_order')
        
        values_data = []
        for value in values:
            value_data = {
                'id': value.id,
                'value': value.value,
                'display_order': value.display_order
            }
            if value.color_code:
                value_data['color_code'] = value.color_code
            values_data.append(value_data)
        
        return JsonResponse({
            'attribute': {
                'id': attribute.id,
                'name': attribute.name,
                'key': attribute.key,
                'type': attribute.type
            },
            'category': {
                'id': category.id,
                'name': category.name
            },
            'values': values_data
        })
        
    except (Category.DoesNotExist, Attribute.DoesNotExist) as e:
        return JsonResponse({'error': str(e)}, status=404) 


# Deleted api_swiss_watches view as requested 

class ProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100

class CategoryProductFilterView(APIView):
    def get(self, request, category_id):
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

        # Get valid attribute keys for this category
        valid_attribute_keys = set(
            category.category_attributes.values_list('key', flat=True)
        )
        
        # Collect multi-value filters using getlist
        multi_value_filters = {}
        price_filters = {}
        
        # Handle both DRF request.query_params and Django request.GET
        query_params = getattr(request, 'query_params', request.GET)
        
        for key in query_params.keys():
            if key in valid_attribute_keys:
                values = query_params.getlist(key)
                # Remove empty values
                values = [v for v in values if v.strip()]
                if values:
                    multi_value_filters[key] = values
            elif key in ['price__gte', 'price__lte', 'price_toman__gte', 'price_toman__lte', 'price_usd__gte', 'price_usd__lte']:
                # Handle price range filtering
                value = query_params.get(key)
                if value and value.strip():
                    price_filters[key] = value

        # Return empty result if no valid filters
        if query_params and not multi_value_filters and not price_filters:
            return Response({
                "products": [], 
                "pagination": {"current_page": 1, "total_pages": 1, "total_items": 0, "has_next": False, "has_previous": False}
            }, status=status.HTTP_200_OK)

        # Start with category products
        products = Product.objects.filter(category=category, is_active=True)
        
        # Apply price filters
        for price_key, price_value in price_filters.items():
            try:
                price_value = float(price_value)
                products = products.filter(**{price_key: price_value})
            except (ValueError, TypeError):
                continue
        
        # Apply attribute filters
        for attr_key, values in multi_value_filters.items():
            if len(values) == 1:
                # Single value - exact match
                matching_ids_legacy = Product.objects.filter(
                    category=category,
                    legacy_attribute_set__key=attr_key,
                    legacy_attribute_set__value=values[0]
                ).values_list('id', flat=True)
                
                matching_ids_new = Product.objects.filter(
                    category=category,
                    attribute_values__attribute__key=attr_key,
                    attribute_values__attribute_value__value=values[0]
                ).values_list('id', flat=True)
                
                matching_ids_custom = Product.objects.filter(
                    category=category,
                    attribute_values__attribute__key=attr_key,
                    attribute_values__custom_value=values[0]
                ).values_list('id', flat=True)
                
                # Combine all matching IDs
                all_matching_ids = set(matching_ids_legacy) | set(matching_ids_new) | set(matching_ids_custom)
                products = products.filter(id__in=all_matching_ids)
            else:
                # Multiple values - use __in filtering
                matching_ids_legacy = Product.objects.filter(
                    category=category,
                    legacy_attribute_set__key=attr_key,
                    legacy_attribute_set__value__in=values
                ).values_list('id', flat=True)
                
                matching_ids_new = Product.objects.filter(
                    category=category,
                    attribute_values__attribute__key=attr_key,
                    attribute_values__attribute_value__value__in=values
                ).values_list('id', flat=True)
                
                matching_ids_custom = Product.objects.filter(
                    category=category,
                    attribute_values__attribute__key=attr_key,
                    attribute_values__custom_value__in=values
                ).values_list('id', flat=True)
                
                # Combine all matching IDs
                all_matching_ids = set(matching_ids_legacy) | set(matching_ids_new) | set(matching_ids_custom)
                products = products.filter(id__in=all_matching_ids)
        
        products = products.distinct().order_by('-created_at')

        paginator = ProductPagination()
        paginated_qs = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(paginated_qs, many=True, context={'request': request})

        pagination = {
            "current_page": paginator.page.number,
            "total_pages": paginator.page.paginator.num_pages,
            "total_items": paginator.page.paginator.count,
            "has_next": paginator.page.has_next(),
            "has_previous": paginator.page.has_previous(),
        }

        return Response({
            "products": serializer.data,
            "pagination": pagination,
            "filters_applied": multi_value_filters,
            "price_filters_applied": price_filters
        })


class ProductsFilterView(APIView):
    """
    General products filter API that supports:
    - Multi-value filtering using getlist() (e.g., ?brand=Nike&brand=Adidas)
    - Price range filtering (price__gte, price__lte, price_toman__gte, etc.)
    - Category filtering
    - Text search
    - All existing attribute filtering with both legacy and new systems
    """
    
    def get(self, request):
        # Start with all active products
        products = Product.objects.filter(is_active=True)
        
        # Collect filters
        multi_value_filters = {}
        price_filters = {}
        special_filters = {}
        
        # Get all possible attribute keys from both systems
        legacy_keys = set(products.values_list('legacy_attribute_set__key', flat=True).distinct())
        new_keys = set(products.values_list('attribute_values__attribute__key', flat=True).distinct())
        all_attribute_keys = legacy_keys | new_keys
        # Remove None values
        all_attribute_keys = {key for key in all_attribute_keys if key}
        
        # Handle both DRF request.query_params and Django request.GET
        query_params = getattr(request, 'query_params', request.GET)
        
        for key in query_params.keys():
            if key in all_attribute_keys:
                # Attribute filtering
                values = query_params.getlist(key)
                values = [v for v in values if v.strip()]
                if values:
                    multi_value_filters[key] = values
            elif key.startswith('price') and ('__gte' in key or '__lte' in key):
                # Price range filtering
                value = query_params.get(key)
                if value and value.strip():
                    price_filters[key] = value
            elif key in ['category', 'q', 'search', 'page', 'per_page', 'is_new_arrival', 'is_active']:
                # Special filters
                value = query_params.get(key)
                if value and value.strip():
                    special_filters[key] = value
        
        # Apply special filters
        if 'category' in special_filters:
            try:
                category_id = int(special_filters['category'])
                products = products.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        
        # Apply text search
        search_query = special_filters.get('q') or special_filters.get('search')
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(model__icontains=search_query)
            )
        
        # Apply new arrivals filter
        is_new_arrival = special_filters.get('is_new_arrival')
        if is_new_arrival:
            if is_new_arrival.lower() in ['true', '1', 'yes']:
                products = products.filter(is_new_arrival=True)
            elif is_new_arrival.lower() in ['false', '0', 'no']:
                products = products.filter(is_new_arrival=False)
        
        # Apply active status filter (override default is_active=True)
        is_active = special_filters.get('is_active')
        if is_active:
            if is_active.lower() in ['false', '0', 'no']:
                # Start over without the is_active=True filter
                products = Product.objects.filter(is_active=False)
                # Re-apply other filters if needed
                if 'category' in special_filters:
                    try:
                        category_id = int(special_filters['category'])
                        products = products.filter(category_id=category_id)
                    except (ValueError, TypeError):
                        pass
        
        # Apply price filters
        for price_key, price_value in price_filters.items():
            try:
                price_value = float(price_value)
                products = products.filter(**{price_key: price_value})
            except (ValueError, TypeError):
                continue
        
        # Apply attribute filters
        for attr_key, values in multi_value_filters.items():
            if len(values) == 1:
                # Single value - exact match
                matching_ids_legacy = Product.objects.filter(
                    legacy_attribute_set__key=attr_key,
                    legacy_attribute_set__value=values[0]
                ).values_list('id', flat=True)
                
                matching_ids_new = Product.objects.filter(
                    attribute_values__attribute__key=attr_key,
                    attribute_values__attribute_value__value=values[0]
                ).values_list('id', flat=True)
                
                matching_ids_custom = Product.objects.filter(
                    attribute_values__attribute__key=attr_key,
                    attribute_values__custom_value=values[0]
                ).values_list('id', flat=True)
                
                # Combine all matching IDs
                all_matching_ids = set(matching_ids_legacy) | set(matching_ids_new) | set(matching_ids_custom)
                products = products.filter(id__in=all_matching_ids)
            else:
                # Multiple values - use __in filtering
                matching_ids_legacy = Product.objects.filter(
                    legacy_attribute_set__key=attr_key,
                    legacy_attribute_set__value__in=values
                ).values_list('id', flat=True)
                
                matching_ids_new = Product.objects.filter(
                    attribute_values__attribute__key=attr_key,
                    attribute_values__attribute_value__value__in=values
                ).values_list('id', flat=True)
                
                matching_ids_custom = Product.objects.filter(
                    attribute_values__attribute__key=attr_key,
                    attribute_values__custom_value__in=values
                ).values_list('id', flat=True)
                
                # Combine all matching IDs
                all_matching_ids = set(matching_ids_legacy) | set(matching_ids_new) | set(matching_ids_custom)
                products = products.filter(id__in=all_matching_ids)
        
        # Apply ordering and distinct
        products = products.distinct().order_by('-created_at')
        
        # Pagination
        paginator = ProductPagination()
        paginated_qs = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(paginated_qs, many=True, context={'request': request})

        pagination = {
            "current_page": paginator.page.number,
            "total_pages": paginator.page.paginator.num_pages,
            "total_items": paginator.page.paginator.count,
            "has_next": paginator.page.has_next(),
            "has_previous": paginator.page.has_previous(),
        }

        return Response({
            "products": serializer.data,
            "pagination": pagination,
            "filters_applied": {
                "attributes": multi_value_filters,
                "price": price_filters,
                "special": special_filters
            },
            "available_attributes": list(all_attribute_keys)
        })


@api_view(['GET'])
def debug_category1_attributes(request):
    from .models import Product
    products = Product.objects.filter(category_id=1)
    result = []
    for p in products:
        attrs = []
        for pav in p.attribute_values.all():
            attrs.append({
                'attribute_key': pav.attribute.key,
                'custom_value': pav.custom_value,
                'attribute_value': getattr(pav.attribute_value, 'value', None)
            })
        result.append({
            'id': p.id,
            'name': p.name,
            'attributes': attrs
        })
    return Response(result) 


@api_view(['GET'])
def debug_category_attributes_structure(request, category_id):
    """Debug endpoint to show CategoryAttribute structure and product relationships"""
    try:
        category = Category.objects.get(id=category_id)
        
        # Get CategoryAttribute definitions for this category
        category_attrs = category.category_attributes.all()
        category_attrs_data = []
        for ca in category_attrs:
            category_attrs_data.append({
                'id': ca.id,
                'key': ca.key,
                'type': ca.type,
                'required': ca.required,
                'label_fa': ca.label_fa
            })
        
        # Get products in this category with their legacy attributes
        products = Product.objects.filter(category=category)
        products_data = []
        for p in products:
            legacy_attrs = []
            for pa in p.legacy_attribute_set.all():
                legacy_attrs.append({
                    'key': pa.key,
                    'value': pa.value
                })
            products_data.append({
                'id': p.id,
                'name': p.name,
                'legacy_attributes': legacy_attrs
            })
        
        return Response({
            'category': {
                'id': category.id,
                'name': category.name
            },
            'category_attributes': category_attrs_data,
            'products': products_data
        })
        
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=404) 


@api_view(['POST'])
def cleanup_product_attributes(request, product_id):
    """Clean up product attributes to only include valid ones for the product's category"""
    try:
        from .models import Product, ProductAttribute
        
        product = Product.objects.get(id=product_id)
        category = product.category
        
        # Get valid attribute keys for this category
        valid_keys = set(category.category_attributes.values_list('key', flat=True))
        
        # Get all current attributes for this product
        current_attributes = product.legacy_attribute_set.all()
        
        # Find attributes to remove (not in valid keys)
        attributes_to_remove = []
        attributes_to_keep = []
        
        for attr in current_attributes:
            if attr.key in valid_keys:
                attributes_to_keep.append(attr)
            else:
                attributes_to_remove.append(attr)
        
        # Remove invalid attributes
        removed_count = 0
        for attr in attributes_to_remove:
            attr.delete()
            removed_count += 1
        
        # Get updated attributes
        updated_attributes = []
        for attr in product.legacy_attribute_set.all():
            updated_attributes.append({
                'key': attr.key,
                'value': attr.value
            })
        
        return Response({
            'success': True,
            'message': f'Cleaned up attributes for product {product.name}',
            'removed_count': removed_count,
            'removed_attributes': [{'key': attr.key, 'value': attr.value} for attr in attributes_to_remove],
            'kept_attributes': [{'key': attr.key, 'value': attr.value} for attr in attributes_to_keep],
            'current_attributes': updated_attributes
        })
        
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400) 


@csrf_exempt
def assign_sample_attributes(request):
    """
    Development endpoint: Assigns sample attributes (brand, color) to every product if missing.
    """
    from .models import Product, Attribute, NewAttributeValue, ProductAttributeValue
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    brand_attr, _ = Attribute.objects.get_or_create(key='brand', defaults={'name': 'Brand'})
    color_attr, _ = Attribute.objects.get_or_create(key='color', defaults={'name': 'Color'})
    brand_value, _ = NewAttributeValue.objects.get_or_create(attribute=brand_attr, value='SampleBrand')
    color_value, _ = NewAttributeValue.objects.get_or_create(attribute=color_attr, value='Black')
    
    count = 0
    for product in Product.objects.all():
        # Brand
        if not ProductAttributeValue.objects.filter(product=product, attribute=brand_attr).exists():
            ProductAttributeValue.objects.create(product=product, attribute=brand_attr, attribute_value=brand_value)
            count += 1
        # Color
        if not ProductAttributeValue.objects.filter(product=product, attribute=color_attr).exists():
            ProductAttributeValue.objects.create(product=product, attribute=color_attr, attribute_value=color_value)
            count += 1
    return JsonResponse({'status': 'ok', 'attributes_added': count})


# Wishlist API Views
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Wishlist
from .serializers import WishlistSerializer, WishlistCreateSerializer, WishlistSimpleSerializer, ProductSerializer
from rest_framework.generics import ListCreateAPIView, DestroyAPIView


class WishlistListCreateAPIView(ListCreateAPIView):
    """
    API view to list all wishlist items for authenticated user or create a new one
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(customer=self.request.user).select_related(
            'product', 'product__category'
        ).prefetch_related('product__images')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WishlistCreateSerializer
        return WishlistSerializer
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """Override list method to return products with pagination in desired format"""
        from rest_framework.response import Response
        from rest_framework.pagination import PageNumberPagination
        
        queryset = self.get_queryset()
        
        # Apply pagination
        paginator = ProductPagination()
        paginated_wishlist = paginator.paginate_queryset(queryset, request)
        
        # Extract products from wishlist items
        products = []
        for wishlist_item in paginated_wishlist:
            product_serializer = ProductSerializer(wishlist_item.product)
            products.append(product_serializer.data)
        
        # Get pagination info
        paginator_info = paginator.get_paginated_response(products)
        pagination_data = {
            'current_page': paginator.page.number,
            'total_pages': paginator.page.paginator.num_pages,
            'total_items': paginator.page.paginator.count,
            'has_next': paginator.page.has_next(),
            'has_previous': paginator.page.has_previous(),
        }
        
        return Response({
            'products': products,
            'pagination': pagination_data
        })


class WishlistDestroyAPIView(DestroyAPIView):
    """
    API view to remove a product from wishlist
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSimpleSerializer
    
    def get_queryset(self):
        return Wishlist.objects.filter(customer=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_wishlist(request):
    """
    API endpoint to toggle product in/out of wishlist
    """
    product_id = request.data.get('product_id')
    
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        customer=request.user,
        product=product
    )
    
    if created:
        return Response({
            'success': True,
            'action': 'added',
            'message': 'محصول به لیست علاقه‌مندی اضافه شد'
        }, status=status.HTTP_201_CREATED)
    else:
        wishlist_item.delete()
        return Response({
            'success': True,
            'action': 'removed',
            'message': 'محصول از لیست علاقه‌مندی حذف شد'
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wishlist_status(request):
    """
    API endpoint to check if products are in wishlist
    """
    product_ids = request.GET.getlist('product_ids')
    
    if not product_ids:
        return Response({'error': 'Product IDs are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product_ids = [int(pid) for pid in product_ids if pid.isdigit()]
    except ValueError:
        return Response({'error': 'Invalid product IDs'}, status=status.HTTP_400_BAD_REQUEST)
    
    wishlist_items = Wishlist.objects.filter(
        customer=request.user,
        product_id__in=product_ids
    ).values_list('product_id', flat=True)
    
    wishlist_status = {
        str(pid): pid in wishlist_items 
        for pid in product_ids
    }
    
    return Response({
        'success': True,
        'wishlist_status': wishlist_status
    }, status=status.HTTP_200_OK) 


# Gender-based category and product API endpoints

@api_view(['GET'])
def api_categories_with_gender(request):
    """
    Enhanced category API that handles both container and direct categories
    URL: /api/categories/
    
    Returns:
    - Container categories: Categories with subcategories (like 'ساعت')
    - Direct categories: Categories with direct products (like 'کتاب')
    - Each category includes type information and product counts
    """
    try:
        # Get main categories (no parent) with prefetch for optimization
        main_categories = Category.objects.filter(parent=None).prefetch_related(
            'subcategories',
            'product_set'
        )
        
        categories_data = []
        for category in main_categories:
            effective_type = category.get_effective_category_type()
            
            category_data = {
                'id': category.id,
                'name': category.name,
                'label': category.get_display_name(),
                'parent_id': None,
                'type': effective_type,  # 'container' or 'direct'
                'product_count': category.get_product_count(),
                'subcategories': []
            }
            
            if effective_type == 'container':
                # For container categories, include subcategory details
                for subcategory in category.subcategories.all():
                    gender = subcategory.get_gender()
                    subcategory_data = {
                        'id': subcategory.id,
                        'name': subcategory.name,
                        'label': subcategory.get_display_name(),
                        'parent_id': category.id,
                        'gender': gender,
                        'product_count': subcategory.get_product_count()
                    }
                    category_data['subcategories'].append(subcategory_data)
            
            # Include category if it has products or subcategories
            if category_data['product_count'] > 0 or category_data['subcategories']:
                categories_data.append(category_data)
        
        return Response({
            'success': True,
            'categories': categories_data,
            'usage_guide': {
                'container_categories': 'Use subcategories for product loading',
                'direct_categories': 'Load products directly from main category'
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def api_products_by_gender_category(request):
    """
    Get products filtered by category and/or gender
    URL: /api/products/
    Parameters:
        - category: Category name (e.g., 'ساعت')
        - gender: Gender filter ('مردانه', 'زنانه', 'یونیسکس')
        - page: Page number for pagination
        - limit: Items per page (default: 20)
    """
    try:
        category_name = request.GET.get('category')
        gender = request.GET.get('gender')
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        search_query = request.GET.get('search', '')
        
        # Start with active products
        products = Product.objects.filter(is_active=True)
        
        # Apply category filter
        if category_name:
            # Method 1: Try gender-specific category first
            if gender:
                gender_category_name = f"{category_name} {gender}"
                gender_category = Category.objects.filter(name=gender_category_name).first()
                if gender_category:
                    products = products.filter(category=gender_category)
                else:
                    # Fallback to attribute-based filtering
                    products = filter_by_category_and_gender_attribute(products, category_name, gender)
            else:
                # Get all products from main category and its subcategories
                main_category = Category.objects.filter(name=category_name).first()
                if main_category:
                    all_subcategories = [main_category] + main_category.get_all_subcategories()
                    products = products.filter(category__in=all_subcategories)
        
        # Apply search filter
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(model__icontains=search_query)
            )
        
        # Order by creation date (newest first)
        products = products.order_by('-created_at')
        
        # Paginate results
        paginator = Paginator(products, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize products
        products_data = []
        for product in page_obj:
            # Get gender from attributes or category name
            product_gender = get_product_gender(product)
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': float(product.price_toman),
                'price_usd': float(product.price_usd) if product.price_usd else None,
                'description': product.description,
                'category_id': product.category.id,
                'category_name': product.category.name,
                'category_label': product.category.get_display_name(),
                'gender': product_gender,
                'image_url': get_product_image_url(product),
                'attributes': get_product_attributes(product),
                'created_at': product.created_at.isoformat(),
                'supplier': product.supplier.name if product.supplier else None
            }
            products_data.append(product_data)
        
        return Response({
            'success': True,
            'products': products_data,
            'pagination': {
                'page': page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'filters': {
                'category': category_name,
                'gender': gender,
                'search': search_query
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# Helper Functions
def extract_gender_from_category_name(category_name):
    """Extract gender from category name"""
    if 'مردانه' in category_name:
        return 'مردانه'
    elif 'زنانه' in category_name:
        return 'زنانه'
    elif 'یونیسکس' in category_name:
        return 'یونیسکس'
    return None

def get_product_gender(product):
    """Get product gender from attributes or category name"""
    # First try to get from attributes
    try:
        gender_attr = product.attribute_values.filter(
            attribute__key='gender'
        ).first()
        if gender_attr:
            if gender_attr.attribute_value:
                return gender_attr.attribute_value.value
            return gender_attr.custom_value
    except:
        pass
    
    # Fallback to category name
    return product.category.get_gender()

def get_product_image_url(product):
    """Get product image URL"""
    try:
        # Assuming you have a ProductImage model
        first_image = product.productimage_set.first()
        if first_image and first_image.image:
            return first_image.image.url
    except:
        pass
    return None

def get_product_attributes(product):
    """Get product attributes as a list"""
    attributes = []
    try:
        for attr_value in product.attribute_values.all():
            attributes.append({
                'key': attr_value.attribute.key,
                'value': attr_value.get_display_value(),
                'display_name': attr_value.attribute.name
            })
    except:
        pass
    return attributes

def filter_by_category_and_gender_attribute(products, category_name, gender):
    """Filter products by category and gender using attributes"""
    # Get main category
    main_category = Category.objects.filter(name=category_name).first()
    if not main_category:
        return products.none()
    
    # Get all subcategories
    all_subcategories = [main_category] + main_category.get_all_subcategories()
    
    # Filter by category and gender attribute
    return products.filter(
        category__in=all_subcategories,
        attribute_values__attribute__key='gender',
        attribute_values__attribute_value__value=gender
    ).distinct() 

@api_view(['GET'])
def api_unified_products(request):
    """
    Unified product loading endpoint that handles both category types seamlessly
    URL: /api/products/unified/
    
    Parameters:
        - category_id: Main category ID
        - subcategory_id: (Optional) Specific subcategory ID for container categories
        - gender: (Optional) Gender filter for container categories
        - search: (Optional) Search query
        - page: Page number for pagination
        - limit: Items per page (default: 20)
    
    This eliminates the need for nested loops on frontend:
    - For container categories: Automatically loads from appropriate subcategory
    - For direct categories: Loads directly from main category
    """
    try:
        category_id = request.GET.get('category_id')
        subcategory_id = request.GET.get('subcategory_id')
        gender = request.GET.get('gender')
        search_query = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        
        if not category_id:
            return Response({
                'success': False,
                'error': 'category_id is required'
            }, status=400)
        
        # Get the main category
        try:
            main_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Category not found'
            }, status=404)
        
        # Determine how to load products based on category type
        category_type = main_category.get_effective_category_type()
        
        if category_type == 'container':
            # Container category: load from subcategories
            if subcategory_id:
                # Specific subcategory requested
                try:
                    subcategory = Category.objects.get(id=subcategory_id, parent=main_category)
                    products = subcategory.get_all_products()
                    used_category = subcategory
                except Category.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Subcategory not found'
                    }, status=404)
            elif gender:
                # Gender-based filtering for container categories
                gender_subcategory = main_category.subcategories.filter(
                    name__icontains=gender
                ).first()
                
                if gender_subcategory:
                    products = gender_subcategory.get_all_products()
                    used_category = gender_subcategory
                else:
                    # No specific gender subcategory found, load all
                    products = main_category.get_all_products()
                    used_category = main_category
            else:
                # Load all products from all subcategories
                products = main_category.get_all_products()
                used_category = main_category
        else:
            # Direct category: load products directly
            products = main_category.get_all_products()
            used_category = main_category
        
        # Apply search filter
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(model__icontains=search_query) |
                Q(sku__icontains=search_query)
            )
        
        # Order by creation date (newest first)
        products = products.order_by('-created_at')
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(products, limit)
        
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        # Serialize products
        products_data = []
        for product in page_obj:
            product_data = {
                'id': product.id,
                'name': product.name,
                'price_toman': float(product.price_toman) if product.price_toman else None,
                'price_usd': float(product.price_usd) if product.price_usd else None,
                'description': product.description,
                'category_id': product.category.id,
                'category_name': product.category.name,
                'is_active': product.is_active,
                'is_new_arrival': product.is_new_arrival,
                'created_at': product.created_at.isoformat(),
                'images': [img.image.url for img in product.images.all()[:3]] if hasattr(product, 'images') else []
            }
            products_data.append(product_data)
        
        return Response({
            'success': True,
            'products': products_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'items_per_page': limit
            },
            'category_info': {
                'main_category': {
                    'id': main_category.id,
                    'name': main_category.name,
                    'type': category_type
                },
                'used_category': {
                    'id': used_category.id,
                    'name': used_category.name
                },
                'available_subcategories': [
                    {
                        'id': sub.id,
                        'name': sub.name,
                        'gender': sub.get_gender(),
                        'product_count': sub.get_product_count()
                    }
                    for sub in main_category.subcategories.all()
                ] if category_type == 'container' else []
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500) 

@api_view(['GET'])
def api_direct_categories(request):
    """
    Returns only direct categories (non-container categories) where is_container_category() returns False.
    These are categories that have products directly, not through subcategories.
    """
    try:
        # Get all categories and filter for direct categories only
        all_categories = Category.objects.filter(is_visible=True).order_by('name')
        direct_categories = []
        
        for category in all_categories:
            if not category.is_container_category():
                category_data = {
                    'id': category.id,
                    'name': category.name,
                    'label': category.get_display_name(),
                    'parent_id': category.parent.id if category.parent else None,
                    'parent_name': category.parent.name if category.parent else None,
                    'product_count': category.get_product_count(),
                    'display_section': category.get_display_section(),
                    'gender': category.get_gender(),
                    'is_container': False,  # Explicitly show this is a direct category
                    'category_type': category.get_effective_category_type()
                }
                direct_categories.append(category_data)
        
        return Response({
            'success': True,
            'count': len(direct_categories),
            'categories': direct_categories,
            'description': 'Direct categories that contain products directly (not through subcategories)'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def api_organized_categories(request):
    """
    Returns pre-organized categories ready for mobile app UI
    URL: /api/categories/organized/
    
    Returns:
    - men: Array of men's categories (leaf categories only)
    - women: Array of women's categories (leaf categories only)  
    - general: Array of general categories (books, etc.)
    - unisex: Array of unisex categories
    
    This eliminates client-side processing and provides optimal performance.
    """
    try:
        # Get only visible leaf categories (categories with products, no subcategories)
        visible_categories = Category.objects.filter(
            is_visible=True
        ).prefetch_related('parent', 'product_set')
        
        organized = {
            'men': [],
            'women': [],
            'unisex': [],
            'general': []
        }
        
        for category in visible_categories:
            # Skip container categories (they should not be visible directly)
            if category.is_container_category():
                continue
                
            # Get display section (auto-detect if not set)
            section = category.get_display_section()
            
            category_data = {
                'id': category.id,
                'name': category.name,
                'label': category.get_display_name(),
                'product_count': category.get_product_count(),
                'parent_name': category.parent.name if category.parent else None,
                'parent_id': category.parent.id if category.parent else None,
                'gender': category.get_gender(),
                'section': section
            }
            
            organized[section].append(category_data)
        
        # Sort each section by product count (most popular first)
        for section in organized:
            organized[section].sort(key=lambda x: x['product_count'], reverse=True)
        
        return Response({
            'success': True,
            'categories': organized,
            'summary': {
                'men_count': len(organized['men']),
                'women_count': len(organized['women']),
                'unisex_count': len(organized['unisex']),
                'general_count': len(organized['general']),
                'total_categories': sum(len(organized[section]) for section in organized)
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500) 

 