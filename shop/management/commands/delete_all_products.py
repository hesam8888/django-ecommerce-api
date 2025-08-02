from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete all products from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Email of the user performing the deletion (for audit trail)',
        )

    def handle(self, *args, **options):
        product_count = Product.objects.count()
        
        if product_count == 0:
            self.stdout.write(
                self.style.WARNING('No products found in the database.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'Found {product_count} products in the database.')
        )

        if not options['force']:
            confirm = input(
                f'Are you sure you want to delete ALL {product_count} products? This action cannot be undone. (yes/no): '
            )
            if confirm.lower() != 'yes':
                self.stdout.write(
                    self.style.ERROR('Deletion cancelled.')
                )
                return

        # Get the user for audit trail
        user = None
        if options['user']:
            try:
                user = User.objects.get(email=options['user'])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'User with email {options["user"]} not found. Proceeding without user audit trail.')
                )

        deleted_count = 0
        
        with transaction.atomic():
            # Delete products in batches to avoid memory issues
            batch_size = 100
            products = Product.objects.all()
            
            for i in range(0, product_count, batch_size):
                batch = products[i:i + batch_size]
                
                for product in batch:
                    # Set the user for audit trail
                    if user:
                        product._current_user = user
                    
                    # Delete the product (this will create DeletedProduct record)
                    product.delete()
                    deleted_count += 1
                    
                    if deleted_count % 10 == 0:
                        self.stdout.write(f'Deleted {deleted_count}/{product_count} products...')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} products.')
        )
        
        if user:
            self.stdout.write(
                self.style.SUCCESS(f'Deletion performed by: {user.email}')
            ) 