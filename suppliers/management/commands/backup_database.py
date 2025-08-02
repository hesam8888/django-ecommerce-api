import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from suppliers.models import BackupLog
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates a backup of the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='full',
            help='Type of backup (full, incremental)'
        )
        parser.add_argument(
            '--user',
            type=int,
            help='ID of the user creating the backup'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        user_id = options.get('user')
        
        # Create backup log entry
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{backup_type}_{timestamp}.sql'
        backup_log = BackupLog.objects.create(
            filename=filename,
            status='in_progress',
            backup_type=backup_type,
            created_by_id=user_id
        )

        try:
            # Get database settings
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_password = db_settings['PASSWORD']
            db_host = db_settings['HOST']
            db_port = db_settings['PORT']

            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, filename)

            # Construct pg_dump command
            cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', db_port,
                '-U', db_user,
                '-F', 'c',  # Custom format
                '-f', backup_path,
                db_name
            ]

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            # Execute backup command
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                error_message = stderr.decode()
                backup_log.mark_failed(error_message)
                self.stdout.write(self.style.ERROR(f'Backup failed: {error_message}'))
                return

            # Get file size
            file_size = os.path.getsize(backup_path)
            backup_log.mark_completed(file_size)

            self.stdout.write(self.style.SUCCESS(f'Successfully created backup: {filename}'))
            self.stdout.write(f'Backup size: {backup_log.file_size_display}')

        except Exception as e:
            error_message = str(e)
            backup_log.mark_failed(error_message)
            self.stdout.write(self.style.ERROR(f'Backup failed: {error_message}'))
            logger.exception('Backup failed') 