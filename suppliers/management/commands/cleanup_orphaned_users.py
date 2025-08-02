from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from suppliers.models import SupplierAdmin
User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up orphaned users that were supplier admins but their suppliers were deleted'

    def handle(self, *args, **options):
        # Get all users marked as supplier_admin
        supplier_admin_users = User.objects.filter(is_supplier_admin=True)
        orphaned_users = []
        
        # Find users that are marked as supplier admins but have no supplier admin role
        for user in supplier_admin_users:
            if not SupplierAdmin.objects.filter(user=user).exists():
                orphaned_users.append(user)
                self.stdout.write(self.style.WARNING(f"Found orphaned user: {user.username} ({user.email})"))
                
        # Ask for confirmation before deleting
        if orphaned_users:
            self.stdout.write(f"Found {len(orphaned_users)} orphaned users.")
            confirm = input("Do you want to delete these orphaned users? (yes/no): ")
            
            if confirm.lower() == 'yes':
                for user in orphaned_users:
                    user_id = user.id
                    username = user.username
                    user.delete()
                    self.stdout.write(self.style.SUCCESS(f"Deleted orphaned user: {username} (ID: {user_id})"))
                self.stdout.write(self.style.SUCCESS(f"Successfully deleted {len(orphaned_users)} orphaned users."))
            else:
                self.stdout.write(self.style.WARNING("Operation cancelled."))
        else:
            self.stdout.write(self.style.SUCCESS("No orphaned users found. Everything is clean!")) 