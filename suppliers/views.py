import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, ListView, DetailView
from django.db.models import Q, Max, Sum
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse, HttpResponseServerError
from django.contrib import admin
from django.contrib.admin.helpers import AdminForm
from django.contrib.admin.options import get_ul_class
from django.contrib.admin.utils import flatten_fieldsets
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from .models import BackupLog, Supplier
from shop.models import Product, Category, ProductImage, ProductAttribute, OrderItem, Order, Tag, CategoryAttribute
from shop.forms import ProductForm
from django.db import transaction
from .models import SupplierInvitation
from .forms import SupplierRegistrationForm
from .models import SupplierAdmin, Store

# Get the custom user model
User = get_user_model()

# Custom login required decorator that allows superusers to bypass the login check
def supplier_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Superusers can access any supplier page
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        # Use Django's login_required for regular users
        if not request.user.is_authenticated:
            # Redirect to supplier login rather than Django's default login
            return redirect('suppliers:login')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def supplier_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('suppliers:login')
        
        # Allow superusers to access all supplier pages
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        # Check if user is a supplier admin
        try:
            SupplierAdmin.objects.get(user=request.user)
        except SupplierAdmin.DoesNotExist:
            raise PermissionDenied(_("You don't have permission to access this page."))
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Custom mixin for class-based views
class SupplierLoginRequiredMixin:
    """
    CBV mixin that ensures superusers can access supplier pages without redirection
    """
    def dispatch(self, request, *args, **kwargs):
        # Allow superusers to access all supplier pages
        if request.user.is_authenticated and request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
            
        # Regular users need to be logged in
        if not request.user.is_authenticated:
            return redirect('suppliers:login')
            
        return super().dispatch(request, *args, **kwargs)

def register_with_token(request, token):
    try:
        invitation = SupplierInvitation.objects.get(token=token)
        if not invitation.is_valid():
            messages.error(request, "This invitation link is invalid or has expired.")
            return redirect('admin:index')

        if request.method == 'POST':
            form = SupplierRegistrationForm(request.POST)
            if form.is_valid():
                # Create the user
                user = form.save(commit=False)
                user.email = invitation.email
                user.username = form.cleaned_data['username']
                user.first_name = invitation.owner_first_name or ''
                user.last_name = invitation.owner_last_name or ''
                user.is_supplier_admin = True
                user.save()
                
                # Create or get supplier
                supplier = None
                if invitation.supplier:
                    supplier = invitation.supplier
                    # Update the supplier with the new user
                    supplier.user = user
                    supplier.save()
                else:
                    # Check if a supplier with this email already exists
                    try:
                        supplier = Supplier.objects.get(email=invitation.email)
                        # Update the supplier with the new user
                        supplier.user = user
                        supplier.save()
                    except Supplier.DoesNotExist:
                        # Create a new supplier with available information
                        supplier = Supplier.objects.create(
                            user=user,
                            name=invitation.store_name or f"{invitation.email}'s Store",
                            email=invitation.email,
                            phone=invitation.phone_number or '',
                            address=invitation.address or ''
                        )
                
                # Create store if not exists and supplier exists
                if supplier:
                    store, created = Store.objects.get_or_create(
                        supplier=supplier,
                        defaults={
                            'name': invitation.store_name or supplier.name,
                            'address': invitation.address or ''
                        }
                    )
                    
                    # Create supplier admin role
                    SupplierAdmin.objects.create(
                        user=user,
                        supplier=supplier,
                        role='owner'  # Set a default role for the owner
                    )
                
                # Mark invitation as used
                invitation.is_used = True
                invitation.status = 'accepted'
                invitation.supplier = supplier
                invitation.save()
                
                # Log the user in
                login(request, user)
                messages.success(request, "Registration successful! You are now logged in.")
                
                # Redirect to success page
                return render(request, 'suppliers/register_success.html', {
                    'user': user,
                    'supplier': supplier
                })
        else:
            # Pre-fill the form with invitation data
            initial_data = {
                'username': invitation.store_username,
                'email': invitation.email,
                'first_name': invitation.owner_first_name,
                'last_name': invitation.owner_last_name
            }
            form = SupplierRegistrationForm(initial=initial_data)

        return render(request, 'suppliers/register.html', {
            'form': form,
            'invitation': invitation
        })
    except SupplierInvitation.DoesNotExist:
        messages.error(request, "Invalid invitation link.")
        return redirect('admin:index')

class SupplierLoginView(View):
    def get(self, request):
        print("GET request received for supplier login")
        if request.user.is_authenticated:
            print("User is authenticated")
            if request.user.is_superuser or request.user.is_supplier_admin:
                print("User is superuser or supplier admin, redirecting to dashboard")
                return redirect('suppliers:dashboard')
            else:
                print("User is not supplier admin or superuser, logging out")
                logout(request)
        
        form = SupplierLoginForm()
        print("Rendering login template")
        return render(request, 'suppliers/login.html', {
            'form': form,
            'title': 'Supplier Login'
        })

    def post(self, request):
        print("POST request received for supplier login")
        form = SupplierLoginForm(data=request.POST)
        if form.is_valid():
            print("Form is valid")
            user = form.get_user()
            login(request, user)
            messages.success(request, "You have been successfully logged in.")
            return redirect('suppliers:dashboard')
        
        print("Form is invalid")
        return render(request, 'suppliers/login.html', {
            'form': form,
            'title': 'Supplier Login'
        })

