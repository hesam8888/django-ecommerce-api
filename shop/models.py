from django.db import models
from django.core.validators import FileExtensionValidator
from suppliers.models import Supplier
from django.utils.text import slugify
from django.utils import timezone
import re
import uuid
import random
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import gettext_lazy as _
# Use Django's built-in JSONField for compatibility with both SQLite and PostgreSQL
from django.db.models import JSONField


class Category(models.Model):
    CATEGORY_TYPES = [
        ('container', 'Container Category'),  # Has subcategories, no direct products
        ('direct', 'Direct Category'),        # Has products directly, no subcategories  
        ('auto', 'Auto-detect'),             # Automatically determine based on content
    ]
    
    DISPLAY_SECTIONS = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    label = models.CharField(max_length=100, blank=True, verbose_name='Display Label', help_text='Clean display name for frontend (e.g., "ساعت" for "ساعت مردانه")')
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='auto', help_text='Category behavior type')
    is_visible = models.BooleanField(default=True, verbose_name='Visible in App', help_text='Show this category in the mobile app')
    display_section = models.CharField(max_length=20, choices=DISPLAY_SECTIONS, null=True, blank=True, verbose_name='Display Section', help_text='Which section to show this category in (men/women/general)')
    
    def __str__(self):
        return self.name

    def is_subcategory(self):
        """Check if this category is a subcategory (has a parent)"""
        return self.parent is not None

    def get_all_subcategories(self):
        """Get all subcategories recursively"""
        subcategories = list(self.subcategories.all())
        for subcategory in list(subcategories):
            subcategories.extend(subcategory.get_all_subcategories())
        return subcategories
    
    def get_display_name(self):
        """Get the display label if available, otherwise return name"""
        return self.label if self.label else self.name
    
    def get_gender(self):
        """Extract gender from category name"""
        if 'مردانه' in self.name:
            return 'مردانه'
        elif 'زنانه' in self.name:
            return 'زنانه'
        elif 'یونیسکس' in self.name:
            return 'یونیسکس'
        return None

    def get_effective_category_type(self):
        """Get the effective category type (resolve 'auto' type)"""
        if self.category_type != 'auto':
            return self.category_type
        
        # Auto-detection logic
        has_subcategories = self.subcategories.exists()
        has_direct_products = self.product_set.filter(is_active=True).exists()
        
        if has_subcategories and not has_direct_products:
            return 'container'
        elif not has_subcategories and has_direct_products:
            return 'direct'
        elif has_subcategories and has_direct_products:
            # Mixed case - default to container
            return 'container'
        else:
            # No products and no subcategories - default to direct
            return 'direct'
    
    def is_container_category(self):
        """Check if this is a container category (has subcategories, no direct products)"""
        return self.get_effective_category_type() == 'container'
    
    def is_direct_category(self):
        """Check if this is a direct category (has products directly)"""
        return self.get_effective_category_type() == 'direct'
    
    def get_all_products(self):
        """Get all products for this category, handling both container and direct types"""
        if self.is_container_category():
            # Get products from all subcategories
            all_subcategories = self.get_all_subcategories()
            from django.db.models import Q
            query = Q(category=self)
            for subcat in all_subcategories:
                query |= Q(category=subcat)
            return self.product_set.model.objects.filter(query, is_active=True)
        else:
            # Get products directly from this category
            return self.product_set.filter(is_active=True)
    
    def get_product_count(self):
        """Get total product count for this category"""
        return self.get_all_products().count()
        
    def get_subcategory_product_counts(self):
        """Get product counts for each subcategory"""
        counts = {}
        for subcat in self.subcategories.all():
            counts[subcat.id] = subcat.get_product_count()
        return counts
    
    def get_display_section(self):
        """Get the display section, auto-detect if not set"""
        if self.display_section:
            return self.display_section
        
        # Auto-detect based on gender
        gender = self.get_gender()
        if gender == 'مردانه':
            return 'men'
        elif gender == 'زنانه':
            return 'women'
        elif gender == 'یونیسکس':
            return 'unisex'
        else:
            return 'general'


