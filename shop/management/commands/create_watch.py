from django.core.management.base import BaseCommand
from shop.models import Category, Product, CategoryAttribute, AttributeValue, ProductAttribute
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates watch category and sample watch product'

    def handle(self, *args, **kwargs):
        try:
            # Create watch category if it doesn't exist
            watch_category, created = Category.objects.get_or_create(
                name='ساعت',
                defaults={'name': 'ساعت'}
            )
            
            # Define watch attributes
            watch_attributes = [
                {
                    'key': 'برند',
                    'type': 'select',
                    'required': True,
                    'values': ['Omega', 'Rolex', 'Patek Philippe', 'Audemars Piguet', 'Cartier']
                },
                {
                    'key': 'سری',
                    'type': 'select',
                    'required': True,
                    'values': ['Constellation', 'Seamaster', 'Speedmaster', 'De Ville']
                },
                {
                    'key': 'جنسیت',
                    'type': 'select',
                    'required': True,
                    'values': ['مردانه', 'زنانه', 'یونیسکس']
                },
                {
                    'key': 'نوع حرکت',
                    'type': 'select',
                    'required': True,
                    'values': ['اتوماتیک', 'کوارتز', 'دستی']
                },
                {
                    'key': 'جنس بدنه',
                    'type': 'select',
                    'required': True,
                    'values': ['استیل', 'طلای 18 عیار', 'طلای 14 عیار', 'تیتانیوم']
                },
                {
                    'key': 'جنس شیشه',
                    'type': 'select',
                    'required': True,
                    'values': ['سافایر', 'مینرال', 'پلکسی']
                },
                {
                    'key': 'مقاوم در برابر آب',
                    'type': 'select',
                    'required': True,
                    'values': ['30 متر', '50 متر', '100 متر', '200 متر', '300 متر', '600 متر']
                },
                {
                    'key': 'تاریخچه',
                    'type': 'text',
                    'required': False
                }
            ]
            
            # Create attributes for watch category
            for attr_data in watch_attributes:
                attr, created = CategoryAttribute.objects.get_or_create(
                    category=watch_category,
                    key=attr_data['key'],
                    defaults={
                        'type': attr_data['type'],
                        'required': attr_data['required']
                    }
                )
                
                # Add values for select type attributes
                if attr_data['type'] == 'select' and 'values' in attr_data:
                    for value in attr_data['values']:
                        AttributeValue.objects.get_or_create(
                            attribute=attr,
                            value=value
                        )
            
            # Create Omega Constellation watch
            product = Product.objects.create(
                name='Omega Constellation',
                description='''
                ساعت مچی Omega Constellation یکی از نمادین‌ترین مدل‌های برند اومگا است که با طراحی منحصر به فرد و کیفیت ساخت عالی شناخته می‌شود.
                
                ویژگی‌های کلیدی:
                - حرکت اتوماتیک با کالیبر 8500
                - بدنه استیل ضد زنگ
                - شیشه سافایر ضد خش
                - مقاوم در برابر آب تا عمق 100 متر
                - قابلیت نمایش تاریخ
                - بند استیل با قفل امنیتی
                ''',
                price_toman=Decimal('250000000'),  # 250 million Toman
                price_usd=Decimal('5000'),  # $5000
                category=watch_category,
                brand='Omega',
                model='Constellation',
                sku='OMG-CONST-001',
                weight=Decimal('150.00'),  # 150 grams
                dimensions='41mm x 13mm',
                warranty='2 سال گارانتی بین‌المللی',
                stock_quantity=1,
                is_active=True
            )
            
            # Add product attributes
            attributes = {
                'برند': 'Omega',
                'سری': 'Constellation',
                'جنسیت': 'مردانه',
                'نوع حرکت': 'اتوماتیک',
                'جنس بدنه': 'استیل',
                'جنس شیشه': 'سافایر',
                'مقاوم در برابر آب': '100 متر',
                'تاریخچه': 'سری Constellation اومگا در سال 1952 معرفی شد و به دلیل طراحی منحصر به فرد و کیفیت ساخت عالی، به یکی از محبوب‌ترین مدل‌های این برند تبدیل شده است.'
            }
            
            for key, value in attributes.items():
                ProductAttribute.objects.create(
                    product=product,
                    key=key,
                    value=value
                )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created Omega Constellation watch with ID: {product.id}'))
            
            # Create 20 diverse watches (no Seiko!)
            import random
            watch_brands = ['Omega', 'Rolex', 'Patek Philippe', 'Audemars Piguet', 'Cartier']
            watch_series = ['Constellation', 'Seamaster', 'Speedmaster', 'De Ville']
            genders = ['مردانه', 'زنانه', 'یونیسکس']
            movements = ['اتوماتیک', 'کوارتز', 'دستی']
            cases = ['استیل', 'طلای 18 عیار', 'طلای 14 عیار', 'تیتانیوم']
            crystals = ['سافایر', 'مینرال', 'پلکسی']
            water_resistances = ['30 متر', '50 متر', '100 متر', '200 متر', '300 متر', '600 متر']
            for i in range(20):
                brand = random.choice(watch_brands)
                series = random.choice(watch_series)
                gender = random.choice(genders)
                movement = random.choice(movements)
                case = random.choice(cases)
                crystal = random.choice(crystals)
                water_resistance = random.choice(water_resistances)
                model = f"{series}-{random.randint(1000,9999)}"
                name = f"{brand} {series} {model}"
                price_toman = Decimal(str(random.randint(100_000_000, 800_000_000)))
                price_usd = price_toman / Decimal('50000')
                sku = f"{brand[:3].upper()}-{series[:3].upper()}-{i+1:03d}"
                weight = Decimal(str(random.randint(120, 200)))
                dimensions = f"{random.randint(36, 45)}mm x {random.randint(8, 16)}mm"
                warranty = random.choice(['1 سال گارانتی', '2 سال گارانتی بین‌المللی', '3 سال گارانتی'])
                stock_quantity = random.randint(1, 10)
                description = f"ساعت {name} با کیفیت عالی و طراحی منحصر به فرد. مناسب برای {gender}."
                product = Product.objects.create(
                    name=name,
                    description=description,
                    price_toman=price_toman,
                    price_usd=price_usd,
                    category=watch_category,
                    brand=brand,
                    model=model,
                    sku=sku,
                    weight=weight,
                    dimensions=dimensions,
                    warranty=warranty,
                    stock_quantity=stock_quantity,
                    is_active=True
                )
                attributes = {
                    'برند': brand,
                    'سری': series,
                    'جنسیت': gender,
                    'نوع حرکت': movement,
                    'جنس بدنه': case,
                    'جنس شیشه': crystal,
                    'مقاوم در برابر آب': water_resistance,
                    'تاریخچه': f"این مدل {series} از برند {brand} یکی از محبوب‌ترین ساعت‌های {gender} است."
                }
                for key, value in attributes.items():
                    ProductAttribute.objects.create(
                        product=product,
                        key=key,
                        value=value
                    )
                self.stdout.write(self.style.SUCCESS(f'Created watch: {name}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating product: {str(e)}')) 