# admin.py
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django import forms
from .models import (
    Category, Product, ProductAttribute, ProductImage, Order, OrderItem, Tag, 
    Attribute, ProductAttributeValue, NewAttributeValue, CategoryAttribute, AttributeValue,
    DeletedProduct, Wishlist
)
from .forms import ProductForm, TagForm
from suppliers.models import SupplierAdmin, User as SupplierUser
from myshop.admin import admin_site
from .models import persian_slugify
from django.utils.html import format_html, mark_safe

# Custom form to allow editing Category ID
class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'label': forms.TextInput(attrs={
                'placeholder': 'نام نمایشی (مثل: ساعت برای ساعت مردانه)',
                'help_text': 'نام تمیز برای نمایش در اپ'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the id field editable
        if 'id' not in self.fields:
            self.fields['id'] = forms.IntegerField(
                initial=self.instance.pk if self.instance.pk else None,
                required=False,
                help_text="Change the ID carefully - this affects all related data"
            )
        
        # Add helpful descriptions for category types
        if 'category_type' in self.fields:
            self.fields['category_type'].help_text = """
            <strong>Category Types:</strong><br>
            • <strong>Auto-detect:</strong> Automatically determine based on content (recommended)<br>
            • <strong>Container:</strong> Has subcategories, no direct products (e.g., "ساعت" with "ساعت مردانه", "ساعت زنانه")<br>
            • <strong>Direct:</strong> Has products directly, no subcategories (e.g., "کتاب", "لوازم التحریر")
            """
            self.fields['category_type'].widget.attrs.update({
                'style': 'width: 100%;'
            })
        
        # Add helpful description for display section
        if 'display_section' in self.fields:
            self.fields['display_section'].help_text = """
            <strong>Display Sections:</strong><br>
            • <strong>Men:</strong> Show in men's section<br>
            • <strong>Women:</strong> Show in women's section<br>
            • <strong>Unisex:</strong> Show in unisex section<br>
            • <strong>General:</strong> Show in general section (default)
            """

# New flexible attribute system admins
class AttributeValueInline(admin.TabularInline):
    model = NewAttributeValue
    extra = 1
    fields = ['value', 'display_order', 'color_code']
    ordering = ['display_order', 'value']

class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'type', 'is_filterable', 'display_order')
    list_filter = ('type', 'is_filterable')
    search_fields = ('name', 'key')
    ordering = ('display_order', 'name')
    inlines = [AttributeValueInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'key', 'type')
        }),
        ('تنظیمات', {
            'fields': ('description', 'is_filterable', 'display_order')
        }),
    )

class NewAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'display_order', 'color_code')
    list_filter = ('attribute__type', 'attribute')
    search_fields = ('value', 'attribute__name')
    ordering = ['attribute__name', 'display_order']
    list_editable = ('display_order',)

# Inline for ProductImages in ProductAdmin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'order']
    max_num = 10  # محدودیت تعداد تصاویر
    validate_max = True  # اعمال محدودیت
    ordering = ['order']  # مرتب‌سازی بر اساس فیلد order
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        form = formset.form
        
        # اضافه کردن اعتبارسنجی برای فیلد order
        original_clean = form.clean
        
        def clean(self):
            cleaned_data = original_clean(self)
            if 'order' in cleaned_data:
                order = cleaned_data['order']
                if order > 10:
                    raise ValidationError(_('شماره ترتیب نمی‌تواند بیشتر از 10 باشد'))
            return cleaned_data
        
        form.clean = clean
        return formset

class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('id', 'name', 'label', 'parent', 'is_container', 'get_product_count', 'get_attribute_count')
    search_fields = ('name', 'label', 'id')
    list_filter = ('parent', 'category_type')
    inlines = []  # Removed CategoryAttributeInline
    fields = ('id', 'name', 'label', 'parent', 'category_type', 'is_visible', 'display_section')
    
    def get_attribute_count(self, obj):
        if obj.is_subcategory():
            return obj.category_attributes.count()
        return '-'
    get_attribute_count.short_description = 'تعداد ویژگی‌ها'
    
    def is_container(self, obj):
        """Show if this is a container category (boolean)"""
        return obj.is_container_category()
    is_container.boolean = True
    is_container.short_description = 'Container'
    
    def get_product_count(self, obj):
        """Show total product count for this category"""
        count = obj.get_product_count()
        return count if count > 0 else '-'
    get_product_count.short_description = 'تعداد محصولات'
    
    def analyze_category_structure(self, request, queryset):
        """Admin action to analyze and display category structure"""
        from django.contrib import messages
        
        for category in queryset:
            has_subcategories = category.subcategories.exists()
            has_direct_products = category.product_set.filter(is_active=True).exists()
            effective_type = category.get_effective_category_type()
            
            message = f"""
            <strong>{category.name}</strong> (ID: {category.id})<br>
            • Has subcategories: {has_subcategories}<br>
            • Has direct products: {has_direct_products}<br>
            • Current type: {category.category_type}<br>
            • Effective type: {effective_type}<br>
            • Product count: {category.get_product_count()}
            """
            messages.info(request, mark_safe(message))
        
        self.message_user(request, f"Analyzed {queryset.count()} categories. Check the messages above for details.")
    analyze_category_structure.short_description = "Analyze category structure and detection logic"
    
    actions = ['analyze_category_structure']

