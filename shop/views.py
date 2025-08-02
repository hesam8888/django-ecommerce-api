from django.http import JsonResponse
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Category, Product, ProductImage, ProductAttribute, Tag, CategoryAttribute, AttributeValue, Attribute
from .forms import ProductForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
import os
from django.views.generic import ListView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.conf import settings
from django.core.paginator import Paginator
import datetime
from pathlib import Path
import subprocess
import psutil
import humanize
from django.views.decorators.cache import never_cache
from .models import ProductAttributeValue

def home(request):
    """Home page view showing featured products and categories."""
    # Get featured products (active products with images)
    featured_products = Product.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('images')[:8]  # Limit to 8 featured products
    
    # Get all categories
    categories = Category.objects.all()
    
    # Get latest products
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category').prefetch_related('images').order_by('-created_at')[:4]  # Latest 4 products
    
    # Get new arrivals
    new_arrivals = Product.get_new_arrivals(limit=6)  # Get first 6 new arrivals
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'shop/home.html', context)

def new_arrivals(request):
    """View showing all new arrivals products."""
    
    # Handle POST requests for admin actions
    if request.method == 'POST' and request.user.is_staff:
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')
        
        if not product_ids:
            return JsonResponse({'success': False, 'message': 'هیچ محصولی انتخاب نشده است.'})
        
        try:
            if action == 'remove_new_arrival':
                # Remove from new arrivals
                Product.objects.filter(id__in=product_ids).update(is_new_arrival=False)
                return JsonResponse({
                    'success': True, 
                    'message': f'علامت "محصول جدید" از {len(product_ids)} محصول حذف شد.'
                })
                
# Delete functionality removed - only new arrival management allowed
                
            elif action == 'keep_new_arrival':
                # This is a no-op, just for confirmation
                return JsonResponse({
                    'success': True, 
                    'message': f'{len(product_ids)} محصول در لیست محصولات جدید باقی ماند.'
                })
                
            else:
                return JsonResponse({'success': False, 'message': 'عملیات نامعتبر.'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'خطا: {str(e)}'})
    
    # GET request - show the page
    # Get all new arrivals with pagination
    new_arrivals = Product.get_new_arrivals()
    
    # Apply pagination
    paginator = Paginator(new_arrivals, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'title': 'محصولات جدید',
        'is_new_arrivals': True,
    }
    return render(request, 'shop/new_arrivals.html', context)

def api_new_arrivals(request):
    """API endpoint for new arrivals products."""
    limit = request.GET.get('limit', 10)
    try:
        limit = int(limit) if limit else 10
        limit = min(limit, 50)  # Maximum 50 products
    except (ValueError, TypeError):
        limit = 10
    
    new_arrivals = Product.get_new_arrivals(limit=limit)
    
    products_data = []
    for product in new_arrivals:
        # Get primary image
        primary_image = product.images.filter(is_primary=True).first()
        image_url = None
        if primary_image and primary_image.image:
            # Convert relative URL to absolute URL
            image_url = request.build_absolute_uri(primary_image.image.url)
        
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price_toman': float(product.price_toman),
            'price_usd': float(product.price_usd) if product.price_usd else None,
            'description': product.description,
            'category': product.category.name,
            'image': image_url,
            'created_at': product.created_at.timestamp(),
            'is_active': product.is_active,
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(products_data),
        'products': products_data
    })

@staff_member_required
def admin_new_arrivals(request):
    """Admin view for managing new arrivals."""
    
    # Handle POST requests for actions
    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        
        if action == 'remove_new_arrival' and product_id:
            try:
                product = Product.objects.get(id=product_id)
                product.unmark_as_new_arrival()
                return JsonResponse({'success': True, 'message': 'علامت جدید از محصول حذف شد.'})
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'محصول یافت نشد.'})
        
        return JsonResponse({'success': False, 'message': 'عملیات نامعتبر.'})
    
    # GET request - show the page
    # Get all new arrivals
    new_arrivals = Product.objects.filter(is_new_arrival=True).select_related('category', 'supplier').prefetch_related('images')
    
    # Get statistics
    total_new_arrivals = new_arrivals.count()
    active_new_arrivals = new_arrivals.filter(is_active=True).count()
    
    # Apply pagination
    paginator = Paginator(new_arrivals, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'total_new_arrivals': total_new_arrivals,
        'active_new_arrivals': active_new_arrivals,
        'title': 'مدیریت محصولات جدید',
    }
    return render(request, 'shop/admin_new_arrivals.html', context)

