from django.db import migrations

def rebuild_suppliers_tables(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    # Rebuild suppliers_deletedsupplier
    cursor.execute('ALTER TABLE suppliers_deletedsupplier RENAME TO suppliers_deletedsupplier_old;')
    cursor.execute('''
        CREATE TABLE suppliers_deletedsupplier (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(254) NOT NULL,
            phone VARCHAR(15) NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL,
            deleted_at DATETIME NOT NULL,
            deletion_reason TEXT NULL,
            deleted_by_id INTEGER NULL REFERENCES suppliers_user(id) ON DELETE SET NULL
        );
    ''')
    cursor.execute('''
        INSERT INTO suppliers_deletedsupplier (id, original_id, name, email, phone, address, description, deleted_at, deletion_reason, deleted_by_id)
        SELECT id, original_id, name, email, phone, address, description, deleted_at, deletion_reason, deleted_by_id FROM suppliers_deletedsupplier_old;
    ''')
    cursor.execute('DROP TABLE suppliers_deletedsupplier_old;')
    # Rebuild suppliers_backuplog
    cursor.execute('ALTER TABLE suppliers_backuplog RENAME TO suppliers_backuplog_old;')
    cursor.execute('''
        CREATE TABLE suppliers_backuplog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL,
            started_at DATETIME NOT NULL,
            completed_at DATETIME NULL,
            file_size BIGINT NULL,
            error_message TEXT NULL,
            backup_type VARCHAR(50) NOT NULL,
            created_by_id INTEGER NULL REFERENCES suppliers_user(id) ON DELETE SET NULL
        );
    ''')
    cursor.execute('''
        INSERT INTO suppliers_backuplog (id, filename, status, started_at, completed_at, file_size, error_message, backup_type, created_by_id)
        SELECT id, filename, status, started_at, completed_at, file_size, error_message, backup_type, created_by_id FROM suppliers_backuplog_old;
    ''')
    cursor.execute('DROP TABLE suppliers_backuplog_old;')

class Migration(migrations.Migration):
    dependencies = [
        ('suppliers', '0006_alter_user_groups_alter_user_user_permissions'),
    ]
    operations = [
        migrations.RunPython(rebuild_suppliers_tables),
    ] 