@login_required
def supplier_logout(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('suppliers:login')

class SupplierDashboardView(SupplierLoginRequiredMixin, ListView):
    model = Product
    template_name = 'suppliers/dashboard.html'
    context_object_name = 'products'
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        print("DEBUG: SupplierDashboardView dispatch started")
        print(f"DEBUG: User is: {request.user.username}, is_superuser: {request.user.is_superuser}")
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            print("DEBUG: User is not authenticated, redirecting to login")
            return redirect('suppliers:login')
        
        # For superusers, allow access without redirection
        if request.user.is_superuser:
            print("DEBUG: User is superuser, allowing access to dashboard")
            return super().dispatch(request, *args, **kwargs)
        
        # Check if user is a supplier admin
        try:
            supplier_admin = SupplierAdmin.objects.get(user=request.user)
            print(f"DEBUG: Found SupplierAdmin record for user: {supplier_admin}")
            try:
                result = super().dispatch(request, *args, **kwargs)
                print("DEBUG: Supplier admin dispatch successful")
                return result
            except Exception as e:
                print(f"DEBUG: Error in supplier admin dispatch: {str(e)}")
                raise
        except SupplierAdmin.DoesNotExist:
            print("DEBUG: SupplierAdmin record not found, raising PermissionDenied")
            raise PermissionDenied(_("This page is only accessible to supplier accounts."))
        except Exception as e:
            print(f"DEBUG: Unexpected error checking supplier admin: {str(e)}")
            raise

    def get_queryset(self):
        print("DEBUG: SupplierDashboardView get_queryset started")
        
        # For superusers, we might be viewing a specific supplier's products
        if self.request.user.is_superuser:
            print("DEBUG: get_queryset for superuser")
            supplier_id = self.request.GET.get('supplier_id')
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                    print(f"DEBUG: Filtering products for supplier_id={supplier_id}")
                    return Product.objects.filter(supplier=supplier).order_by('-created_at')
                except Supplier.DoesNotExist:
                    print(f"DEBUG: Supplier with ID {supplier_id} not found")
                    pass
            # If no supplier_id specified or invalid, show all products for superusers
            print("DEBUG: Returning all products for superuser")
            return Product.objects.all().order_by('-created_at')

        # Get the supplier admin for the current user
        try:
            print(f"DEBUG: Getting SupplierAdmin for user {self.request.user.username}")
            supplier_admin = SupplierAdmin.objects.get(user=self.request.user)
            supplier = supplier_admin.supplier
            if not supplier:
                print("DEBUG: No supplier associated with account")
                raise PermissionDenied("No supplier associated with your account.")
            print(f"DEBUG: Found supplier: {supplier.name}")
        except SupplierAdmin.DoesNotExist:
            print("DEBUG: SupplierAdmin record not found in get_queryset")
            raise PermissionDenied("You don't have permission to access this page.")
        except Exception as e:
            print(f"DEBUG: Error accessing supplier data: {str(e)}")
            raise PermissionDenied(f"Error accessing supplier data: {str(e)}")

        queryset = Product.objects.filter(supplier=supplier)

        # Handle category filtering
        category_id = self.request.GET.get('category')
        if category_id and category_id != 'all':
            print(f"DEBUG: Filtering by category_id={category_id}")
            queryset = queryset.filter(category_id=category_id)

        # Handle search
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            print(f"DEBUG: Searching for query: {search_query}")
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query)
            )

        print(f"DEBUG: get_queryset returning {queryset.count()} products")
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        print("DEBUG: SupplierDashboardView get_context_data started")
        try:
            context = super().get_context_data(**kwargs)
            print("DEBUG: Base context data retrieved successfully")
        except Exception as e:
            print(f"DEBUG: Error in super().get_context_data: {str(e)}")
            raise
        
        # For superusers, we might be viewing a specific supplier's products
        if self.request.user.is_superuser:
            print("DEBUG: Building context for superuser")
            supplier_id = self.request.GET.get('supplier_id')
            if supplier_id:
                try:
                    supplier = get_object_or_404(Supplier, id=supplier_id)
                    context['supplier'] = supplier
                    
                    # Add total sales for this supplier
                    context['total_sales'] = OrderItem.objects.filter(
                        product__supplier=supplier
                    ).aggregate(total=Sum('price'))['total'] or 0
                    
                    # Add total orders for this supplier
                    context['total_orders'] = Order.objects.filter(
                        items__product__supplier=supplier
                    ).distinct().count()
                except:
                    # Fallback for invalid supplier_id
                    context['suppliers'] = Supplier.objects.all()
                    context['total_sales'] = OrderItem.objects.filter(
                        order__paid=True
                    ).aggregate(total=Sum('price'))['total'] or 0
                    context['total_orders'] = Order.objects.filter(
                        paid=True
                    ).count()
                    context['is_superuser_view'] = True
            else:
                # No specific supplier selected, show all suppliers
                context['suppliers'] = Supplier.objects.all()
                
                # Add total sales across all suppliers
                context['total_sales'] = OrderItem.objects.filter(
                    order__paid=True
                ).aggregate(total=Sum('price'))['total'] or 0
                
                # Add total orders across all suppliers
                context['total_orders'] = Order.objects.filter(
                    paid=True
                ).count()
                
                # Flag to indicate we're in superuser mode without a specific supplier
                context['is_superuser_view'] = True
        else:
            try:
                # Regular supplier admin flow
                supplier_admin = SupplierAdmin.objects.get(user=self.request.user)
                supplier = supplier_admin.supplier
                
                # Add supplier to context
                context['supplier'] = supplier
                
                # Add total sales for this supplier
                context['total_sales'] = OrderItem.objects.filter(
                    product__supplier=supplier
                ).aggregate(total=Sum('price'))['total'] or 0
                
                # Add total orders for this supplier
                context['total_orders'] = Order.objects.filter(
                    items__product__supplier=supplier
                ).distinct().count()
            except SupplierAdmin.DoesNotExist:
                # Handle the case where a user without SupplierAdmin record somehow gets past dispatch
                context['total_sales'] = 0
                context['total_orders'] = 0
        
        # Add categories to context
        context['categories'] = Category.objects.all()
        
        # Add current category to context
        category_id = self.request.GET.get('category')
        if category_id and category_id != 'all':
            try:
                context['current_category'] = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        # Add search query to context
        context['search_query'] = self.request.GET.get('search', '')
        
        # Add total products count
        context['total_products'] = self.get_queryset().count()

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # For AJAX requests, render only the products section
                html = render_to_string('suppliers/includes/products_section.html', context)
                response = HttpResponse(html)
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            except Exception as e:
                return HttpResponseServerError(f"Error rendering products section: {str(e)}")
        return super().render_to_response(context, **response_kwargs)