def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            if images:
                for i, image in enumerate(images):
                    ProductImage.create(
                        product=product,
                        image=image,
                        is_primary=(i == 0)  # First image is primary
                    )
            
            messages.success(request, 'محصول با موفقیت ایجاد شد')
            return redirect('admin:shop_product_changelist')
    else:
        form = ProductForm()
    
    return render(request, 'admin/shop/product/create.html', {
        'form': form,
        'categories': Category.objects.all()
    })

@csrf_exempt
def reorder_images(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        for index, image_id in enumerate(data.get('image_ids', [])):
            ProductImage.objects.filter(id=image_id).update(order=index)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


def sort_product_images(request, product_id):
    product = Product.objects.get(id=product_id)
    images = product.images.all()
    return render(request, 'shop/sort_images.html', {'images': product.images.all})

@require_POST
def delete_product_image(request, image_id):
    try:
        image = get_object_or_404(ProductImage, id=image_id)
        product = image.product
        
        # Delete the image file from storage
        if image.image:
            try:
                # Get the full path to the image file
                image_path = image.image.path
                # Delete the file if it exists
                if os.path.isfile(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image file: {e}")
        
        # Store the order before deletion for reordering
        deleted_order = image.order
        
        # Delete the database record
        image.delete()
        
        # Reorder remaining images
        remaining_images = ProductImage.objects.filter(product=product).order_by('order')
        for i, img in enumerate(remaining_images):
            if img.order > deleted_order:
                img.order = i + 1
                img.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Image deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_POST
def update_image_order(request, image_id):
    try:
        data = json.loads(request.body)
        image = get_object_or_404(ProductImage, id=image_id)
        image.order = data.get('order', 0)
        image.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(staff_member_required, name='dispatch')
class ProductsExplorerAdminView(ListView):
    model = Product
    template_name = 'suppliers/products_explorer.html'
    context_object_name = 'products'
    paginate_by = 24
    
    def get_queryset(self):
        # Start with all products
        queryset = Product.objects.all()
        
        # Apply search filter
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(sku__icontains=query) |
                Q(supplier__name__icontains=query) |
                Q(supplier__email__icontains=query)
            )
        
        # Apply category filter
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Apply status filter
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'draft':
            queryset = queryset.filter(draft=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Apply supplier filter (admin-specific)
        supplier_id = self.request.GET.get('supplier', '')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        # Apply sorting
        sort = self.request.GET.get('sort', 'created_desc')
        if sort == 'created_desc':
            queryset = queryset.order_by('-created_at')
        elif sort == 'created_asc':
            queryset = queryset.order_by('created_at')
        elif sort == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'supplier_asc':
            queryset = queryset.order_by('supplier__name')
        elif sort == 'supplier_desc':
            queryset = queryset.order_by('-supplier__name')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Apply new arrivals filter
        new_arrivals = self.request.GET.get('new_arrivals', '')
        if new_arrivals == 'yes':
            queryset = queryset.filter(is_new_arrival=True)
        elif new_arrivals == 'no':
            queryset = queryset.filter(is_new_arrival=False)
        
        return queryset.select_related('supplier', 'category')

    def post(self, request, *args, **kwargs):
        """Handle POST requests for bulk actions"""
        action = request.POST.get('action')
        product_ids = request.POST.getlist('product_ids')
        
        if action == 'mark_new_arrivals' and product_ids:
            Product.objects.filter(id__in=product_ids).update(is_new_arrival=True)
            messages.success(request, f'{len(product_ids)} محصول به عنوان "محصول جدید" علامت‌گذاری شد.')
        elif action == 'unmark_new_arrivals' and product_ids:
            Product.objects.filter(id__in=product_ids).update(is_new_arrival=False)
            messages.success(request, f'علامت "محصول جدید" از {len(product_ids)} محصول حذف شد.')
        elif action == 'toggle_active' and product_ids:
            for product_id in product_ids:
                product = Product.objects.get(id=product_id)
                product.is_active = not product.is_active
                product.save()
            messages.success(request, f'وضعیت {len(product_ids)} محصول تغییر کرد.')
        
        return redirect(request.get_full_path())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all categories
        context['categories'] = Category.objects.all()
        # Removed brands logic
        # Get all suppliers for admin filtering
        from suppliers.models import Supplier
        suppliers = Supplier.objects.all().order_by('name')
        # Create a list of suppliers
        supplier_list = []
        for supplier in suppliers:
            supplier_list.append({
                'id': supplier.id,
                'name': supplier.name
            })
        # Sort the list by supplier name
        supplier_list.sort(key=lambda x: x['name'].lower())
        context['suppliers'] = supplier_list
        # Save search parameters
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_supplier'] = self.request.GET.get('supplier', '')
        context['selected_category'] = self.request.GET.get('category', '')
        # Removed selected_brand
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_sort'] = self.request.GET.get('sort', 'created_desc')
        context['selected_new_arrivals'] = self.request.GET.get('new_arrivals', '')
        
        # Add new arrivals statistics
        total_products = Product.objects.count()
        new_arrivals_count = Product.objects.filter(is_new_arrival=True).count()
        active_new_arrivals = Product.objects.filter(is_new_arrival=True, is_active=True).count()
        
        context['total_products'] = total_products
        context['new_arrivals_count'] = new_arrivals_count
        context['active_new_arrivals'] = active_new_arrivals
        
        # Set admin flag to customize template behavior
        context['is_admin'] = True
        return context

@staff_member_required
def product_detail(request, product_id):
    """Get product details for the sidebar view in admin."""
    product = get_object_or_404(Product, id=product_id)
    
    # Get product attributes
    attributes = ProductAttribute.objects.filter(product=product)
    attributes_dict = {attr.key: attr.value for attr in attributes}
    
    # Get product images
    images = ProductImage.objects.filter(product=product).order_by('order', 'created_at')
    
    # Format all product images
    product_images = []
    for image in images:
        try:
            image_url = image.image.url
            if not image_url.startswith(('http://', 'https://')):
                current_site = request.build_absolute_uri('/').rstrip('/')
                image_url = f"{current_site}{image_url}"
            product_images.append({
                'url': image_url,
                'is_primary': image.is_primary
            })
        except Exception as e:
            print(f"Error getting image URL: {e}")
    
    # Get similar products (same category and brand, excluding current product)
    similar_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]  # Limit to 4 similar products
    
    # Format similar products data
    similar_products_data = []
    for similar in similar_products:
        similar_image = ProductImage.objects.filter(product=similar).first()
        image_url = None
        if similar_image and similar_image.image:
            try:
                image_url = similar_image.image.url
                if not image_url.startswith(('http://', 'https://')):
                    current_site = request.build_absolute_uri('/').rstrip('/')
                    image_url = f"{current_site}{image_url}"
            except Exception as e:
                print(f"Error getting similar product image URL: {e}")
        
        similar_products_data.append({
            'id': similar.id,
            'name': similar.name,
            'price': str(similar.price),
            'image_url': image_url
        })
    
    # Get product tags
    tags = product.tags.all().values('id', 'name')
    
    # Return JSON response for API
    data = {
        'id': product.id,
        'name': product.name,
        'price': str(product.price),
        'description': product.description or '',
        'category': str(product.category),
        'supplier': str(product.supplier) if product.supplier else '',
        'is_active': product.is_active,
        'created_at': product.created_at.timestamp(),  # Return as seconds since 1970 for Swift Date
        'attributes': attributes_dict,
        'images': product_images,
        'similar_products': similar_products_data,
        'tags': list(tags)  # Add tags to the response
    }
    
    return JsonResponse(data)

def get_tags_for_category(request):
    """
    Endpoint to fetch tags for a specific category
    Example: /shop/get_tags_for_category/?category_id=1
    """
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse({'error': 'Category ID is required'}, status=400)
    
    try:
        tags = Tag.objects.filter(categories__id=category_id).values('id', 'name')
        return JsonResponse({'tags': list(tags)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@staff_member_required
@require_POST
def delete_product(request, product_id):
    """Handle product deletion via AJAX"""
    try:
        product = Product.objects.get(id=product_id)
        product_name = str(product)
        product.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Product "{product_name}" was successfully deleted.'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Product not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_products(request):
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    
    try:
        page = int(page)
        per_page = int(per_page)
    except ValueError:
        return JsonResponse({'error': 'Invalid page or per_page parameter'}, status=400)
    
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    paginator = Paginator(products, per_page)
    
    try:
        products_page = paginator.page(page)
    except:
        return JsonResponse({'error': 'Page not found'}, status=404)
    
    products_data = []
    for product in products_page:
        product_dict = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price_toman': float(product.price_toman),
            'price_usd': float(product.price_usd) if product.price_usd else None,
            'model': product.model,
            'sku': product.sku,
            'stock_quantity': product.stock_quantity,
            'created_at': product.created_at.timestamp(),  # Return as seconds since 1970 for Swift Date
            'images': [],
            'attributes': []
        }
        
        # Add images
        for image in product.images.all():
            product_dict['images'].append({
                'url': request.build_absolute_uri(image.image.url),
                'is_primary': image.is_primary
            })
            
        # Add attributes
        for attr_value in product.attribute_values.all():
            product_dict['attributes'].append({
                'key': attr_value.attribute.key,
                'value': attr_value.get_display_value()
            })
            
        products_data.append(product_dict)
    
    return JsonResponse({
        'products': products_data,
        'pagination': {
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_items': paginator.count,
            'has_next': products_page.has_next(),
            'has_previous': products_page.has_previous(),
        }
    })

@require_http_methods(["GET"])
def api_advanced_search(request):
    """
    Advanced search API endpoint that supports multiple search criteria:
    - Text search in name, description, SKU
    - Price range (min/max) in both Toman and USD
    - Category filter
    - Tag filter
    - Brand filter
    - Attribute filters
    - Stock availability
    - Active status
    """
    try:
        # Start with base queryset
        queryset = Product.objects.select_related('category', 'supplier').prefetch_related('tags', 'attribute_set', 'images')

        # Text search
        search_query = request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(model__icontains=search_query)
            )

        # Price range filters
        min_price_toman = request.GET.get('min_price_toman')
        max_price_toman = request.GET.get('max_price_toman')
        min_price_usd = request.GET.get('min_price_usd')
        max_price_usd = request.GET.get('max_price_usd')

        if min_price_toman:
            queryset = queryset.filter(price_toman__gte=min_price_toman)
        if max_price_toman:
            queryset = queryset.filter(price_toman__lte=max_price_toman)
        if min_price_usd:
            queryset = queryset.filter(price_usd__gte=min_price_usd)
        if max_price_usd:
            queryset = queryset.filter(price_usd__lte=max_price_usd)

        # Category filter
        category_id = request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Tag filter
        tags = request.GET.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()

        # Stock availability
        in_stock = request.GET.get('in_stock')
        if in_stock == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        elif in_stock == 'false':
            queryset = queryset.filter(stock_quantity=0)

        # Active status
        is_active = request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        # Attribute filters
        for key, value in request.GET.items():
            if key.startswith('attr_'):
                attr_key = key[5:]  # Remove 'attr_' prefix
                queryset = queryset.filter(attribute_set__key=attr_key, attribute_set__value=value)

        # Enforce explicit ordering by '-created_at' unless overridden by a sort param
        sort_by = request.GET.get('sort_by')
        valid_sort_fields = {
            'name': 'name',
            '-name': '-name',
            'price': 'price_toman',
            '-price': '-price_toman',
            'date': 'created_at',
            '-date': '-created_at'
        }
        if sort_by:
            sort_field = valid_sort_fields.get(sort_by, '-created_at')
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by('-created_at')

        # Pagination
        page = request.GET.get('page', 1)
        per_page = int(request.GET.get('per_page', 24))
        paginator = Paginator(queryset, per_page)
        
        try:
            products_page = paginator.page(page)
        except:
            products_page = paginator.page(1)

        # Prepare response data
        products_data = []
        for product in products_page:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price_toman': float(product.price_toman),
                'price_usd': float(product.price_usd) if product.price_usd else None,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name
                },
                'model': product.model,
                'sku': product.sku,
                'stock_quantity': product.stock_quantity,
                'is_active': product.is_active,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in product.tags.all()],
                'attributes': [
                    {'key': attr.key, 'value': attr.value}
                    for attr in product.attribute_set.all()
                ],
                'images': [
                    {
                        'id': img.id,
                        'url': request.build_absolute_uri(img.image.url),
                        'is_primary': img.is_primary
                    }
                    for img in product.images.all()
                ]
            }
            products_data.append(product_data)

        response_data = {
            'products': products_data,
            'pagination': {
                'current_page': products_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': products_page.has_next(),
                'has_previous': products_page.has_previous(),
            }
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def api_simple_search(request):
    """
    Simple search API endpoint that supports:
    - Basic text search in name, description, SKU, brand, and model
    - Fuzzy matching as fallback when exact matches return no results
    - Pagination
    - Sorting by price, date, or name
    """
    try:
        # Get search parameters
        search_query = request.GET.get('q', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 24))
        sort_by = request.GET.get('sort_by', '-date')  # Default sort by newest first
        use_fuzzy = request.GET.get('fuzzy', 'true').lower() == 'true'  # Enable fuzzy by default
        valid_sort_fields = {
            'name': 'name',
            '-name': '-name',
            'price': 'price_toman',
            '-price': '-price_toman',
            'date': 'created_at',
            '-date': '-created_at'
        }
        sort_field = valid_sort_fields.get(sort_by, '-created_at')
        
        # Start with base queryset
        queryset = Product.objects.filter(is_active=True).prefetch_related('images', 'attribute_values', 'attribute_values__attribute')
        
        # Apply category filter
        category_id = request.GET.get('category')
        if category_id:
            print(f"DEBUG: Filtering by category ID: {category_id}")
            queryset = queryset.filter(category_id=category_id)
            print(f"DEBUG: Products after category filter: {queryset.count()}")
        
        # Apply search if query exists
        if search_query:
            # First try exact matching
            exact_queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(model__icontains=search_query)
            )
            
            # If no results and fuzzy matching is enabled, try fuzzy matching
            if exact_queryset.count() == 0 and use_fuzzy:
                from django.db import connection
                if connection.vendor == 'postgresql':
                    from django.contrib.postgres.search import TrigramSimilarity
                    queryset = queryset.annotate(
                        name_similarity=TrigramSimilarity('name', search_query),
                        model_similarity=TrigramSimilarity('model', search_query),
                        sku_similarity=TrigramSimilarity('sku', search_query)
                    ).filter(
                        Q(name_similarity__gt=0.3) |
                        Q(model_similarity__gt=0.3) |
                        Q(sku_similarity__gt=0.3)
                    ).order_by(
                        '-name_similarity',
                        '-model_similarity',
                        '-sku_similarity'
                    )
                else:
                    queryset = exact_queryset.none()
            else:
                queryset = exact_queryset
        
        # Apply sorting (only if not using fuzzy matching)
        if not (use_fuzzy and search_query and exact_queryset.count() == 0):
            queryset = queryset.order_by(sort_field)
        else:
            queryset = queryset.order_by('-created_at')
        
        # Apply pagination
        paginator = Paginator(queryset, per_page)
        
        try:
            products_page = paginator.page(page)
        except:
            products_page = paginator.page(1)
        
        # Prepare response data
        products_data = []
        for product in products_page:
            # Get all images for the product
            images = []
            for image in product.images.all().order_by('-is_primary', 'order'):
                images.append({
                    'id': image.id,
                    'url': request.build_absolute_uri(image.image.url),
                    'is_primary': image.is_primary,
                    'order': image.order
                })
            
            # --- Populate attributes using attribute_values and legacy_attribute_set ---
            # Only include attributes defined for the product's category, using new system first, then legacy fallback
            attributes = []
            if product.category:
                allowed_keys = list(product.category.category_attributes.values_list('key', flat=True))
                for key in allowed_keys:
                    value = None
                    # Try new system (ProductAttributeValue)
                    pav = product.attribute_values.filter(attribute__key=key).first()
                    if pav and hasattr(pav, 'get_display_value') and pav.get_display_value():
                        value = pav.get_display_value()
                    else:
                        # Fallback to legacy
                        legacy = product.legacy_attribute_set.filter(key=key).first()
                        if legacy and legacy.value:
                            value = legacy.value
                    # Always add the attribute if a value is found
                    if value is not None and value != "":
                        attributes.append({'key': key, 'value': value})
                # Ensure 'brand' is always included if it is a category attribute and has a value
                if 'brand' in allowed_keys and not any(attr['key'] == 'brand' for attr in attributes):
                    # Always fetch brand from attribute_values or legacy_attribute_set
                    brand_value = None
                    pav = product.attribute_values.filter(attribute__key='brand').first()
                    if pav and hasattr(pav, 'get_display_value') and pav.get_display_value():
                        brand_value = pav.get_display_value()
                    else:
                        legacy = product.legacy_attribute_set.filter(key='brand').first()
                        if legacy and legacy.value:
                            brand_value = legacy.value
                    if brand_value:
                        attributes.append({'key': 'brand', 'value': brand_value})
            
            # Remove 'brand' and rename 'برند' to 'brand'
            new_attributes = []
            for attr in attributes:
                if attr['key'] == 'برند':
                    attr['key'] = 'brand'
                new_attributes.append(attr)
            attributes = new_attributes
            
            # Remove any 'brand' from attributes (to avoid duplicates)
            attributes = [attr for attr in attributes if attr['key'] != 'brand']
            # Add 'brand' from flexible attributes only (never from product.brand)
            brand_value = None
            pav = product.attribute_values.filter(attribute__key='brand').first()
            if pav and hasattr(pav, 'get_display_value') and pav.get_display_value():
                brand_value = pav.get_display_value()
            else:
                legacy = product.legacy_attribute_set.filter(key='brand').first()
                if legacy and legacy.value:
                    brand_value = legacy.value
            if brand_value:
                attributes.append({'key': 'brand', 'value': brand_value})
            
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price_toman': float(product.price_toman),
                'price_usd': float(product.price_usd) if product.price_usd else None,
                'model': product.model,
                'sku': product.sku,
                'stock_quantity': product.stock_quantity,
                'images': images,
                'attributes': attributes,
                'created_at': product.created_at.timestamp(),  # Return as timestamp for Swift Date
            }
            
            # Add brand image if available
            if hasattr(product, 'brand_image') and product.brand_image:
                current_site = request.build_absolute_uri('/').rstrip('/')
                brand_image_url = product.brand_image.url
                if not brand_image_url.startswith(('http://', 'https://')):
                    brand_image_url = f"{current_site}{brand_image_url}"
                product_data['brand_image'] = brand_image_url
            else:
                product_data['brand_image'] = None
            
            # Add similarity scores if using fuzzy matching
            if use_fuzzy and search_query and exact_queryset.count() == 0:
                product_data['similarity_scores'] = {
                    'name': float(getattr(product, 'name_similarity', 0)),
                    'model': float(getattr(product, 'model_similarity', 0)),
                    'sku': float(getattr(product, 'sku_similarity', 0))
                }
            
            products_data.append(product_data)
        
        response_data = {
            'products': products_data,
            'pagination': {
                'current_page': products_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': products_page.has_next(),
                'has_previous': products_page.has_previous(),
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@staff_member_required
@never_cache
def backup_logs(request):
    """Enhanced view for monitoring database backup logs with statistics"""
    log_file = "/var/log/postgres_backup.log"
    backup_dir = "/backups"
    
    # Get backup logs
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.readlines()[-100:]  # Get last 100 lines
    
    # Get backup files with enhanced information
    backup_files = []
    total_size = 0
    if os.path.exists(backup_dir):
        for f in Path(backup_dir).glob('backup-*.sql.gz'):
            size = f.stat().st_size
            total_size += size
            backup_files.append({
                'name': f.name,
                'size': size,
                'size_human': humanize.naturalsize(size),
                'date': datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'age_days': (datetime.datetime.now() - datetime.datetime.fromtimestamp(f.stat().st_mtime)).days
            })
    
    # Sort backups by date
    backup_files.sort(key=lambda x: x['date'], reverse=True)
    
    # Get system statistics
    disk_usage = psutil.disk_usage(backup_dir)
    system_stats = {
        'disk_total': humanize.naturalsize(disk_usage.total),
        'disk_used': humanize.naturalsize(disk_usage.used),
        'disk_free': humanize.naturalsize(disk_usage.free),
        'disk_percent': disk_usage.percent,
        'backup_count': len(backup_files),
        'total_backup_size': humanize.naturalsize(total_size)
    }
    
    # Get backup statistics
    backup_stats = {
        'success_count': sum(1 for log in logs if 'Backup completed successfully' in log),
        'error_count': sum(1 for log in logs if 'ERROR' in log),
        'last_success': next((log for log in reversed(logs) if 'Backup completed successfully' in log), 'Never'),
        'last_error': next((log for log in reversed(logs) if 'ERROR' in log), 'None')
    }
    
    context = {
        'logs': logs,
        'backup_files': backup_files,
        'log_file': log_file,
        'backup_dir': backup_dir,
        'system_stats': system_stats,
        'backup_stats': backup_stats
    }
    
    return render(request, 'shop/backup_logs.html', context)

@staff_member_required
@require_POST
def delete_backup(request, filename):
    """Delete a specific backup file"""
    backup_path = os.path.join('/backups', filename)
    if os.path.exists(backup_path):
        try:
            os.remove(backup_path)
            messages.success(request, f'Backup {filename} deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting backup: {str(e)}')
    else:
        messages.error(request, 'Backup file not found')
    return redirect('backup_logs')

@staff_member_required
def download_backup(request, filename):
    """Download a specific backup file"""
    backup_path = os.path.join('/backups', filename)
    if os.path.exists(backup_path):
        with open(backup_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/gzip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return HttpResponse('Backup file not found', status=404)

@staff_member_required
@require_POST
def trigger_backup(request):
    """Manually trigger a backup"""
    try:
        # Execute the backup script
        result = subprocess.run(['/usr/local/bin/backup_postgres.sh'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            messages.success(request, 'Backup triggered successfully')
        else:
            messages.error(request, f'Backup failed: {result.stderr}')
    except Exception as e:
        messages.error(request, f'Error triggering backup: {str(e)}')
    
    return redirect('backup_logs')

@staff_member_required
def get_backup_status(request):
    """API endpoint for real-time backup status"""
    log_file = "/var/log/postgres_backup.log"
    backup_dir = "/backups"
    
    # Get latest logs
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.readlines()[-10:]  # Get last 10 lines
    
    # Get backup files
    backup_files = []
    if os.path.exists(backup_dir):
        backup_files = sorted([
            {
                'name': f.name,
                'size': humanize.naturalsize(f.stat().st_size),
                'date': datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            }
            for f in Path(backup_dir).glob('backup-*.sql.gz')
        ], key=lambda x: x['date'], reverse=True)
    
    return JsonResponse({
        'logs': logs,
        'backup_files': backup_files,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

def api_categories(request):
    """
    Returns all categories (main and subcategories) with their id, name, parent (id and name if exists),
    and a list of subcategories (id and name).
    """
    from .models import Category
    from django.http import JsonResponse

    categories = Category.objects.all()
    data = []
    for cat in categories:
        parent_obj = None
        if cat.parent:
            parent_obj = {
                'id': cat.parent.id,
                'name': cat.parent.name
            }
        subcats = cat.subcategories.all()
        subcategories_list = [
            {
                'id': sub.id, 
                'name': sub.name,
                'label': sub.get_display_name(),
                'gender': sub.get_gender()
            } for sub in subcats
        ]
        data.append({
            'id': cat.id,
            'name': cat.name,
            'label': cat.get_display_name(),
            'parent': parent_obj,
            'subcategories': subcategories_list,
        })
    return JsonResponse({'categories': data})

def search_page(request):
    """
    Search page with category filtering
    """
    # Get search parameters
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 12))
    sort_by = request.GET.get('sort_by', '-created_at')
    
    # Get all categories for the filter dropdown
    categories = Category.objects.all().order_by('name')
    
    # Build search URL
    search_params = {}
    if search_query:
        search_params['q'] = search_query
    if category_id:
        search_params['category'] = category_id
    if page != 1:
        search_params['page'] = page
    if per_page != 12:
        search_params['per_page'] = per_page
    if sort_by != '-created_at':
        search_params['sort_by'] = sort_by
    
    # Get selected category name
    selected_category = None
    if category_id:
        try:
            selected_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            pass
    
    context = {
        'search_query': search_query,
        'categories': categories,
        'selected_category': selected_category,
        'selected_category_id': category_id,
        'current_page': int(page),
        'per_page': per_page,
        'sort_by': sort_by,
        'search_params': search_params,
    }
    
    return render(request, 'shop/search.html', context)

@require_http_methods(["GET"])
def api_category_attributes(request, category_id):
    """
    Returns all attributes for a given category (e.g., ساعت) as a list of dicts keyed by attribute key.
    Example response:
    {
        "category": {"id": 1, "name": "ساعت"},
        "attributes": [
            {
                "key": "نوع موومنت",
                "type": "select",
                "required": true,
                "display_order": 0,
                "label_fa": "نوع موومنت",
                "values": ["کوارتز", "اتوماتیک", "دستی"]
            },
            ...
        ]
    }
    """
    try:
        category = Category.objects.get(id=category_id)
        attributes = CategoryAttribute.objects.filter(category=category).order_by('display_order', 'key')
        attributes_data = []
        for attr in attributes:
            values = list(attr.values.order_by('display_order', 'value').values_list('value', flat=True))
            attributes_data.append({
                'key': attr.key,
                'type': attr.type,
                'required': attr.required,
                'display_order': attr.display_order,
                'label_fa': attr.label_fa,
                'values': values
            })
        return JsonResponse({
            'category': {'id': category.id, 'name': category.name},
            'attributes': attributes_data
        })
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)


# Wishlist Views
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from .models import Wishlist

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def add_to_wishlist(request):
    """Add a product to user's wishlist."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Create or get wishlist item
        wishlist_item, created = Wishlist.objects.get_or_create(
            customer=request.user,
            product=product
        )
        
        if created:
            return JsonResponse({
                'success': True,
                'message': 'محصول به لیست علاقه‌مندی اضافه شد',
                'added': True
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'محصول در لیست علاقه‌مندی شما موجود است',
                'added': False
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def remove_from_wishlist(request):
    """Remove a product from user's wishlist."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        
        try:
            wishlist_item = Wishlist.objects.get(
                customer=request.user,
                product_id=product_id
            )
            wishlist_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'محصول از لیست علاقه‌مندی حذف شد',
                'removed': True
            })
            
        except Wishlist.DoesNotExist:
            return JsonResponse({
                'success': True,
                'message': 'محصول در لیست علاقه‌مندی شما موجود نیست',
                'removed': False
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def wishlist_view(request):
    """Display user's wishlist."""
    wishlist_items = Wishlist.objects.filter(
        customer=request.user
    ).select_related('product', 'product__category').prefetch_related('product__images').order_by('-created_at')
    
    # Add pagination
    paginator = Paginator(wishlist_items, 12)  # Show 12 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wishlist_items': page_obj,
        'total_items': wishlist_items.count(),
    }
    
    return render(request, 'shop/wishlist.html', context)


@login_required
def get_wishlist_status(request):
    """Get wishlist status for multiple products (for showing heart icons)."""
    product_ids = request.GET.getlist('product_ids')
    
    if not product_ids:
        return JsonResponse({'error': 'Product IDs are required'}, status=400)
    
    try:
        # Convert to integers
        product_ids = [int(pid) for pid in product_ids if pid.isdigit()]
        
        # Get wishlist status for all products
        wishlist_items = Wishlist.objects.filter(
            customer=request.user,
            product_id__in=product_ids
        ).values_list('product_id', flat=True)
        
        wishlist_status = {
            str(pid): pid in wishlist_items 
            for pid in product_ids
        }
        
        return JsonResponse({
            'success': True,
            'wishlist_status': wishlist_status
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid product IDs'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def product_list_with_wishlist(request):
    """Product list view with wishlist status for authenticated users."""
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
    
    # Apply filters
    category_id = request.GET.get('category')
    search_query = request.GET.get('search')
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Add wishlist status for authenticated users
    if request.user.is_authenticated:
        products = products.annotate(
            is_in_wishlist=Exists(
                Wishlist.objects.filter(
                    customer=request.user,
                    product=OuterRef('pk')
                )
            )
        )
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': Category.objects.all(),
        'current_category': category_id,
        'search_query': search_query,
    }
    
    return render(request, 'shop/product_list.html', context)
