from django.db import migrations, models
import django.utils.timezone

def generate_usernames(apps, schema_editor):
    Customer = apps.get_model('accounts', 'Customer')
    for customer in Customer.objects.all():
        if not customer.username:
            base_username = customer.email.split('@')[0]
            username = base_username
            counter = 1
            while Customer.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            customer.username = username
            customer.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # First add the field as nullable
        migrations.AddField(
            model_name='customer',
            name='username',
            field=models.CharField(max_length=150, null=True, unique=True),
        ),
        # Generate usernames for existing customers
        migrations.RunPython(generate_usernames),
        # Make the field non-nullable
        migrations.AlterField(
            model_name='customer',
            name='username',
            field=models.CharField(max_length=150, unique=True),
        ),
    ] 