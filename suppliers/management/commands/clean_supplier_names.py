from django.core.management.base import BaseCommand
from suppliers.models import Supplier

class Command(BaseCommand):
    help = 'Removes "\'s Store" suffix from all supplier names'

    def handle(self, *args, **options):
        suppliers = Supplier.objects.all()
        updated_count = 0
        
        for supplier in suppliers:
            if "'s Store" in supplier.name:
                old_name = supplier.name
                supplier.name = supplier.name.replace("'s Store", "")
                supplier.save(update_fields=['name'])
                updated_count += 1
                self.stdout.write(f"Updated: '{old_name}' → '{supplier.name}'")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} supplier names')) 