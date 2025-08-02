from django.core.management.base import BaseCommand
from shop.models import Category, Product, CategoryAttribute, AttributeValue, ProductAttribute
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates perfume category (عطر) and related attributes with Persian labels'

    def handle(self, *args, **kwargs):
        try:
            # Create perfume category if it doesn't exist
            perfume_category, created = Category.objects.get_or_create(
                name='عطر',
                defaults={'name': 'عطر'}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created perfume category: {perfume_category.name}'))
            else:
                self.stdout.write(f'Perfume category already exists: {perfume_category.name}')
            
            # Define perfume attributes with English keys and Persian labels/values
            perfume_attributes = [
                {
                    'key': 'brand',
                    'label_fa': 'برند',
                    'type': 'select',
                    'required': True,
                    'values': ['Chanel', 'Dior', 'Tom Ford', 'Creed', 'Yves Saint Laurent', 'Giorgio Armani', 'Versace', 'Gucci', 'Dolce & Gabbana', 'Paco Rabanne']
                },
                {
                    'key': 'fragrance_family',
                    'label_fa': 'خانواده عطر',
                    'type': 'select',
                    'required': True,
                    'values': ['شرقی', 'تازه', 'گلی', 'چوبی', 'ادویه‌ای', 'میوه‌ای', 'آکواتیک', 'گورماند', 'سبز', 'مرکبات']
                },
                {
                    'key': 'top_notes',
                    'label_fa': 'نت‌های آغازین',
                    'type': 'text',
                    'required': False
                },
                {
                    'key': 'middle_notes',
                    'label_fa': 'نت‌های میانی',
                    'type': 'text',
                    'required': False
                },
                {
                    'key': 'base_notes',
                    'label_fa': 'نت‌های پایانی',
                    'type': 'text',
                    'required': False
                },
                {
                    'key': 'volume',
                    'label_fa': 'حجم',
                    'type': 'select',
                    'required': True,
                    'values': ['30ml', '50ml', '75ml', '100ml', '125ml', '150ml', '200ml']
                },
                {
                    'key': 'gender',
                    'label_fa': 'جنسیت',
                    'type': 'select',
                    'required': True,
                    'values': ['مردانه', 'زنانه', 'یونیسکس']
                },
                {
                    'key': 'concentration',
                    'label_fa': 'غلظت',
                    'type': 'select',
                    'required': True,
                    'values': ['Parfum', 'Eau de Parfum', 'Eau de Toilette', 'Eau de Cologne', 'Eau Fraiche']
                },
                {
                    'key': 'origin_country',
                    'label_fa': 'کشور سازنده',
                    'type': 'select',
                    'required': False,
                    'values': ['فرانسه', 'ایتالیا', 'انگلیس', 'آمریکا', 'اسپانیا', 'آلمان', 'سوئیس', 'امارات متحده عربی']
                },
                {
                    'key': 'suitable_season',
                    'label_fa': 'فصل مناسب',
                    'type': 'multiselect',
                    'required': False,
                    'values': ['بهار', 'تابستان', 'پاییز', 'زمستان', 'همه فصول']
                },
                {
                    'key': 'longevity',
                    'label_fa': 'ماندگاری',
                    'type': 'select',
                    'required': False,
                    'values': ['کم (2-4 ساعت)', 'متوسط (4-6 ساعت)', 'خوب (6-8 ساعت)', 'عالی (8+ ساعت)']
                },
                {
                    'key': 'sillage',
                    'label_fa': 'پخش بو',
                    'type': 'select',
                    'required': False,
                    'values': ['نزدیک', 'متوسط', 'قوی', 'بسیار قوی']
                },
                {
                    'key': 'launch_year',
                    'label_fa': 'سال عرضه',
                    'type': 'number',
                    'required': False
                },
                {
                    'key': 'perfumer',
                    'label_fa': 'عطرساز',
                    'type': 'text',
                    'required': False
                },
                {
                    'key': 'occasion',
                    'label_fa': 'مناسبت مصرف',
                    'type': 'multiselect',
                    'required': False,
                    'values': ['روزانه', 'مهمانی', 'اداری', 'ورزشی', 'عاشقانه', 'رسمی', 'شبانه']
                }
            ]
            
            # Create attributes for perfume category
            for attr_data in perfume_attributes:
                attr, created = CategoryAttribute.objects.get_or_create(
                    category=perfume_category,
                    key=attr_data['key'],
                    defaults={
                        'label_fa': attr_data['label_fa'],
                        'type': attr_data['type'],
                        'required': attr_data['required']
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created attribute: {attr_data["label_fa"]} ({attr_data["key"]})'))
                
                # Add values for select type attributes
                if attr_data['type'] in ['select', 'multiselect'] and 'values' in attr_data:
                    for order, value in enumerate(attr_data['values']):
                        attr_value, created = AttributeValue.objects.get_or_create(
                            attribute=attr,
                            value=value,
                            defaults={'display_order': order}
                        )
                        if created:
                            self.stdout.write(f'  Added value: {value}')
            
            # Create a sample perfume product
            sample_perfume = Product.objects.create(
                name='Chanel No. 5 Eau de Parfum',
                description='''
                شانل شماره 5 یکی از معروف‌ترین و محبوب‌ترین عطرهای دنیا است که در سال 1921 توسط ارنست بو خلق شد.
                
                ویژگی‌های کلیدی:
                - نت‌های آغازین: آلدهید، نرولی، لیمو، برگاموت، لیمون
                - نت‌های میانی: یاس، رز، زنبق دره، ایریس
                - نت‌های پایانی: وتیور، صندل، وانیل، مشک سفید، عنبر
                - ماندگاری عالی و پخش بوی قوی
                - مناسب برای زنان با شخصیت قوی و خاص
                ''',
                price_toman=Decimal('8500000'),  # 8.5 million Toman
                price_usd=Decimal('170'),  # $170
                category=perfume_category,
                model='No. 5 EDP',
                sku='CHANEL-NO5-EDP-100',
                weight=Decimal('300.00'),  # 300 grams including packaging
                dimensions='12cm x 8cm x 8cm',
                warranty='گارانتی اصالت کالا',
                stock_quantity=5,
                is_active=True
            )
            
            # Add product attributes for the sample perfume
            sample_attributes = {
                'brand': 'Chanel',
                'fragrance_family': 'گلی',
                'top_notes': 'آلدهید، نرولی، لیمو، برگاموت، لیمون',
                'middle_notes': 'یاس، رز، زنبق دره، ایریس',
                'base_notes': 'وتیور، صندل، وانیل، مشک سفید، عنبر',
                'volume': '100ml',
                'gender': 'زنانه',
                'concentration': 'Eau de Parfum',
                'origin_country': 'فرانسه',
                'suitable_season': 'همه فصول',
                'longevity': 'عالی (8+ ساعت)',
                'sillage': 'قوی',
                'launch_year': '1921',
                'perfumer': 'Ernest Beaux',
                'occasion': 'رسمی، مهمانی، عاشقانه'
            }
            
            for key, value in sample_attributes.items():
                ProductAttribute.objects.create(
                    product=sample_perfume,
                    key=key,
                    value=value
                )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created sample perfume: {sample_perfume.name} with ID: {sample_perfume.id}'))
            
            # Create additional sample perfumes
            sample_perfumes = [
                {
                    'name': 'Dior Sauvage Eau de Toilette',
                    'description': 'عطر مردانه دیور ساواژ با رایحه‌ای تازه و طبیعی که الهام از طبیعت وحشی گرفته شده است.',
                    'price_toman': Decimal('6200000'),
                    'price_usd': Decimal('124'),
                    'attributes': {
                        'brand': 'Dior',
                        'fragrance_family': 'تازه',
                        'top_notes': 'برگاموت، فلفل رز',
                        'middle_notes': 'لاوندر، ژرانیوم، الدانوس',
                        'base_notes': 'عنبر، پچولی، وتیور',
                        'volume': '100ml',
                        'gender': 'مردانه',
                        'concentration': 'Eau de Toilette',
                        'origin_country': 'فرانسه',
                        'suitable_season': 'همه فصول',
                        'longevity': 'خوب (6-8 ساعت)',
                        'sillage': 'متوسط',
                        'launch_year': '2015',
                        'perfumer': 'François Demachy',
                        'occasion': 'روزانه، اداری، ورزشی'
                    }
                },
                {
                    'name': 'Tom Ford Black Orchid',
                    'description': 'عطر یونیسکس تام فورد با رایحه‌ای شرقی و مرموز که برای عاشقان عطرهای پیچیده طراحی شده است.',
                    'price_toman': Decimal('12500000'),
                    'price_usd': Decimal('250'),
                    'attributes': {
                        'brand': 'Tom Ford',
                        'fragrance_family': 'شرقی',
                        'top_notes': 'ترافل، گردو، کشمش سیاه',
                        'middle_notes': 'ارکیده، ادویه‌ها، یاس',
                        'base_notes': 'پچولی، وانیل، عنبر',
                        'volume': '50ml',
                        'gender': 'یونیسکس',
                        'concentration': 'Eau de Parfum',
                        'origin_country': 'آمریکا',
                        'suitable_season': 'پاییز، زمستان',
                        'longevity': 'عالی (8+ ساعت)',
                        'sillage': 'بسیار قوی',
                        'launch_year': '2006',
                        'perfumer': 'David Apel, Pierre Negrin',
                        'occasion': 'شبانه، مهمانی، رسمی'
                    }
                }
            ]
            
            for perfume_data in sample_perfumes:
                product = Product.objects.create(
                    name=perfume_data['name'],
                    description=perfume_data['description'],
                    price_toman=perfume_data['price_toman'],
                    price_usd=perfume_data['price_usd'],
                    category=perfume_category,
                    model=perfume_data['name'].split()[-1],  # Use last word as model
                    sku=f"{perfume_data['attributes']['brand'].upper()}-{perfume_data['attributes']['volume']}-001",
                    weight=Decimal('300.00'),
                    dimensions='12cm x 8cm x 8cm',
                    warranty='گارانتی اصالت کالا',
                    stock_quantity=3,
                    is_active=True
                )
                
                # Add attributes for this perfume
                for key, value in perfume_data['attributes'].items():
                    ProductAttribute.objects.create(
                        product=product,
                        key=key,
                        value=value
                    )
                
                self.stdout.write(self.style.SUCCESS(f'Created perfume: {product.name}'))
            
            self.stdout.write(self.style.SUCCESS('Successfully created perfume category with all attributes and sample products!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating perfume category: {str(e)}')) 