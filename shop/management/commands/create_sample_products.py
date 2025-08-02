from django.core.management.base import BaseCommand
from shop.models import Category, Product, Tag
from decimal import Decimal
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Creates 100 sample products across different categories'

    def handle(self, *args, **kwargs):
        # Create main categories if they don't exist
        categories = {
            'Electronics': {
                'subcategories': ['Smartphones', 'Laptops', 'Tablets', 'Accessories']
            },
            'Fashion': {
                'subcategories': ['Men\'s Clothing', 'Women\'s Clothing', 'Shoes', 'Accessories']
            },
            'Home': {
                'subcategories': ['Furniture', 'Kitchen', 'Decor', 'Lighting']
            },
            'Sports': {
                'subcategories': ['Fitness', 'Outdoor', 'Team Sports', 'Equipment']
            },
            'Books': {
                'subcategories': ['Fiction', 'Non-Fiction', 'Educational', 'Children']
            }
        }

        # Create categories and subcategories
        created_categories = {}
        for main_cat, data in categories.items():
            main_category, _ = Category.objects.get_or_create(name=main_cat)
            created_categories[main_cat] = main_category
            
            for subcat in data['subcategories']:
                subcategory, _ = Category.objects.get_or_create(
                    name=subcat,
                    parent=main_category
                )
                created_categories[subcat] = subcategory

        # Sample data for products
        brands = {
            'Electronics': ['Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Lenovo'],
            'Fashion': ['Nike', 'Adidas', 'Zara', 'H&M', 'Gucci', 'Puma', 'Under Armour'],
            'Home': ['IKEA', 'Ashley', 'Pottery Barn', 'West Elm', 'Crate & Barrel'],
            'Sports': ['Nike', 'Adidas', 'Under Armour', 'Puma', 'Reebok', 'New Balance'],
            'Books': ['Penguin', 'HarperCollins', 'Random House', 'Simon & Schuster']
        }

        # Create tags
        tags = {
            'Electronics': ['New', 'Popular', 'Best Seller', 'Limited Edition'],
            'Fashion': ['Trending', 'Classic', 'Seasonal', 'Exclusive'],
            'Home': ['Modern', 'Traditional', 'Minimalist', 'Luxury'],
            'Sports': ['Professional', 'Amateur', 'Training', 'Competition'],
            'Books': ['Bestseller', 'Award Winner', 'New Release', 'Classic']
        }

        # Create products
        for i in range(100):
            # Select random main category
            main_cat = random.choice(list(categories.keys()))
            subcat = random.choice(categories[main_cat]['subcategories'])
            category = created_categories[subcat]
            
            # Generate product data
            brand = random.choice(brands[main_cat])
            model = f"Model-{random.randint(1000, 9999)}"
            name = f"{brand} {model}"
            
            # Generate random price between 100,000 and 10,000,000 Toman
            price_toman = Decimal(str(random.randint(100000, 10000000)))
            price_usd = price_toman / Decimal('50000')  # Approximate USD conversion
            
            # Create product
            product = Product.objects.create(
                name=name,
                description=f"High-quality {name} with excellent features and durability.",
                price_toman=price_toman,
                price_usd=price_usd,
                category=category,
                brand=brand,
                model=model,
                sku=f"SKU-{random.randint(10000, 99999)}",
                stock_quantity=random.randint(1, 100),
                is_active=True,
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            
            # Add tags
            for tag_name in random.sample(tags[main_cat], k=random.randint(1, 3)):
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                product.tags.add(tag)
            
            self.stdout.write(self.style.SUCCESS(f'Created product: {name}')) 