class Attribute(models.Model):
    """Reusable attributes that can be assigned to multiple categories"""
    ATTRIBUTE_TYPES = [
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Single Selection'),
        ('multiselect', 'Multiple Selection'),
        ('boolean', 'Yes/No'),
        ('color', 'Color Picker'),
        ('size', 'Size Selection')
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='نام ویژگی')
    key = models.CharField(max_length=100, unique=True, verbose_name='کلید ویژگی',
                          help_text='کلید یکتا برای استفاده در API (مثل: color, size)')
    type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPES, default='select',
                           verbose_name='نوع ویژگی',
                           help_text='نوع تعیین می‌کند که این ویژگی چگونه در فرم‌ها نمایش داده شود')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    is_filterable = models.BooleanField(default=True, verbose_name='قابل فیلتر',
                                       help_text='آیا این ویژگی در فیلترهای جستجو نمایش داده شود؟')
    display_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    
    class Meta:
        verbose_name = 'ویژگی'
        verbose_name_plural = 'ویژگی‌ها'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class NewAttributeValue(models.Model):
    """Values for each attribute"""
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values',
                                 verbose_name='ویژگی')
    value = models.CharField(max_length=100, verbose_name='مقدار')
    display_order = models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')
    color_code = models.CharField(max_length=7, blank=True, null=True, verbose_name='کد رنگ',
                                 help_text='کد رنگ hex برای ویژگی‌های رنگی (مثل: #FF0000)')
    
    class Meta:
        unique_together = ('attribute', 'value')
        ordering = ['display_order', 'value']
        verbose_name = 'مقدار ویژگی'
        verbose_name_plural = 'مقادیر ویژگی'
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductAttributeValue(models.Model):
    """Flexible relation between products and attribute values"""
    product = models.ForeignKey('Product', on_delete=models.CASCADE,
                               related_name='attribute_values',
                               verbose_name='محصول')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE,
                                 verbose_name='ویژگی')
    attribute_value = models.ForeignKey(NewAttributeValue, on_delete=models.CASCADE,
                                       blank=True, null=True,
                                       verbose_name='مقدار ویژگی',
                                       help_text='برای ویژگی‌های از پیش تعریف شده')
    custom_value = models.CharField(max_length=255, blank=True, null=True,
                                   verbose_name='مقدار سفارشی',
                                   help_text='برای ویژگی‌های متنی یا عددی')
    
    class Meta:
        unique_together = ('product', 'attribute')
        verbose_name = 'مقدار ویژگی محصول'
        verbose_name_plural = 'مقادیر ویژگی محصول'
    
    def __str__(self):
        value = self.attribute_value.value if self.attribute_value else self.custom_value
        return f"{self.product.name} - {self.attribute.name}: {value}"
    
    def get_display_value(self):
        """Get the display value for this attribute"""
        if self.attribute_value:
            return self.attribute_value.value
        return self.custom_value or ''

    def clean(self):
        """Validate that either attribute_value or custom_value is provided"""
        from django.core.exceptions import ValidationError
        
        if not self.attribute_value and not self.custom_value:
            raise ValidationError('Either attribute_value or custom_value must be provided.')
        
        if self.attribute_value and self.custom_value:
            raise ValidationError('Only one of attribute_value or custom_value should be provided.')


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='tags', blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            # Try to generate a slug from Persian characters
            self.slug = persian_slugify(self.name)
            # If slug is empty (all Persian chars), create a unique ID
            if not self.slug:
                # Generate a random ID based on the name and a random number
                name_hash = hash(self.name) % 10000
                random_part = random.randint(1000, 9999)
                self.slug = f"tag-{name_hash}-{random_part}"
        super().save(*args, **kwargs)

def persian_slugify(text):
    """
    Custom slugify function that works with Persian text.
    For Persian text, it generates a transliterated version when possible,
    or falls back to a unique ID if no Latin chars are available.
    """
    # First try the normal slugify for any Latin characters
    slug = slugify(text)
    
    # If there are Latin characters or numbers, use them
    if slug:
        return slug
        
    # For pure Persian text, create a cleaned version without spaces
    # Remove any non-alphanumeric or space characters
    persian_slug = re.sub(r'[^\w\s]', '', text)
    # Replace spaces with dashes
    persian_slug = re.sub(r'\s+', '-', persian_slug.strip())
    
    # If we still have content, return it
    if persian_slug:
        return persian_slug
        
    # Last resort: return empty and let save() handle it
    return ""


