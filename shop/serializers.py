from rest_framework import serializers
from .models import Product, ProductAttributeValue, ProductAttribute, Category, Wishlist

class LegacyProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = ['key', 'value']

class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(source='attribute.key')
    value = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttributeValue
        fields = ['attribute', 'value']

    def get_value(self, obj):
        # Prefer attribute_value (FK to NewAttributeValue), else custom_value
        if obj.attribute_value:
            return obj.attribute_value.value
        return obj.custom_value

class ProductImageSerializer(serializers.Serializer):
    url = serializers.CharField()
    is_primary = serializers.BooleanField()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    price_toman = serializers.FloatField()
    price_usd = serializers.FloatField(allow_null=True)
    stock_quantity = serializers.IntegerField()
    created_at = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price_toman', 'price_usd', 'model', 'sku',
            'stock_quantity', 'created_at', 'images', 'attributes', 'category', 'is_new_arrival', 'is_active'
        ]

    def get_created_at(self, obj):
        # Return as seconds since 1970 for Swift Date compatibility
        return obj.created_at.timestamp()

    def get_images(self, obj):
        request = self.context.get('request', None)
        images = []
        for image in obj.images.all():
            url = image.image.url
            if request and not url.startswith(('http://', 'https://')):
                url = request.build_absolute_uri(url)
            images.append({'url': url, 'is_primary': image.is_primary})
        return images

    def get_attributes(self, obj):
        # Get allowed keys for this product's category
        allowed_keys = set()
        if obj.category:
            allowed_keys = set(obj.category.category_attributes.values_list('key', flat=True))
        attributes = []
        # Collect from new system (attribute_values)
        for av in obj.attribute_values.all():
            key = av.attribute.key
            value = av.get_display_value()
            if key == 'برند':
                key = 'brand'
            if value is not None and value != '':
                attributes.append({'key': key, 'value': value})
        # Collect from legacy system (legacy_attribute_set)
        for legacy in obj.legacy_attribute_set.all():
            key = legacy.key
            value = legacy.value
            if key == 'برند':
                key = 'brand'
            if value is not None and value != '':
                attributes.append({'key': key, 'value': value})
        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_attributes = []
        for attr in attributes:
            if attr['key'] not in seen:
                seen.add(attr['key'])
                unique_attributes.append(attr)
        # Only include attributes defined for the product's category
        if allowed_keys:
            unique_attributes = [attr for attr in unique_attributes if attr['key'] in allowed_keys]
        return unique_attributes


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'customer_name', 'customer_email', 'created_at']
        read_only_fields = ['customer']


class WishlistCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating wishlist items"""
    product_id = serializers.IntegerField()
    
    class Meta:
        model = Wishlist
        fields = ['product_id']
    
    def validate_product_id(self, value):
        """Validate that the product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
        return value
    
    def create(self, validated_data):
        """Create wishlist item"""
        product_id = validated_data['product_id']
        customer = self.context['request'].user
        
        # Create or get existing wishlist item
        wishlist_item, created = Wishlist.objects.get_or_create(
            customer=customer,
            product_id=product_id
        )
        
        if not created:
            raise serializers.ValidationError("Product already in wishlist")
        
        return wishlist_item


class WishlistSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for wishlist without nested product data"""
    product_id = serializers.IntegerField(source='product.id')
    product_name = serializers.CharField(source='product.name')
    product_price = serializers.CharField(source='product.get_formatted_toman_price')
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product_id', 'product_name', 'product_price', 'created_at'] 