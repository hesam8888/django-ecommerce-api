# Generated manually to handle flexible attribute system
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_merge_0002_add_brand_image_0005_deletedproduct'),
    ]

    operations = [
        # Step 1: Create the new Attribute model
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='نام ویژگی')),
                ('key', models.CharField(help_text='کلید یکتا برای استفاده در API (مثل: color, size)', max_length=100, unique=True, verbose_name='کلید ویژگی')),
                ('type', models.CharField(choices=[('text', 'Text Input'), ('number', 'Number Input'), ('select', 'Single Selection'), ('multiselect', 'Multiple Selection'), ('boolean', 'Yes/No'), ('color', 'Color Picker'), ('size', 'Size Selection')], default='select', help_text='نوع تعیین می‌کند که این ویژگی چگونه در فرم‌ها نمایش داده شود', max_length=20, verbose_name='نوع ویژگی')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('is_filterable', models.BooleanField(default=True, help_text='آیا این ویژگی در فیلترهای جستجو نمایش داده شود؟', verbose_name='قابل فیلتر')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
            ],
            options={
                'verbose_name': 'ویژگی',
                'verbose_name_plural': 'ویژگی‌ها',
                'ordering': ['display_order', 'name'],
            },
        ),

        # Step 2: Create new AttributeValue model (separate from existing one)
        migrations.CreateModel(
            name='NewAttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100, verbose_name='مقدار')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('color_code', models.CharField(blank=True, help_text='کد رنگ hex برای ویژگی‌های رنگی (مثل: #FF0000)', max_length=7, null=True, verbose_name='کد رنگ')),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='shop.attribute', verbose_name='ویژگی')),
            ],
            options={
                'verbose_name': 'مقدار ویژگی',
                'verbose_name_plural': 'مقادیر ویژگی',
                'ordering': ['display_order', 'value'],
                'unique_together': {('attribute', 'value')},
            },
        ),

        # Step 3: Create ProductAttributeValue model
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('custom_value', models.CharField(blank=True, help_text='برای ویژگی‌های متنی یا عددی', max_length=255, null=True, verbose_name='مقدار سفارشی')),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.attribute', verbose_name='ویژگی')),
                ('attribute_value', models.ForeignKey(blank=True, help_text='برای ویژگی‌های از پیش تعریف شده', null=True, on_delete=django.db.models.deletion.CASCADE, to='shop.newattributevalue', verbose_name='مقدار ویژگی')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attribute_values', to='shop.product', verbose_name='محصول')),
            ],
            options={
                'verbose_name': 'مقدار ویژگی محصول',
                'verbose_name_plural': 'مقادیر ویژگی محصول',
                'unique_together': {('product', 'attribute')},
            },
        ),

        # Step 6: Update legacy models
        migrations.AlterModelOptions(
            name='productattribute',
            options={'verbose_name': 'Product Attribute (Legacy)', 'verbose_name_plural': 'Product Attributes (Legacy)'},
        ),
        migrations.AlterField(
            model_name='productattribute',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='legacy_attribute_set', to='shop.product'),
        ),
    ] 