class Product(models.Model):
    CURRENCY_CHOICES = [
        ('TOMAN', 'تومان'),
        ('USD', 'دلار')
    ]

    name = models.CharField(max_length=100, verbose_name='نام محصول')
    # Price in Toman (required)
    price_toman = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='قیمت (تومان)', default=0)
    # Price in USD (optional)
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='قیمت (دلار)')
    
    # Keep this for backward compatibility, but it will be deprecated
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='قیمت', null=True, blank=True)
    price_currency = models.CharField(
        max_length=5,
        choices=CURRENCY_CHOICES,
        default='TOMAN',
        verbose_name='واحد پول',
        null=True, blank=True
    )
    
    description = models.TextField(blank=True, verbose_name='توضیحات')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1, verbose_name='دسته‌بندی')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products', null=True, blank=True, verbose_name='تامین‌کننده')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', verbose_name='برچسب‌ها')
    
    # Entity fields
    model = models.CharField(max_length=100, blank=True, verbose_name='مدل')
    sku = models.CharField(max_length=50, blank=True, verbose_name='کد محصول')
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='وزن (گرم)')
    dimensions = models.CharField(max_length=100, blank=True, verbose_name='ابعاد (سانتیمتر)')
    warranty = models.CharField(max_length=100, blank=True, verbose_name='گارانتی')
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='تعداد موجودی')
    is_new_arrival = models.BooleanField(default=False, verbose_name='جدید / محصول جدید')

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_formatted_price(self):
        """Returns the formatted price with currency symbol - for backward compatibility"""
        # Try to use the new price fields first
        if hasattr(self, 'price_toman') and self.price_toman is not None:
            return f"{self.price_toman:,.0f} تومان"
        elif self.price_currency == 'TOMAN' and self.price:
            return f"{self.price:,.0f} تومان"
        elif self.price_currency == 'USD' and self.price:
            return f"${self.price:,.2f}"
        elif hasattr(self, 'price_usd') and self.price_usd is not None:
            return f"${self.price_usd:,.2f}"
        else:
            return "قیمت تعیین نشده"
    
    def get_formatted_toman_price(self):
        """Returns the formatted Toman price"""
        if hasattr(self, 'price_toman') and self.price_toman is not None:
            return f"{self.price_toman:,.0f} تومان"
        return "قیمت تعیین نشده"
        
    def get_formatted_usd_price(self):
        """Returns the formatted USD price if available"""
        if hasattr(self, 'price_usd') and self.price_usd is not None:
            return f"${self.price_usd:,.2f}"
        return "قیمت دلاری تعیین نشده"

    def get_available_attributes(self):
        """Get all attributes available for this product based on its category"""
        if not self.category or not self.category.is_subcategory():
            return Attribute.objects.none()
        
        return Attribute.objects.filter(
            assigned_subcategories__subcategory=self.category
        ).distinct().order_by('display_order', 'name')

    def get_attribute_value(self, attribute_key):
        """Get the value of a specific attribute for this product"""
        try:
            attribute = Attribute.objects.get(key=attribute_key)
            product_attr = self.attribute_values.get(attribute=attribute)
            return product_attr.get_display_value()
        except (Attribute.DoesNotExist, ProductAttributeValue.DoesNotExist):
            return None

    def set_attribute_value(self, attribute_key, value):
        """Set the value of a specific attribute for this product"""
        try:
            attribute = Attribute.objects.get(key=attribute_key)
            
            # Get or create the ProductAttributeValue
            product_attr, created = ProductAttributeValue.objects.get_or_create(
                product=self,
                attribute=attribute,
                defaults={}
            )
            
            # Try to find a matching NewAttributeValue first
            try:
                attribute_value = NewAttributeValue.objects.get(attribute=attribute, value=value)
                product_attr.attribute_value = attribute_value
                product_attr.custom_value = None
            except NewAttributeValue.DoesNotExist:
                # Use custom value if no predefined value exists
                product_attr.attribute_value = None
                product_attr.custom_value = value
            
            product_attr.save()
            return product_attr
            
        except Attribute.DoesNotExist:
            raise ValueError(f"Attribute with key '{attribute_key}' does not exist")

    def get_attributes_dict(self):
        """Get all attribute values as a dictionary"""
        attributes = {}
        for attr_value in self.attribute_values.select_related('attribute', 'attribute_value'):
            attributes[attr_value.attribute.key] = attr_value.get_display_value()
        return attributes

    @classmethod
    def get_new_arrivals(cls, limit=None):
        """Get products marked as new arrivals"""
        queryset = cls.objects.filter(is_new_arrival=True, is_active=True).order_by('-created_at')
        if limit:
            queryset = queryset[:limit]
        return queryset

    def mark_as_new_arrival(self):
        """Mark this product as a new arrival"""
        self.is_new_arrival = True
        self.save(update_fields=['is_new_arrival'])

    def unmark_as_new_arrival(self):
        """Remove new arrival status from this product"""
        self.is_new_arrival = False
        self.save(update_fields=['is_new_arrival'])

    def save(self, *args, **kwargs):
        # Check if category is being changed
        if self.pk:  # Only for existing products
            try:
                old_product = Product.objects.get(pk=self.pk)
                if old_product.category_id != self.category_id:
                    # Category has changed, clean up invalid attributes
                    self._cleanup_attributes_on_category_change()
            except Product.DoesNotExist:
                pass  # New product, no cleanup needed
        
        # Migration: Move data from old price field to new ones
        if self.price is not None and self.price_toman == 0:  # If price_toman is default but price exists
            if self.price_currency == 'TOMAN' or self.price_currency is None:
                self.price_toman = self.price
            elif self.price_currency == 'USD' and self.price_usd is None:
                self.price_usd = self.price
                # We should still set a reasonable toman price
                # This is a placeholder, ideally use a conversion rate
                self.price_toman = self.price * 50000  # Example conversion rate, adjust as needed
        
        # Ensure old price field is synced for compatibility
        if not self.price or self.price != self.price_toman:
            self.price = self.price_toman
            self.price_currency = 'TOMAN'
            
        super(Product, self).save(*args, **kwargs)

    def _cleanup_attributes_on_category_change(self):
        """Remove invalid attributes when category changes"""
        if not self.category:
            return
            
        # Get valid attribute keys for the new category
        valid_keys = set(self.category.category_attributes.values_list('key', flat=True))
        
        # Find and remove invalid attributes
        invalid_attributes = self.legacy_attribute_set.exclude(key__in=valid_keys)
        removed_count = invalid_attributes.count()
        
        if removed_count > 0:
            invalid_attributes.delete()
            print(f"Cleaned up {removed_count} invalid attributes for product {self.name} when category changed to {self.category.name}")

    def delete(self, *args, **kwargs):
        # Create a record in DeletedProduct before deleting
        try:
            # Get the current user from the request if available
            deleted_by = None
            if hasattr(self, '_current_user'):
                deleted_by = self._current_user
            
            DeletedProduct.objects.create(
                original_id=self.id,
                name=self.name,
                price_toman=self.price_toman,
                price_usd=self.price_usd,
                description=self.description,
                category_name=self.category.name if self.category else '',
                supplier_name=self.supplier.name if self.supplier else '',
                model=self.model,
                sku=self.sku,
                deletion_reason=kwargs.get('deletion_reason', ''),
                deleted_by=deleted_by
            )
        except Exception as e:
            # Log the error but don't prevent deletion
            print(f"Failed to create DeletedProduct record: {e}")
        
        super().delete(*args, **kwargs)