class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'value')
    list_filter = ('key',)
    search_fields = ('product__name', 'key', 'value')

class TagAdmin(admin.ModelAdmin):
    form = TagForm
    list_display = ('name', 'slug', 'get_categories')
    search_fields = ('name', 'slug')
    filter_horizontal = ('categories',)
    list_filter = ('categories',)
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle slug generation for Persian text
        """
        if not obj.slug:
            # Use our custom persian_slugify function
            obj.slug = persian_slugify(obj.name)
            # If slug is empty (all Persian chars), create a unique ID
            if not obj.slug:
                import random
                # Generate a random ID based on the name and a random number
                name_hash = hash(obj.name) % 10000
                random_part = random.randint(1000, 9999)
                obj.slug = f"tag-{name_hash}-{random_part}"
        super().save_model(request, obj, form, change)
    
    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = 'Categories'

class ProductAdmin(admin.ModelAdmin):
    class Media:
        js = ('shop/js/product_detail_sidebar.js', 'shop/js/product_tags.js')
        css = {
            'all': ('shop/css/product_detail_sidebar.css',)
        }

    list_display = ('name', 'price_toman', 'price_usd', 'category', 'is_active', 'is_new_arrival')
    list_filter = ('category', 'is_active', 'is_new_arrival')
    search_fields = ('name', 'description')
    readonly_fields = ['created_at']
    inlines = [ProductImageInline]
    form = ProductForm
    change_form_template = 'admin/shop/product/change_form.html'
    change_list_template = 'admin/shop/product/changelist.html'
    delete_confirmation_template = 'admin/shop/product/delete_confirmation.html'
    filter_horizontal = ('tags',)
    autocomplete_fields = ['category']

    def get_available_attributes_count(self, obj):
        """Show how many attributes are available for this product's category"""
        if obj.category and obj.category.is_subcategory():
            return obj.get_available_attributes().count()
        return 0
    get_available_attributes_count.short_description = 'ویژگی‌های قابل استفاده'

    def response_delete(self, request, obj_display, obj_id):
        """Override to redirect to custom admin products page after deletion"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        # Redirect to custom admin products page
        return HttpResponseRedirect(reverse('shop:admin_products_explorer'))

    def delete_model(self, request, obj):
        """Override to set the current user before deletion"""
        obj._current_user = request.user
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Override to set the current user before bulk deletion"""
        for obj in queryset:
            obj._current_user = request.user
        super().delete_queryset(request, queryset)

    def custom_edit_link(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        
        # Generate URL to custom edit page
        custom_edit_url = f"{reverse('suppliers:add_product')}?product_id={obj.id}"
        
        # Return an HTML link button
        return format_html('<a href="{}" class="button" style="background-color: #6c5ce7; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">ویرایش محصول</a>', 
                         custom_edit_url)
    
    custom_edit_link.short_description = 'ویرایش'
    custom_edit_link.allow_tags = True

    def response_change(self, request, obj):
        """Override to redirect to custom edit page after viewing a product"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        # Get the custom edit URL
        custom_edit_url = f"{reverse('suppliers:add_product')}?product_id={obj.id}"
        
        # Redirect to custom edit page
        return HttpResponseRedirect(custom_edit_url)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override to redirect to custom edit page when viewing a product"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        # Get the custom edit URL
        custom_edit_url = f"{reverse('suppliers:add_product')}?product_id={object_id}"
        
        # Redirect to custom edit page
        return HttpResponseRedirect(custom_edit_url)

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if isinstance(list_display, (list, tuple)):
            list_display = list(list_display)
            if 'quick_edit' in list_display:
                list_display.remove('quick_edit')
        return list_display

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'quick_edit' in actions:
            del actions['quick_edit']
        return actions

    def get_urls(self):
        urls = super().get_urls()
        # Filter out any quick edit related URLs
        urls = [url for url in urls if 'quick-edit' not in str(url.pattern)]
        return urls

    def display_supplier(self, obj):
        if obj.supplier:
            return obj.supplier.name
        return format_html('Unknown Supplier <span style="color: red; font-weight: bold;">[Deleted]</span>')
    display_supplier.short_description = 'تامین‌کننده'
    display_supplier.admin_order_field = 'supplier__name'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if isinstance(request.user, SupplierUser) and SupplierAdmin.objects.filter(user=request.user, is_active=True).exists():
            supplier_admin = SupplierAdmin.objects.get(user=request.user)
            return qs.filter(supplier=supplier_admin.supplier)
        elif not isinstance(request.user, SupplierUser):
            import logging
            logging.warning(f"[ProductAdmin] request.user is not a SupplierUser instance: {request.user} ({type(request.user)})")
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if isinstance(request.user, SupplierUser) and SupplierAdmin.objects.filter(user=request.user, is_active=True).exists():
            supplier_admin = SupplierAdmin.objects.get(user=request.user)
            if 'supplier' in form.base_fields:
                form.base_fields['supplier'].initial = supplier_admin.supplier
                form.base_fields['supplier'].disabled = True
        elif not isinstance(request.user, SupplierUser):
            import logging
            logging.warning(f"[ProductAdmin] request.user is not a SupplierUser instance: {request.user} ({type(request.user)})")
        return form

    def save_model(self, request, obj, form, change):
        if not obj.supplier and isinstance(request.user, SupplierUser) and SupplierAdmin.objects.filter(user=request.user, is_active=True).exists():
            supplier_admin = SupplierAdmin.objects.get(user=request.user)
            obj.supplier = supplier_admin.supplier
        elif not isinstance(request.user, SupplierUser):
            import logging
            logging.warning(f"[ProductAdmin] request.user is not a SupplierUser instance: {request.user} ({type(request.user)})")
        super().save_model(request, obj, form, change)
            
        # Remove existing legacy attributes on edit
        if change:
            obj.legacy_attribute_set.all().delete()

        # Save only submitted and non-empty legacy attributes
        for key, value in request.POST.items():
            if key.startswith('attr_') and value.strip():
                attr_key = key.replace('attr_', '')
                
                # Check if this is a flexible attribute
                if obj.category and obj.category.is_subcategory():
                    try:
                        # Try to find the attribute in the flexible system
                        attribute = Attribute.objects.get(key=attr_key)
                        # This is a flexible attribute, save it properly
                        obj.set_attribute_value(attr_key, value)
                        continue
                    except Attribute.DoesNotExist:
                        pass
                
                # Fall back to legacy system
                ProductAttribute.objects.create(
                    product=obj,
                    key=attr_key,
                    value=value
                )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            ProductImage.create(
                product=form.instance,
                image=image,
                order=i  # Set the order based on the index
            )


    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['is_add_view'] = True
        return super().add_view(request, form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        # Get all suppliers for the dropdown
        from suppliers.models import Supplier
        suppliers = Supplier.objects.all().order_by('name')
        
        # Get selected supplier if any
        selected_supplier = request.GET.get('supplier', '')
        
        # Add to context
        extra_context = extra_context or {}
        extra_context.update({
            'suppliers': suppliers,
            'selected_supplier': selected_supplier,
        })
        
        # Apply supplier filter directly to the request
        if selected_supplier:
            # Store the original queryset method
            original_get_queryset = self.get_queryset
            
            # Define a new method that will filter by supplier
            def filtered_queryset(request):
                return original_get_queryset(request).filter(supplier_id=selected_supplier)
                
            # Temporarily replace the get_queryset method
            # Have to use types.MethodType to properly bind the method to the instance
            import types
            self.get_queryset = types.MethodType(lambda self, request: filtered_queryset(request), self)
            
            # Call parent changelist_view
            response = super().changelist_view(request, extra_context=extra_context)
            
            # Restore the original method
            self.get_queryset = original_get_queryset
            
            return response
        else:
            # No supplier filter, just call parent method
            return super().changelist_view(request, extra_context=extra_context)

    def get_brand_image(self, obj):
        if obj.brand_image:
            return mark_safe(f'<img src="{obj.brand_image.url}" width="50" height="50" />')
        return "No image"
    get_brand_image.short_description = 'تصویر برند'

    def mark_as_new_arrival(self, request, queryset):
        """Admin action to mark selected products as new arrivals"""
        updated = queryset.update(is_new_arrival=True)
        self.message_user(request, f'{updated} محصول به عنوان "محصول جدید" علامت‌گذاری شد.')
    mark_as_new_arrival.short_description = 'علامت‌گذاری به عنوان محصول جدید'

    def unmark_as_new_arrival(self, request, queryset):
        """Admin action to remove new arrival status from selected products"""
        updated = queryset.update(is_new_arrival=False)
        self.message_user(request, f'علامت "محصول جدید" از {updated} محصول حذف شد.')
    unmark_as_new_arrival.short_description = 'حذف علامت محصول جدید'

    actions = ['mark_as_new_arrival', 'unmark_as_new_arrival']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'category', 'tags', 'is_active', 'is_new_arrival')
        }),
        ('قیمت‌گذاری', {
            'fields': ('price_toman', 'price_usd', 'price', 'price_currency')
        }),
        ('اطلاعات فنی', {
            'fields': ('weight', 'dimensions', 'warranty', 'stock_quantity')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('supplier', 'created_at')
        }),
    )

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'order' in form.base_fields:
            form.base_fields['order'].help_text = 'شماره ترتیب باید بین 1 تا 10 باشد'
            form.base_fields['order'].validators.append(
                lambda value: ValidationError('شماره ترتیب نمی‌تواند بیشتر از 10 باشد') if value > 10 else None
            )
        return form

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email',
                   'address', 'postal_code', 'city', 'paid',
                   'created', 'updated']
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline]
    search_fields = ['first_name', 'last_name', 'email']

# Move these admin classes up before any registration calls:
class AttributeValueInlineForCategory(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ['value', 'display_order']
    ordering = ['display_order', 'value']

class CategoryAttributeAdmin(admin.ModelAdmin):
    list_display = ('category', 'key', 'label_fa', 'type', 'required', 'display_order')
    list_filter = ('category', 'type', 'required')
    search_fields = ('key', 'label_fa', 'category__name')
    ordering = ('category', 'display_order', 'key')
    inlines = [AttributeValueInlineForCategory]
    fields = ('category', 'key', 'label_fa', 'type', 'required', 'display_order')

class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'display_order')
    list_filter = ('attribute',)
    search_fields = ('value', 'attribute__key')
    ordering = ['attribute__key', 'display_order']
    list_editable = ('display_order',)


class DeletedProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'original_id', 'category_name', 'supplier_name', 'deleted_at', 'deleted_by')
    list_filter = ('deleted_at', 'category_name', 'supplier_name')
    search_fields = ('name', 'original_id')
    readonly_fields = ('original_id', 'name', 'price_toman', 'price_usd', 'description', 
                      'category_name', 'supplier_name', 'sku', 'deleted_at')
    ordering = ['-deleted_at']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of deleted product records


class WishlistAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'created_at')
    list_filter = ('created_at', 'product__category')
    search_fields = ('customer__email', 'customer__first_name', 'customer__last_name', 'product__name')
    readonly_fields = ('created_at',)
    ordering = ['-created_at']
    
    def get_customer_display(self, obj):
        return obj.customer.get_full_name() or obj.customer.email
    get_customer_display.short_description = 'مشتری'
    get_customer_display.admin_order_field = 'customer__first_name'

# Register models with our custom admin site
admin_site.register(Category, CategoryAdmin)
admin_site.register(ProductAttribute, ProductAttributeAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(ProductImage, ProductImageAdmin)
admin_site.register(Order, OrderAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Wishlist, WishlistAdmin)

# New flexible attribute system models
admin_site.register(Attribute, AttributeAdmin)
admin_site.register(NewAttributeValue, NewAttributeValueAdmin)
admin_site.register(CategoryAttribute, CategoryAttributeAdmin)
admin_site.register(AttributeValue)
admin_site.register(DeletedProduct, DeletedProductAdmin)

# Also register with default admin site
admin.site.register(Category, CategoryAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage, ProductImageAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Wishlist, WishlistAdmin)

# New flexible attribute system models on default admin
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(NewAttributeValue, NewAttributeValueAdmin)
admin.site.register(AttributeValue, AttributeValueAdmin)
admin.site.register(DeletedProduct, DeletedProductAdmin)

# Also register with custom admin site if available
try:
    admin_site.register(Category, CategoryAdmin)
    admin_site.register(Product, ProductAdmin)
    admin_site.register(ProductAttribute, ProductAttributeAdmin)
    admin_site.register(ProductImage, ProductImageAdmin)
    admin_site.register(Order, OrderAdmin)
    admin_site.register(Tag, TagAdmin)
    admin_site.register(DeletedProduct, DeletedProductAdmin)
except:
    pass
