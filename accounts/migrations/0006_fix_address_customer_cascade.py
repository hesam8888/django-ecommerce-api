from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='address',
            name='customer',
        ),
        migrations.AddField(
            model_name='address',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='accounts.customer'),
        ),
    ] 