class ProductAttribute(models.Model):
    """Legacy model - use ProductAttributeValue instead"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='legacy_attribute_set')
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Product Attribute (Legacy)'
        verbose_name_plural = 'Product Attributes (Legacy)'

    def __str__(self):
        return f'{self.key}: {self.value}'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    image_hash = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        ordering = ['-is_primary', 'order', 'created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'order'],
                name='unique_product_image_order'
            )
        ]

    def __str__(self):
        return f"Image for {self.product.name}"

    def calculate_image_hash(self):
        """Calculate a hash of the image content to identify duplicates"""
        import hashlib
        if not self.image:
            return None
            
        try:
            # Read image content
            self.image.seek(0)
            image_content = self.image.read()
            # Calculate SHA-256 hash
            hash_object = hashlib.sha256(image_content)
            hex_dig = hash_object.hexdigest()
            # Reset file pointer
            self.image.seek(0)
            return hex_dig
        except Exception as e:
            print(f"Error calculating image hash: {e}")
            return None

    def _compress_image(self):
        """Compress the image if it's not already in webp format"""
        if not self.image:
            return
            
        # Skip compression if already in webp format
        if hasattr(self.image, 'name') and self.image.name.lower().endswith('.webp'):
            print(f"Skipping compression - already in webp format: {self.image.name}")
            return
            
        print(f"Compressing image: {getattr(self.image, 'name', 'unnamed')}")
        
        try:
            from .utils import compress_image
            # Compress the image
            self.image = compress_image(self.image)
            print(f"Compression complete: {self.image.name}")
        except Exception as e:
            print(f"Error during compression: {e}")

    def save(self, *args, **kwargs):
        # Check if compress parameter was passed
        compress = kwargs.pop('compress', True)
        
        # For new images or when image has changed
        is_new = self.pk is None
        
        # Calculate hash before compression if it's not already set
        if is_new and not self.image_hash:
            self.image_hash = self.calculate_image_hash()
        
        # Check for duplicate images by hash
        if is_new and self.image_hash:
            duplicate = ProductImage.objects.filter(
                product=self.product,
                image_hash=self.image_hash
            ).first()
            
            if duplicate:
                print(f"Duplicate image detected with hash: {self.image_hash}")
                # Instead of creating a duplicate, return the existing one
                return duplicate
        
        # Compress the image if requested and if it's new
        if compress and is_new:
            self._compress_image()
            
        # Recalculate hash if compression was applied
        if not self.image_hash:
            self.image_hash = self.calculate_image_hash()
        
        # Save to database
        super().save(*args, **kwargs)
        return self

    @classmethod
    def create(cls, **kwargs):
        """Create a new ProductImage instance, avoiding duplicates"""
        product = kwargs.get('product')
        image = kwargs.get('image')
        is_primary = kwargs.get('is_primary', False)
        order = kwargs.get('order', 0)
        
        if not product or not image:
            raise ValueError("Both product and image are required")
            
        # Create the instance but don't save it yet
        instance = cls(
            product=product,
            image=image,
            is_primary=is_primary,
            order=order
        )
        
        # Calculate image hash
        image_hash = instance.calculate_image_hash()
        
        # Check for duplicate by hash
        if image_hash:
            duplicate = cls.objects.filter(
                product=product,
                image_hash=image_hash
            ).first()
            
            if duplicate:
                print(f"Found duplicate image (hash: {image_hash}), returning existing")
                return duplicate
        
        # No duplicate found, save the new instance
        instance.save()
        return instance


