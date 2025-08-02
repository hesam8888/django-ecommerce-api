from django.core.management.base import BaseCommand
from shop.models import Category, CategoryAttribute, AttributeValue, Product

class Command(BaseCommand):
    help = 'Set up gender-based category structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-products',
            action='store_true',
            help='Migrate existing products to gender categories',
        )

    def handle(self, *args, **options):
        self.stdout.write("🚀 Setting up Gender-Based Category Architecture")
        self.stdout.write("=" * 60)
        
        # Step 1: Create categories
        created_categories = self.create_gender_based_categories()
        
        # Step 2: Migrate existing products if requested
        if options['migrate_products']:
            self.migrate_existing_products()
        
        # Step 3: Show final structure
        self.show_category_structure()
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Setup Complete!"))
        self.stdout.write("\nNext Steps:")
        self.stdout.write("1. ✅ Categories and attributes are ready")
        self.stdout.write("2. 📝 When adding new products, assign them to gender-specific categories")
        self.stdout.write("3. 🔍 Use the API endpoints provided for frontend integration")
        
        self.stdout.write(f"\n💡 Example API calls:")
        self.stdout.write(f"   - Get men's watches: GET /api/products/?category=ساعت&gender=مردانه")
        self.stdout.write(f"   - Get women's clothing: GET /api/products/?category=لباس&gender=زنانه")

    def create_gender_based_categories(self):
        """
        Create the recommended gender-based category structure
        """
        self.stdout.write("🏗️  Creating gender-based category structure...")
        
        # Define categories that need gender separation
        gender_categories = {
            'ساعت': {
                'genders': ['مردانه', 'زنانه', 'یونیسکس'],
                'attributes': [
                    {'key': 'برند', 'type': 'select', 'required': True, 'label_fa': 'برند'},
                    {'key': 'سری', 'type': 'select', 'required': True, 'label_fa': 'سری'},
                    {'key': 'نوع حرکت', 'type': 'select', 'required': True, 'label_fa': 'نوع حرکت'},
                    {'key': 'جنس بدنه', 'type': 'select', 'required': True, 'label_fa': 'جنس بدنه'},
                    {'key': 'جنس شیشه', 'type': 'select', 'required': True, 'label_fa': 'جنس شیشه'},
                    {'key': 'مقاوم در برابر آب', 'type': 'select', 'required': False, 'label_fa': 'مقاوم در برابر آب'},
                    {'key': 'جنسیت', 'type': 'select', 'required': True, 'label_fa': 'جنسیت'}
                ]
            },
            'لباس': {
                'genders': ['مردانه', 'زنانه', 'یونیسکس'],
                'attributes': [
                    {'key': 'برند', 'type': 'select', 'required': True, 'label_fa': 'برند'},
                    {'key': 'سایز', 'type': 'select', 'required': True, 'label_fa': 'سایز'},
                    {'key': 'رنگ', 'type': 'select', 'required': True, 'label_fa': 'رنگ'},
                    {'key': 'جنس پارچه', 'type': 'select', 'required': True, 'label_fa': 'جنس پارچه'},
                    {'key': 'طرح', 'type': 'select', 'required': False, 'label_fa': 'طرح'},
                    {'key': 'جنسیت', 'type': 'select', 'required': True, 'label_fa': 'جنسیت'}
                ]
            },
            'عطر': {
                'genders': ['مردانه', 'زنانه', 'یونیسکس'],
                'attributes': [
                    {'key': 'برند', 'type': 'select', 'required': True, 'label_fa': 'برند'},
                    {'key': 'حجم', 'type': 'select', 'required': True, 'label_fa': 'حجم'},
                    {'key': 'نوع رایحه', 'type': 'select', 'required': True, 'label_fa': 'نوع رایحه'},
                    {'key': 'پایداری', 'type': 'select', 'required': False, 'label_fa': 'پایداری'},
                    {'key': 'فصل', 'type': 'select', 'required': False, 'label_fa': 'فصل'},
                    {'key': 'جنسیت', 'type': 'select', 'required': True, 'label_fa': 'جنسیت'}
                ]
            },
            'کفش': {
                'genders': ['مردانه', 'زنانه', 'یونیسکس'],
                'attributes': [
                    {'key': 'برند', 'type': 'select', 'required': True, 'label_fa': 'برند'},
                    {'key': 'سایز', 'type': 'select', 'required': True, 'label_fa': 'سایز'},
                    {'key': 'رنگ', 'type': 'select', 'required': True, 'label_fa': 'رنگ'},
                    {'key': 'جنس', 'type': 'select', 'required': True, 'label_fa': 'جنس'},
                    {'key': 'نوع کفش', 'type': 'select', 'required': True, 'label_fa': 'نوع کفش'},
                    {'key': 'جنسیت', 'type': 'select', 'required': True, 'label_fa': 'جنسیت'}
                ]
            }
        }
        
        created_categories = {}
        
        for main_cat_name, data in gender_categories.items():
            self.stdout.write(f"\n📂 Creating category: {main_cat_name}")
            
            # Create or get main category
            main_category, created = Category.objects.get_or_create(
                name=main_cat_name,
                defaults={'parent': None}
            )
            
            if created:
                self.stdout.write(f"   ✅ Created main category: {main_cat_name}")
            else:
                self.stdout.write(f"   ℹ️  Main category already exists: {main_cat_name}")
            
            created_categories[main_cat_name] = main_category
            
            # Create gender subcategories
            for gender in data['genders']:
                subcategory_name = f"{main_cat_name} {gender}"
                
                subcategory, created = Category.objects.get_or_create(
                    name=subcategory_name,
                    defaults={'parent': main_category}
                )
                
                if created:
                    self.stdout.write(f"   ✅ Created subcategory: {subcategory_name}")
                else:
                    self.stdout.write(f"   ℹ️  Subcategory already exists: {subcategory_name}")
                
                created_categories[subcategory_name] = subcategory
                
                # Add attributes to subcategory
                self.stdout.write(f"      📋 Adding attributes to {subcategory_name}:")
                
                for i, attr_data in enumerate(data['attributes']):
                    category_attr, created = CategoryAttribute.objects.get_or_create(
                        category=subcategory,
                        key=attr_data['key'],
                        defaults={
                            'type': attr_data['type'],
                            'required': attr_data['required'],
                            'display_order': i,
                            'label_fa': attr_data['label_fa']
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"         ✅ Added attribute: {attr_data['key']}")
                    else:
                        self.stdout.write(f"         ℹ️  Attribute already exists: {attr_data['key']}")
                    
                    # Add gender values for gender attribute
                    if attr_data['key'] == 'جنسیت':
                        for j, gender_value in enumerate(['مردانه', 'زنانه', 'یونیسکس']):
                            attr_value, created = AttributeValue.objects.get_or_create(
                                attribute=category_attr,
                                value=gender_value,
                                defaults={'display_order': j}
                            )
                            if created:
                                self.stdout.write(f"            ✅ Added gender value: {gender_value}")
        
        return created_categories

    def migrate_existing_products(self):
        """
        Migrate existing products to appropriate gender categories
        """
        self.stdout.write("\n🔄 Migrating existing products...")
        
        # Find products in main categories that should be moved to gender subcategories
        main_categories = ['ساعت', 'لباس', 'عطر', 'کفش']
        
        for main_cat_name in main_categories:
            try:
                main_category = Category.objects.get(name=main_cat_name)
                products_in_main = Product.objects.filter(category=main_category)
                
                if products_in_main.exists():
                    self.stdout.write(f"\n📦 Found {products_in_main.count()} products in {main_cat_name}")
                    self.stdout.write("   These products should be moved to gender-specific subcategories:")
                    
                    for product in products_in_main:
                        # Try to determine gender from existing attributes
                        gender = self.get_product_gender_from_attributes(product)
                        
                        if gender:
                            # Move to appropriate gender subcategory
                            gender_category_name = f"{main_cat_name} {gender}"
                            try:
                                gender_category = Category.objects.get(name=gender_category_name)
                                product.category = gender_category
                                product.save()
                                self.stdout.write(f"   ✅ Moved '{product.name}' to {gender_category_name}")
                            except Category.DoesNotExist:
                                self.stdout.write(f"   ❌ Gender category not found: {gender_category_name}")
                        else:
                            self.stdout.write(f"   ⚠️  Could not determine gender for: {product.name}")
                            self.stdout.write(f"      Please manually assign this product to a gender category")
            
            except Category.DoesNotExist:
                self.stdout.write(f"   ℹ️  No main category found: {main_cat_name}")

    def get_product_gender_from_attributes(self, product):
        """
        Try to determine product gender from existing attributes
        """
        # Check legacy ProductAttribute model
        try:
            gender_attr = product.attribute_set.filter(key='جنسیت').first()
            if gender_attr:
                return gender_attr.value
        except:
            pass
        
        # Check new ProductAttributeValue model
        try:
            gender_attr = product.attribute_values.filter(
                attribute__key='جنسیت'
            ).first()
            if gender_attr:
                if gender_attr.attribute_value:
                    return gender_attr.attribute_value.value
                return gender_attr.custom_value
        except:
            pass
        
        # Try to guess from product name
        product_name = product.name.lower()
        if 'مردانه' in product_name or 'مرد' in product_name:
            return 'مردانه'
        elif 'زنانه' in product_name or 'زن' in product_name:
            return 'زنانه'
        elif 'یونیسکس' in product_name:
            return 'یونیسکس'
        
        return None

    def show_category_structure(self):
        """
        Display the created category structure
        """
        self.stdout.write("\n📊 Category Structure:")
        self.stdout.write("=" * 50)
        
        main_categories = Category.objects.filter(parent=None)
        
        for main_cat in main_categories:
            product_count = Product.objects.filter(category=main_cat, is_active=True).count()
            self.stdout.write(f"📂 {main_cat.name} ({product_count} products)")
            
            for subcat in main_cat.subcategories.all():
                sub_product_count = Product.objects.filter(category=subcat, is_active=True).count()
                attributes_count = subcat.category_attributes.count()
                self.stdout.write(f"   └── {subcat.name} ({sub_product_count} products, {attributes_count} attributes)") 