@login_required
def select_supplier(request):
    """View for selecting a supplier before adding a product"""
    if not request.user.is_superuser:
        messages.error(request, _("Only superusers can access this page."))
        return redirect('suppliers:dashboard')
    
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'suppliers/select_supplier.html', {
        'suppliers': suppliers,
        'title': _('Select Supplier')
    })

@login_required
def add_product(request):
    # Check if this is an edit request (product_id in GET parameters)
    product_id = request.GET.get('product_id')
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        # Check if user has permission to edit this product
        if not request.user.is_superuser and product.supplier != request.user.supplieradmin.supplier:
            raise PermissionDenied

    supplier = None
    if not request.user.is_superuser:
        supplier = request.user.supplieradmin.supplier

    if request.method == 'POST':
        print("DEBUG: POST request received")
        print(f"DEBUG: POST data: {request.POST}")
        print(f"DEBUG: FILES data: {request.FILES}")
        
        # Convert is_active to boolean
        post_data = request.POST.copy()
        post_data['is_active'] = post_data.get('is_active') == 'true'
        
        form = ProductForm(post_data, request.FILES, instance=product)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the product first
                    product = form.save(commit=False)
                    if supplier:
                        product.supplier = supplier
                    product.save()
                    # Save tags using form's save_m2m method
                    form.save_m2m()
                    
                    # Handle image uploads - NEW SIMPLIFIED APPROACH
                    print("🔄 NEW SIMPLIFIED BACKEND APPROACH")
                    print("=" * 50)
                    
                    # If editing, delete ALL existing images first
                    if product_id:
                        print("📝 Editing mode: Deleting all existing images")
                        existing_images = ProductImage.objects.filter(product=product)
                        for img in existing_images:
                            print(f"   🗑️ Deleting: {img.image.name}")
                            if img.image and os.path.isfile(img.image.path):
                                os.remove(img.image.path)
                            img.delete()
                        print(f"   ✅ Deleted {existing_images.count()} existing images")
                    
                    # Get all images sent by frontend
                    all_images = request.FILES.getlist('all_images')
                    image_orders = request.POST.getlist('image_order')
                    
                    print(f"📥 Received {len(all_images)} images from frontend")
                    print(f"📥 Received {len(image_orders)} order values")
                    
                    # Create new images in order
                    for i, image_file in enumerate(all_images):
                        order = int(image_orders[i]) + 1 if i < len(image_orders) else i + 1
                        
                        print(f"   📷 Creating image {i+1}: order={order}, file={image_file.name}")
                        
                        try:
                            new_image = ProductImage.create(
                                product=product,
                                image=image_file,
                                is_primary=(order == 1),
                                order=order
                            )
                            print(f"   ✅ Created image ID {new_image.id} with order {order}")
                        except Exception as e:
                            print(f"   ❌ Error creating image: {str(e)}")
                            continue
                    
                    print("=" * 50)
                    print("✅ IMAGE PROCESSING COMPLETE")
                    
                    # Also handle any new images from the regular file input (fallback)
                    regular_images = request.FILES.getlist('images')
                    if regular_images:
                        print(f"📥 Processing {len(regular_images)} additional regular images")
                        current_max_order = ProductImage.objects.filter(product=product).aggregate(Max('order'))['order__max'] or 0
                        
                        for i, image in enumerate(regular_images):
                            order = current_max_order + i + 1
                            print(f"   📷 Creating additional image: order={order}")
                            
                            try:
                                new_image = ProductImage.create(
                                    product=product,
                                    image=image,
                                    is_primary=(order == 1),
                                    order=order
                                )
                                print(f"   ✅ Created additional image ID {new_image.id}")
                            except Exception as e:
                                print(f"   ❌ Error creating additional image: {str(e)}")
                                continue
                
                    # Save category attributes
                    category = form.cleaned_data.get('category')
                    if category:
                        # Get all category attributes
                        category_attrs = CategoryAttribute.objects.filter(category=category)
                        for attr in category_attrs:
                            attr_key = f'attr_{attr.key}'
                            value = request.POST.get(attr_key, '').strip()
                            # For required attributes, ensure they have a value
                            if attr.required and not value:
                                raise ValueError(f'فیلد {attr.key} الزامی است')
                            # Save the attribute value using ProductAttribute (legacy system)
                            if value:
                                pav, created = ProductAttribute.objects.get_or_create(product=product, key=attr.key)
                                if attr.type == 'multiselect':
                                    pav.value = ','.join(request.POST.getlist(attr_key))
                                else:
                                    pav.value = value
                                pav.save()
                messages.success(request, _("Product has been saved successfully."))
                
                # Determine redirect URL based on the submit button clicked
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    if '_addanother' in request.POST:
                        redirect_url = reverse('suppliers:add_product')
                    elif '_continue' in request.POST:
                        redirect_url = f'{reverse("suppliers:add_product")}?product_id={product.id}'
                    elif request.user.is_superuser:
                        redirect_url = reverse('shop:admin_products_explorer')
                    else:
                        redirect_url = reverse('suppliers:dashboard')
                    
                    return JsonResponse({
                        'success': True,
                        'redirect_url': redirect_url
                    })
                else:
                    # Handle regular form submission
                    if '_addanother' in request.POST:
                        return redirect('suppliers:add_product')
                    elif '_continue' in request.POST:
                        return redirect(f'{reverse("suppliers:add_product")}?product_id={product.id}')
                    elif request.user.is_superuser:
                        return redirect('shop:admin_products_explorer')
                    else:
                        return redirect('suppliers:dashboard')
                    
            except Exception as e:
                print(f"DEBUG: Error saving product: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                messages.error(request, f"Error saving product: {str(e)}")
        else:
            print(f"DEBUG: Form errors: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': ' '.join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
                })
            messages.error(request, "Please correct the errors below.")
    else:
        # Initialize form with product instance if editing
        if product:
            form = ProductForm(instance=product)
        else:
            form = ProductForm()
    
    # Get all categories for dropdown
    categories = Category.objects.all()
    
    # Get category attributes for dynamic form
    category_attributes = {}
    for category in categories:
        print(f"DEBUG: Processing category: {category.name} (ID: {category.id})")
        
        # Legacy attributes
        legacy_attrs = CategoryAttribute.objects.filter(category=category)
        print(f"DEBUG: Found {legacy_attrs.count()} legacy attributes for {category.name}")
        
        legacy_list = [{
            'key': attr.key,
            'required': attr.required,
            'type': attr.type,
            'value': '',
            'source': 'legacy',
            'values': [v.value for v in attr.values.all()]
        } for attr in legacy_attrs]
        
        print(f"DEBUG: Legacy list for {category.name}: {len(legacy_list)} items")

        # Flexible attributes (if subcategory)
        flexible_list = []
        # Remove any code that directly uses SubcategoryAttribute (such as queries, filters, etc.)
        
        category_attributes[category.id] = legacy_list + flexible_list
        print(f"DEBUG: Total attributes for {category.name}: {len(category_attributes[category.id])}")
    
    print(f"DEBUG: Final category_attributes keys: {list(category_attributes.keys())}")
    print(f"DEBUG: Sample data for first category: {list(category_attributes.values())[0] if category_attributes else 'No data'}")
    
    # Add detailed debugging for watch category specifically
    watch_category_id = None
    for cat in categories:
        if cat.name == 'ساعت':
            watch_category_id = cat.id
            break
    
    if watch_category_id:
        print(f"DEBUG: Watch category ID: {watch_category_id}")
        if watch_category_id in category_attributes:
            watch_attrs = category_attributes[watch_category_id]
            print(f"DEBUG: Watch category has {len(watch_attrs)} attributes")
            for i, attr in enumerate(watch_attrs[:3]):  # Show first 3
                print(f"DEBUG: Watch attr {i+1}: {attr['key']} ({attr['type']}) - {len(attr.get('values', []))} values")
        else:
            print(f"DEBUG: Watch category ID {watch_category_id} not found in category_attributes")
    else:
        print("DEBUG: Watch category not found in categories")
    
    print(f"DEBUG: category_attributes JSON length: {len(json.dumps(category_attributes))}")
    
    # Load existing attribute values if editing
    existing_attrs = {}
    if product:
        # Get all product attributes
        product_attrs = ProductAttribute.objects.filter(product=product)
        for attr in product_attrs:
            existing_attrs[attr.key] = attr.value
    
    # Get available tags for each category
    category_tags = {}
    for category in categories:
        tags = Tag.objects.filter(categories=category).values('id', 'name').distinct()
        category_tags[category.id] = list(tags)
    
    # Get currently selected tags if editing
    selected_tags = []
    if product:
        selected_tags = list(product.tags.values_list('id', flat=True).distinct())
    
    # Get current product images if editing
    product_images = []
    if product:
        for img in product.images.all().order_by('order'):
            product_images.append({
                'id': img.id,
                'url': img.image.url,
                'is_primary': img.is_primary,
                'order': img.order
            })
    
    title = _('Edit Product') if product else _('Add Product')
    
    return render(request, 'suppliers/add_product.html', {
        'form': form,
        'product': product,
        'categories': categories,
        'category_attributes': json.dumps(category_attributes),
        'existing_attrs': json.dumps(existing_attrs),
        'category_tags': json.dumps(category_tags),
        'selected_tags': json.dumps(selected_tags),
        'product_images': json.dumps(product_images),
        'supplier': supplier,
        'is_superuser': request.user.is_superuser,
        'title': title,
        'is_edit': bool(product)
    })