class OrderItem(models.Model):
    order = models.ForeignKey('Order', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def get_cost(self):
        return self.price * self.quantity


class Order(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class CategoryAttribute(models.Model):
    ATTRIBUTE_TYPES = [
        ('text', 'Text Input'),
        ('number', 'Number Input'),
        ('select', 'Single Selection'),
        ('multiselect', 'Multiple Selection'),
        ('boolean', 'Yes/No')
    ]
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_attributes')
    key = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPES, default='text', verbose_name='Attribute Type')
    required = models.BooleanField(default=False, verbose_name='Is Required')
    display_order = models.PositiveIntegerField(default=0, verbose_name='Display Order')
    label_fa = models.CharField(max_length=100, help_text='Persian display label')

    class Meta:
        unique_together = ('category', 'key')
        ordering = ['display_order', 'key']
        verbose_name = 'Category Attribute'
        verbose_name_plural = 'Category Attributes'

    def __str__(self):
        return f"{self.category.name} - {self.key}"

class AttributeValue(models.Model):
    attribute = models.ForeignKey(CategoryAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('attribute', 'value')
        ordering = ['display_order', 'value']
        verbose_name = 'Attribute Value'
        verbose_name_plural = 'Attribute Values'
    
    def __str__(self):
        return f"{self.attribute.key}: {self.value}"


class DeletedProduct(models.Model):
    """Model to track deleted products for audit purposes"""
    original_id = models.IntegerField(help_text='Original ID of the product')
    name = models.CharField(max_length=100)
    price_toman = models.DecimalField(max_digits=12, decimal_places=0)
    price_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    category_name = models.CharField(max_length=100)
    supplier_name = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=50, blank=True)
    deleted_at = models.DateTimeField(auto_now_add=True)
    deletion_reason = models.TextField(blank=True, null=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='deleted_products')

    class Meta:
        verbose_name = 'deleted product'
        verbose_name_plural = 'deleted products'
        ordering = ['-deleted_at']

    def __str__(self):
        return f"Deleted: {self.name} (ID: {self.original_id})"


class Wishlist(models.Model):
    """Model to manage user wishlists"""
    customer = models.ForeignKey('accounts.Customer', on_delete=models.CASCADE, related_name='wishlists', verbose_name='مشتری')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='wishlisted_by', verbose_name='محصول')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ اضافه شدن')
    
    class Meta:
        unique_together = ('customer', 'product')
        verbose_name = 'لیست علاقه‌مندی'
        verbose_name_plural = 'لیست‌های علاقه‌مندی'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.get_full_name()} - {self.product.name}"




