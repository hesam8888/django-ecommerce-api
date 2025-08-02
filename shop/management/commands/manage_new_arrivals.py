from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from shop.models import Product


class Command(BaseCommand):
    help = 'Manage new arrivals products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mark-recent',
            type=int,
            help='Mark products created in the last N days as new arrivals',
        )
        parser.add_argument(
            '--unmark-old',
            type=int,
            help='Unmark products older than N days from new arrivals',
        )
        parser.add_argument(
            '--mark-product',
            type=int,
            help='Mark specific product ID as new arrival',
        )
        parser.add_argument(
            '--unmark-product',
            type=int,
            help='Unmark specific product ID from new arrivals',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all new arrivals products',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Remove new arrival status from all products',
        )

    def handle(self, *args, **options):
        if options['mark_recent']:
            self.mark_recent_products(options['mark_recent'])
        
        elif options['unmark_old']:
            self.unmark_old_products(options['unmark_old'])
        
        elif options['mark_product']:
            self.mark_single_product(options['mark_product'])
        
        elif options['unmark_product']:
            self.unmark_single_product(options['unmark_product'])
        
        elif options['list']:
            self.list_new_arrivals()
        
        elif options['clear_all']:
            self.clear_all_new_arrivals()
        
        else:
            self.stdout.write(
                self.style.ERROR('Please specify an action. Use --help for available options.')
            )

    def mark_recent_products(self, days):
        """Mark products created in the last N days as new arrivals"""
        cutoff_date = timezone.now() - timedelta(days=days)
        products = Product.objects.filter(
            created_at__gte=cutoff_date,
            is_new_arrival=False,
            is_active=True
        )
        
        count = products.count()
        if count == 0:
            self.stdout.write(
                self.style.WARNING(f'No products found created in the last {days} days.')
            )
            return
        
        products.update(is_new_arrival=True)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully marked {count} products as new arrivals '
                f'(created in the last {days} days).'
            )
        )

    def unmark_old_products(self, days):
        """Unmark products older than N days from new arrivals"""
        cutoff_date = timezone.now() - timedelta(days=days)
        products = Product.objects.filter(
            created_at__lt=cutoff_date,
            is_new_arrival=True
        )
        
        count = products.count()
        if count == 0:
            self.stdout.write(
                self.style.WARNING(f'No new arrival products found older than {days} days.')
            )
            return
        
        products.update(is_new_arrival=False)
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully unmarked {count} products from new arrivals '
                f'(older than {days} days).'
            )
        )

    def mark_single_product(self, product_id):
        """Mark a specific product as new arrival"""
        try:
            product = Product.objects.get(id=product_id)
            if product.is_new_arrival:
                self.stdout.write(
                    self.style.WARNING(f'Product "{product.name}" is already marked as new arrival.')
                )
            else:
                product.mark_as_new_arrival()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully marked product "{product.name}" as new arrival.')
                )
        except Product.DoesNotExist:
            raise CommandError(f'Product with ID {product_id} does not exist.')

    def unmark_single_product(self, product_id):
        """Unmark a specific product from new arrivals"""
        try:
            product = Product.objects.get(id=product_id)
            if not product.is_new_arrival:
                self.stdout.write(
                    self.style.WARNING(f'Product "{product.name}" is not marked as new arrival.')
                )
            else:
                product.unmark_as_new_arrival()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully unmarked product "{product.name}" from new arrivals.')
                )
        except Product.DoesNotExist:
            raise CommandError(f'Product with ID {product_id} does not exist.')

    def list_new_arrivals(self):
        """List all new arrivals products"""
        new_arrivals = Product.objects.filter(is_new_arrival=True).order_by('-created_at')
        
        if not new_arrivals.exists():
            self.stdout.write(
                self.style.WARNING('No products are currently marked as new arrivals.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {new_arrivals.count()} new arrival products:')
        )
        self.stdout.write('')
        
        for product in new_arrivals:
            status = "Active" if product.is_active else "Inactive"
            self.stdout.write(
                f'ID: {product.id:4d} | {product.name[:50]:50s} | '
                f'{product.category.name[:20]:20s} | {status:8s} | '
                f'{product.created_at.strftime("%Y-%m-%d")}'
            )

    def clear_all_new_arrivals(self):
        """Remove new arrival status from all products"""
        if not self.confirm_action('This will remove new arrival status from ALL products. Continue?'):
            self.stdout.write('Operation cancelled.')
            return
        
        count = Product.objects.filter(is_new_arrival=True).update(is_new_arrival=False)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully removed new arrival status from {count} products.')
        )

    def confirm_action(self, message):
        """Ask for user confirmation"""
        answer = input(f'{message} [y/N]: ').lower().strip()
        return answer in ['y', 'yes'] 