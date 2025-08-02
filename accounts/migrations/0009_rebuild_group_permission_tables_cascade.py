from django.db import migrations

def rebuild_group_permission_tables(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    # Rebuild accounts_customer_groups
    cursor.execute('ALTER TABLE accounts_customer_groups RENAME TO accounts_customer_groups_old;')
    cursor.execute('''
        CREATE TABLE accounts_customer_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES accounts_customer(id) ON DELETE CASCADE,
            group_id INTEGER NOT NULL REFERENCES auth_group(id)
        );
    ''')
    cursor.execute('''
        INSERT INTO accounts_customer_groups (id, customer_id, group_id)
        SELECT id, customer_id, group_id FROM accounts_customer_groups_old;
    ''')
    cursor.execute('DROP TABLE accounts_customer_groups_old;')
    # Rebuild accounts_customer_user_permissions
    cursor.execute('ALTER TABLE accounts_customer_user_permissions RENAME TO accounts_customer_user_permissions_old;')
    cursor.execute('''
        CREATE TABLE accounts_customer_user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES accounts_customer(id) ON DELETE CASCADE,
            permission_id INTEGER NOT NULL REFERENCES auth_permission(id)
        );
    ''')
    cursor.execute('''
        INSERT INTO accounts_customer_user_permissions (id, customer_id, permission_id)
        SELECT id, customer_id, permission_id FROM accounts_customer_user_permissions_old;
    ''')
    cursor.execute('DROP TABLE accounts_customer_user_permissions_old;')

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0008_rebuild_address_table_cascade'),
    ]
    operations = [
        migrations.RunPython(rebuild_group_permission_tables),
    ] 