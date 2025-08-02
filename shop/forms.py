# forms.py
from django import forms
from .models import Product, ProductImage, Category, Tag, CategoryAttribute, AttributeValue, ProductAttributeValue
from suppliers.models import Supplier
from decimal import Decimal, InvalidOperation

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class ProductForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        label="تصاویر محصول",
        widget=MultipleFileInput(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="انتخاب کنید",
        required=True,
        label="دسته‌بندی",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        empty_label="انتخاب کنید",
        required=False,
        label="تامین‌کننده",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        label="برچسب‌ها",
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control multi-select-tags',
            'data-placeholder': 'انتخاب برچسب‌ها',
        })
    )
    
    price_toman = forms.DecimalField(
        max_digits=12,
        decimal_places=0,
        required=True,
        label="قیمت (تومان)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'قیمت به تومان (الزامی)'})
    )
    
    price_usd = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        label="قیمت (دلار)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'قیمت به دلار (اختیاری)'})
    )
    
    # Keep these fields for backwards compatibility but hide them
    price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.HiddenInput(),
    )
    
    price_currency = forms.ChoiceField(
        choices=Product.CURRENCY_CHOICES,
        required=False,
        widget=forms.HiddenInput(),
    )
    
    # Entity fields
    model = forms.CharField(
        max_length=100,
        required=False,
        label="مدل",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    sku = forms.CharField(
        max_length=50,
        required=False,
        label="کد محصول",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    weight = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="وزن (گرم)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    dimensions = forms.CharField(
        max_length=100,
        required=False,
        label="ابعاد (سانتیمتر)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    warranty = forms.CharField(
        max_length=100,
        required=False,
        label="گارانتی",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    stock_quantity = forms.IntegerField(
        required=True,
        label="تعداد موجودی",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        initial=0
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial tags queryset based on category
        if 'instance' in kwargs and kwargs['instance']:
            instance = kwargs['instance']
            if instance.category:
                self.fields['tags'].queryset = Tag.objects.filter(
                    categories=instance.category
                ).distinct()
        elif 'initial' in kwargs and 'category' in kwargs['initial']:
            category = kwargs['initial']['category']
            if category:
                self.fields['tags'].queryset = Tag.objects.filter(
                    categories=category
                ).distinct()
        elif 'data' in kwargs and 'category' in kwargs['data']:
            category_id = kwargs['data']['category']
            if category_id:
                self.fields['tags'].queryset = Tag.objects.filter(
                    categories__id=category_id
                ).distinct()
        
        # Dynamically add fields for category attributes
        category = None
        if 'instance' in kwargs and kwargs['instance'] and kwargs['instance'].category:
            category = kwargs['instance'].category
        elif 'initial' in kwargs and 'category' in kwargs['initial']:
            category = kwargs['initial']['category']
        elif 'data' in kwargs and 'category' in kwargs['data']:
            try:
                category = Category.objects.get(id=kwargs['data']['category'])
            except Exception:
                pass
        if category:
            attributes = CategoryAttribute.objects.filter(category=category).order_by('display_order', 'key')
            for attr in attributes:
                field_name = f'attr_{attr.key}'
                field_required = attr.required
                if attr.type == 'text':
                    self.fields[field_name] = forms.CharField(
                        required=field_required,
                        label=attr.key,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                elif attr.type == 'number':
                    self.fields[field_name] = forms.DecimalField(
                        required=field_required,
                        label=attr.key,
                        widget=forms.NumberInput(attrs={'class': 'form-control'})
                    )
                elif attr.type == 'select':
                    choices = [(v.value, v.value) for v in attr.values.order_by('display_order', 'value')]
                    self.fields[field_name] = forms.ChoiceField(
                        required=field_required,
                        label=attr.key,
                        choices=choices,
                        widget=forms.Select(attrs={'class': 'form-control'})
                    )
                elif attr.type == 'multiselect':
                    choices = [(v.value, v.value) for v in attr.values.order_by('display_order', 'value')]
                    self.fields[field_name] = forms.MultipleChoiceField(
                        required=field_required,
                        label=attr.key,
                        choices=choices,
                        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
                    )
                elif attr.type == 'boolean':
                    self.fields[field_name] = forms.BooleanField(
                        required=field_required,
                        label=attr.key
                    )
                # Set initial value if editing
                if 'instance' in kwargs and kwargs['instance']:
                    product = kwargs['instance']
                    from shop.models import ProductAttribute
                    pav = ProductAttribute.objects.filter(product=product, key=attr.key).first()
                    if pav:
                        if attr.type == 'multiselect':
                            self.initial[field_name] = pav.value.split(',') if pav.value else []
                        else:
                            self.initial[field_name] = pav.value

    def clean_price_toman(self):
        price_toman = self.cleaned_data['price_toman']
        if isinstance(price_toman, str):
            # Remove commas and convert to decimal
            price_toman = price_toman.replace(',', '')
            try:
                price_toman = Decimal(price_toman)
            except (ValueError, InvalidOperation):
                raise forms.ValidationError('لطفا یک عدد معتبر وارد کنید')
        
        if price_toman <= 0:
            raise forms.ValidationError('قیمت تومان باید بزرگتر از صفر باشد')
        return price_toman
        
    def clean_price_usd(self):
        price_usd = self.cleaned_data.get('price_usd')
        if price_usd is not None:
            if isinstance(price_usd, str):
                # Remove commas and convert to decimal
                price_usd = price_usd.replace(',', '')
                try:
                    price_usd = Decimal(price_usd)
                except (ValueError, InvalidOperation):
                    raise forms.ValidationError('لطفا یک عدد معتبر وارد کنید')
            
            if price_usd <= 0:
                raise forms.ValidationError('قیمت دلار باید بزرگتر از صفر باشد')
        return price_usd
        
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        tags = cleaned_data.get('tags')
        
        # Validate that selected tags belong to the selected category
        if category and tags:
            valid_tags = Tag.objects.filter(categories=category)
            for tag in tags:
                if tag not in valid_tags:
                    self.add_error('tags', f'Tag "{tag}" is not valid for the selected category.')
        
        # Set the old price field for compatibility
        if 'price_toman' in cleaned_data and cleaned_data['price_toman']:
            cleaned_data['price'] = cleaned_data['price_toman']
            cleaned_data['price_currency'] = 'TOMAN'
        
        # Remove all references to CategoryAttribute and AttributeValue
        
        return cleaned_data

    def clean_images(self):
        images = self.files.getlist('images')
        if len(images) > 10:
            raise forms.ValidationError('شما نمی‌توانید بیشتر از 10 تصویر آپلود کنید')
        
        # Validate each image
        for image in images:
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError('فقط فایل‌های تصویری مجاز هستند')
            if image.size > 20 * 1024 * 1024:  # 20MB
                raise forms.ValidationError('حجم هر تصویر نباید بیشتر از 20 مگابایت باشد')
        
        return images

    def save(self, commit=True):
        product = super().save(commit)
        # Save dynamic attributes
        category = product.category
        attributes = CategoryAttribute.objects.filter(category=category)
        for attr in attributes:
            field_name = f'attr_{attr.key}'
            value = self.cleaned_data.get(field_name)
            if value is not None:
                from shop.models import ProductAttribute
                pav, _ = ProductAttribute.objects.get_or_create(product=product, key=attr.key)
                if attr.type == 'multiselect':
                    pav.value = ','.join(value)
                else:
                    pav.value = value
                pav.save()
        return product

    class Meta:
        model = Product
        fields = ['name', 'description', 'price_toman', 'price_usd', 'price', 'price_currency', 
                  'category', 'supplier', 'tags', 'is_active', 'model', 'sku', 'weight', 
                  'dimensions', 'warranty', 'stock_quantity']

# class ProductImageForm(forms.ModelForm):
#     image = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

#     class Meta:
#         model = ProductImage
#         fields = ['image']

class TagForm(forms.ModelForm):
    """
    Custom form for Tag model that handles Persian text in slug field
    """
    slug = forms.SlugField(
        max_length=100,
        required=False,
        help_text="Leave empty to auto-generate. For Persian text, a unique ID will be created."
    )
    
    class Meta:
        model = Tag
        fields = ['name', 'slug', 'categories']
        
    def clean_slug(self):
        """
        Allow slug to be empty; it will be auto-generated in the model save method
        """
        slug = self.cleaned_data.get('slug')
        if not slug:
            # We'll handle this in the model save method
            return ''
        return slug
