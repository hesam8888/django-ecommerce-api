from django.core.management.base import BaseCommand
from accounts.models import Address, Customer
from django.db.models import OuterRef, Subquery, Exists

class Command(BaseCommand):
    help = 'Delete all Address objects whose customer_id does not exist in the Customer table.'

    def handle(self, *args, **options):
        # Find orphaned addresses
        orphaned_addresses = Address.objects.filter(~Exists(Customer.objects.filter(id=OuterRef('customer_id'))))
        count = orphaned_addresses.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No orphaned addresses found.'))
            return
        orphaned_addresses.delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} orphaned address(es).')) 