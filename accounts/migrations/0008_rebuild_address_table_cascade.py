from django.db import migrations, models
import django.db.models.deletion

def rebuild_address_table(apps, schema_editor):
    # Get the database connection
    connection = schema_editor.connection
    cursor = connection.cursor()
    # Rename the old table
    cursor.execute('ALTER TABLE accounts_address RENAME TO accounts_address_old;')
    # Recreate the table with the correct constraint
    cursor.execute('''
        CREATE TABLE accounts_address (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label VARCHAR(50) NULL,
            street_address VARCHAR(255) NOT NULL,
            city VARCHAR(100) NOT NULL,
            province VARCHAR(100) NULL,
            pelak VARCHAR(20) NULL,
            vahed VARCHAR(20) NULL,
            country VARCHAR(100) NOT NULL DEFAULT 'ایران',
            postal_code VARCHAR(20) NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            customer_id INTEGER NOT NULL REFERENCES accounts_customer(id) ON DELETE CASCADE
        );
    ''')
    # Copy the data
    cursor.execute('''
        INSERT INTO accounts_address (id, label, street_address, city, province, pelak, vahed, country, postal_code, created_at, updated_at, customer_id)
        SELECT id, label, street_address, city, province, pelak, vahed, country, postal_code, created_at, updated_at, customer_id FROM accounts_address_old;
    ''')
    # Drop the old table
    cursor.execute('DROP TABLE accounts_address_old;')

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0007_merge_20250630_2224'),
    ]
    operations = [
        migrations.RunPython(rebuild_address_table),
    ] 