@supplier_login_required
def edit_product(request, product_id):
    """Redirect to add_product with product_id as a query parameter"""
    return redirect(f'{reverse("suppliers:add_product")}?product_id={product_id}')

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Get the deletion reason from the form
        deletion_reason = request.POST.get('deletion_reason', '')
        
        # Delete the product using the new method
        product.delete(deleted_by=request.user, deletion_reason=deletion_reason)
        
        messages.success(request, 'محصول با موفقیت حذف شد.')
        return redirect('suppliers:product_list')
    
    return render(request, 'suppliers/delete_product.html', {
        'product': product
    })

@login_required
@supplier_required
def sold_items(request):
    # For superusers, allow viewing all sales or filter by supplier
    if request.user.is_superuser:
        supplier_id = request.GET.get('supplier_id')
        if supplier_id:
            try:
                supplier = Supplier.objects.get(id=supplier_id)
                sold_items = OrderItem.objects.filter(
                    product__supplier=supplier,
                    order__paid=True
                ).select_related('product', 'order').order_by('-order__created')
                
                # Calculate totals for this supplier
                total_sales = sold_items.aggregate(total=Sum('price'))['total'] or 0
                total_items = sold_items.aggregate(total=Sum('quantity'))['total'] or 0
                
                # Get sales by product
                sales_by_product = sold_items.values(
                    'product__name',
                    'product__sku'
                ).annotate(
                    total_quantity=Sum('quantity'),
                    total_revenue=Sum('price')
                ).order_by('-total_quantity')
                
                context = {
                    'sold_items': sold_items,
                    'total_sales': total_sales,
                    'total_items': total_items,
                    'sales_by_product': sales_by_product,
                    'supplier': supplier,
                    'suppliers': Supplier.objects.all(),
                    'is_superuser': True
                }
                return render(request, 'suppliers/sold_items.html', context)
            except Supplier.DoesNotExist:
                pass
        
        # Show all sales for all suppliers
        sold_items = OrderItem.objects.filter(
            order__paid=True
        ).select_related('product', 'order').order_by('-order__created')
        
        # Calculate totals
        total_sales = sold_items.aggregate(total=Sum('price'))['total'] or 0
        total_items = sold_items.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get sales by product
        sales_by_product = sold_items.values(
            'product__name',
            'product__sku',
            'product__supplier__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('price')
        ).order_by('-total_quantity')
        
        context = {
            'sold_items': sold_items,
            'total_sales': total_sales,
            'total_items': total_items,
            'sales_by_product': sales_by_product,
            'suppliers': Supplier.objects.all(),
            'is_superuser': True
        }
        return render(request, 'suppliers/sold_items.html', context)
    
    # Regular supplier admin flow
    try:
        supplier_admin = SupplierAdmin.objects.get(user=request.user)
        supplier = supplier_admin.supplier
    except SupplierAdmin.DoesNotExist:
        raise PermissionDenied(_("You don't have permission to access this page."))

    # Get all order items for products belonging to this supplier
    sold_items = OrderItem.objects.filter(
        product__supplier=supplier,
        order__paid=True
    ).select_related('product', 'order').order_by('-order__created')

    # Calculate total sales and items
    total_sales = sold_items.aggregate(total=Sum('price'))['total'] or 0
    total_items = sold_items.aggregate(total=Sum('quantity'))['total'] or 0

    # Get sales by product
    sales_by_product = sold_items.values(
        'product__name',
        'product__sku'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_quantity')

    context = {
        'sold_items': sold_items,
        'total_sales': total_sales,
        'total_items': total_items,
        'sales_by_product': sales_by_product,
        'supplier': supplier
    }
    return render(request, 'suppliers/sold_items.html', context)

@login_required
def test_add_product(request):
    try:
        supplier_admin = SupplierAdmin.objects.get(user=request.user)
        supplier = supplier_admin.supplier
    except SupplierAdmin.DoesNotExist:
        raise PermissionDenied(_("You don't have permission to add products."))
    
    if request.method == 'POST':
        # Debug information
        print("POST request received for test add product")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid")
            product = form.save(commit=False)
            product.supplier = supplier
            product.save()
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            print(f"Found {len(images)} images")
            if images:
                for i, image in enumerate(images):
                    ProductImage.create(
                        product=product,
                        image=image,
                        is_primary=(i == 0)  # First image is primary
                    )
            
            messages.success(request, _('Product was added successfully.'))
            return redirect('suppliers:dashboard')
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = ProductForm()
    
    return render(request, 'suppliers/test_add_product.html', {
        'form': form,
        'categories': Category.objects.all(),
        'supplier': supplier
    })

@supplier_login_required
def bulk_delete_products(request):
    # If user is a superuser, they can delete any products
    if request.user.is_superuser:
        if request.method == 'POST':
            product_ids = request.POST.getlist('product_ids')
            if product_ids:
                products = Product.objects.filter(id__in=product_ids)
                products_count = products.count()
                products.delete()
                messages.success(request, _(f"{products_count} products were deleted successfully."))
            return redirect('shop:admin_products_explorer')
    else:
        # Regular supplier admin flow - use the supplier_required decorator's logic
        def _wrapped_view(request, *args, **kwargs):
            try:
                # Check if the user is a supplier admin
                supplier_admin = SupplierAdmin.objects.get(user=request.user)
                
                # Continue with the original view
                if request.method == 'POST':
                    product_ids = request.POST.getlist('product_ids')
                    if product_ids:
                        products = Product.objects.filter(id__in=product_ids, supplier=supplier_admin.supplier)
                        products_count = products.count()
                        products.delete()
                        messages.success(request, _(f"{products_count} products were deleted successfully."))
                    return redirect('suppliers:dashboard')
                
                return render(request, 'suppliers/bulk_delete_products.html')
                
            except SupplierAdmin.DoesNotExist:
                raise PermissionDenied(_("You must be a supplier admin to access this page."))
        
        return _wrapped_view(request)

@login_required
def send_supplier_invitation(request):
    """
    View for sending invitation emails to suppliers with a registration link
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        store_username = request.POST.get('store_username')
        supplier_name = request.POST.get('supplier_name')
        
        if not all([email, store_username, supplier_name]):
            messages.error(request, "All fields are required.")
            return render(request, 'suppliers/send_invitation.html')
        
        try:
            # Check if there's already an active invitation for this email
            existing_invitation = SupplierInvitation.objects.filter(
                email=email,
                is_used=False,
                status='pending'
            ).first()
            
            if existing_invitation:
                messages.error(request, "An active invitation already exists for this email.")
                return render(request, 'suppliers/send_invitation.html')
            
            # Create a new supplier
            supplier = Supplier.objects.create(
                name=supplier_name,
                email=email
            )
            
            # Create new invitation
            invitation = SupplierInvitation.objects.create(
                email=email,
                store_username=store_username,
                supplier=supplier
            )
            
            # Send the invitation email
            if invitation.send_invitation():
                messages.success(request, f"Invitation sent successfully to {email}")
                # Clear form by redirecting back to the same page
                return redirect('suppliers:send_invitation')
            else:
                messages.error(request, "Failed to send invitation email.")
                invitation.delete()
                supplier.delete()  # Clean up the supplier if email fails
                
        except Exception as e:
            messages.error(request, f"Error creating invitation: {str(e)}")
    
    return render(request, 'suppliers/send_invitation.html')

class ProductsExplorerView(SupplierLoginRequiredMixin, ListView):
    model = Product
    template_name = 'suppliers/products_explorer.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        # For superusers, show all products
        if self.request.user.is_superuser:
            supplier_id = self.request.GET.get('supplier_id')
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                    queryset = Product.objects.filter(supplier=supplier)
                except Supplier.DoesNotExist:
                    queryset = Product.objects.all()
            else:
                queryset = Product.objects.all()
        else:
            # Get the supplier admin for the current user
            try:
                supplier_admin = SupplierAdmin.objects.get(user=self.request.user)
                supplier = supplier_admin.supplier
            except SupplierAdmin.DoesNotExist:
                raise PermissionDenied("You don't have permission to access this page.")
            
            # Start with all products for this supplier
            queryset = Product.objects.filter(supplier=supplier)
        
        # Apply search filter
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(sku__icontains=query)
            )
        
        # Apply category filter
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Apply brand filter
        brand = self.request.GET.get('brand', '')
        if brand:
            queryset = queryset.filter(brand=brand)
        
        # Apply status filter
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'draft':
            queryset = queryset.filter(draft=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
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
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all categories
        context['categories'] = Category.objects.all()
        
        # Get all brands
        if self.request.user.is_superuser:
            supplier_id = self.request.GET.get('supplier_id')
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                    brands = Product.objects.filter(
                        supplier=supplier
                    ).exclude(
                        brand__isnull=True
                    ).exclude(
                        brand__exact=''
                    ).values_list('brand', flat=True).distinct()
                    context['suppliers'] = Supplier.objects.all()
                    context['current_supplier'] = supplier
                except Supplier.DoesNotExist:
                    brands = Product.objects.exclude(
                        brand__isnull=True
                    ).exclude(
                        brand__exact=''
                    ).values_list('brand', flat=True).distinct()
                    context['suppliers'] = Supplier.objects.all()
            else:
                brands = Product.objects.exclude(
                    brand__isnull=True
                ).exclude(
                    brand__exact=''
                ).values_list('brand', flat=True).distinct()
                context['suppliers'] = Supplier.objects.all()
        else:
            try:
                # Get unique brands from supplier's products
                supplier_admin = SupplierAdmin.objects.get(user=self.request.user)
                supplier = supplier_admin.supplier
                
                brands = Product.objects.filter(
                    supplier=supplier
                ).exclude(
                    brand__isnull=True
                ).exclude(
                    brand__exact=''
                ).values_list('brand', flat=True).distinct()
            except SupplierAdmin.DoesNotExist:
                brands = []
        
        context['brands'] = brands
        
        return context

@login_required
def direct_dashboard(request):
    """
    A simplified dashboard view that bypasses most permission checks.
    This is for debugging purposes only.
    """
    print("DEBUG: direct_dashboard called")
    print(f"DEBUG: User: {request.user.username}, is_superuser: {request.user.is_superuser}, is_supplier_admin: {getattr(request.user, 'is_supplier_admin', False)}")
    
    # Get all suppliers
    suppliers = Supplier.objects.all()
    print(f"DEBUG: Found {len(suppliers)} suppliers")
    
    # Get all products
    products = Product.objects.all()
    print(f"DEBUG: Found {len(products)} products")
    
    # Try to get supplier admin for this user
    supplier_admin = None
    supplier = None
    try:
        if hasattr(request.user, 'supplieradmin'):
            supplier_admin = request.user.supplieradmin
            supplier = supplier_admin.supplier
            print(f"DEBUG: Found supplier_admin: {supplier_admin}, supplier: {supplier}")
        else:
            supplier_admin_qs = SupplierAdmin.objects.filter(user=request.user)
            if supplier_admin_qs.exists():
                supplier_admin = supplier_admin_qs.first()
                supplier = supplier_admin.supplier
                print(f"DEBUG: Found supplier_admin via query: {supplier_admin}, supplier: {supplier}")
            else:
                print("DEBUG: No supplier_admin found for this user")
    except Exception as e:
        print(f"DEBUG: Error getting supplier_admin: {str(e)}")
    
    # Prepare minimal context
    context = {
        'products': products[:20],  # Limit to first 20
        'categories': Category.objects.all(),
        'total_products': products.count(),
        'total_sales': 0,
        'total_orders': 0,
        'is_superuser': request.user.is_superuser,
        'suppliers': suppliers,
    }
    
    # Add supplier if found
    if supplier:
        context['supplier'] = supplier
    
    print("DEBUG: Rendering dashboard template with minimal context")
    return render(request, 'suppliers/dashboard.html', context)

@login_required
def product_detail_api(request, product_id):
    """API endpoint to get product details in JSON format"""
    try:
        # Get the product
        if request.user.is_superuser:
            product = get_object_or_404(Product, id=product_id)
        else:
            try:
                supplier_admin = SupplierAdmin.objects.get(user=request.user)
                product = get_object_or_404(Product, id=product_id, supplier=supplier_admin.supplier)
            except SupplierAdmin.DoesNotExist:
                # If the user isn't a supplier admin but is still authenticated, just try to get the product
                product = get_object_or_404(Product, id=product_id)
        
        # Start with basic product data that should always be available
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price': str(product.price),
            'sku': product.sku or '',
            'is_active': product.is_active if hasattr(product, 'is_active') else True,
            'created_at': product.created_at.isoformat() if hasattr(product, 'created_at') else '',
        }
        
        # Add category information if available
        try:
            if hasattr(product, 'category') and product.category is not None:
                product_data['category'] = {
                    'id': product.category.id,
                    'name': product.category.name
                }
            else:
                product_data['category'] = {
                    'id': None,
                    'name': 'Uncategorized'
                }
        except Exception as e:
            print(f"Error getting category: {str(e)}")
            product_data['category'] = {'id': None, 'name': 'Uncategorized'}
        
        # Add supplier information if available
        try:
            if hasattr(product, 'supplier') and product.supplier is not None:
                product_data['supplier'] = {
                    'id': product.supplier.id,
                    'name': product.supplier.name
                }
            else:
                product_data['supplier'] = {
                    'id': None,
                    'name': 'Unknown'
                }
        except Exception as e:
            print(f"Error getting supplier: {str(e)}")
            product_data['supplier'] = {'id': None, 'name': 'Unknown'}
        
        # Add brand
        product_data['brand'] = product.brand if hasattr(product, 'brand') and product.brand else ''
        
        # Add brand image
        try:
            if hasattr(product, 'brand_image') and product.brand_image:
                current_site = request.build_absolute_uri('/').rstrip('/')
                brand_image_url = product.brand_image.url
                if not brand_image_url.startswith(('http://', 'https://')):
                    brand_image_url = f"{current_site}{brand_image_url}"
                product_data['brand_image'] = brand_image_url
            else:
                product_data['brand_image'] = None
        except Exception as e:
            print(f"Error getting brand image: {str(e)}")
            product_data['brand_image'] = None
        
        # Collect product attributes
        attributes = {}
        try:
            # Try to get product attributes from the ProductAttribute model directly
            product_attrs = ProductAttribute.objects.filter(product=product)
            for attr in product_attrs:
                attributes[attr.key] = attr.value
            product_data['attributes'] = attributes
        except Exception as e:
            print(f"Error getting product attributes: {str(e)}")
            product_data['attributes'] = {}
        
        # Collect product images
        images = []
        try:
            if hasattr(product, 'images'):
                for img in product.images.all().order_by('order'):
                    images.append({
                        'id': img.id,
                        'url': img.image.url,
                        'is_primary': img.is_primary if hasattr(img, 'is_primary') else False,
                        'order': img.order if hasattr(img, 'order') else 0
                    })
            product_data['images'] = images
        except Exception as e:
            print(f"Error getting product images: {str(e)}")
            product_data['images'] = []
        
        # Collect tags if available
        tags = []
        try:
            if hasattr(product, 'tags'):
                for tag in product.tags.all():
                    tags.append({
                        'id': tag.id,
                        'name': tag.name
                    })
            product_data['tags'] = tags
        except Exception as e:
            print(f"Error getting product tags: {str(e)}")
            product_data['tags'] = []
        
        return JsonResponse(product_data)
    except Exception as e:
        import traceback
        print(f"Error in product_detail_api: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)

def product_debug_api(request, product_id):
    """Simple debug API endpoint that returns minimal product information"""
    try:
        # Get the product without any permission checks
        product = get_object_or_404(Product, id=product_id)
        
        # Return only basic product data
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price': str(product.price),
            'success': True
        }
        
        return JsonResponse(product_data)
    except Exception as e:
        import traceback
        print(f"Error in product_debug_api: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@staff_member_required
def create_backup(request):
    """Create a new database backup"""
    try:
        # Create backup using management command
        call_command('backup_database', user=request.user.id)
        return JsonResponse({
            'status': 'success',
            'message': 'Backup started successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@staff_member_required
def get_backup_status(request):
    """Get the status of recent backups"""
    backups = BackupLog.objects.all().order_by('-started_at')[:10]
    backup_list = []
    
    for backup in backups:
        backup_list.append({
            'id': backup.id,
            'filename': backup.filename,
            'status': backup.status,
            'started_at': backup.started_at.isoformat(),
            'completed_at': backup.completed_at.isoformat() if backup.completed_at else None,
            'file_size': backup.file_size_display,
            'duration': str(backup.duration) if backup.duration else None,
            'error_message': backup.error_message
        })
    
    return JsonResponse({
        'status': 'success',
        'backups': backup_list
    })

@staff_member_required
def download_backup(request, backup_id):
    """Download a backup file"""
    try:
        backup = BackupLog.objects.get(id=backup_id)
        backup_path = os.path.join(settings.BASE_DIR, 'backups', backup.filename)
        
        if not os.path.exists(backup_path):
            return JsonResponse({
                'status': 'error',
                'message': 'Backup file not found'
            }, status=404)
        
        with open(backup_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{backup.filename}"'
            return response
            
    except BackupLog.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Backup not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@staff_member_required
def backup_dashboard(request):
    """Render the backup dashboard"""
    return render(request, 'admin/backup_dashboard.html')

@login_required
def delete_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        # Get the deletion reason from the form
        deletion_reason = request.POST.get('deletion_reason', '')
        
        # Delete the supplier using the new method
        supplier.delete(deleted_by=request.user, deletion_reason=deletion_reason)
        
        messages.success(request, 'تامین‌کننده با موفقیت حذف شد.')
        return redirect('suppliers:supplier_list')
    
    return render(request, 'suppliers/delete_supplier.html', {
        'supplier': supplier
    })
