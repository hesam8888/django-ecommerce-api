from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Category


class Command(BaseCommand):
    help = 'Change a category ID safely'
    
    def add_arguments(self, parser):
        parser.add_argument('old_id', type=int, help='Current category ID')
        parser.add_argument('new_id', type=int, help='New category ID')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force the change even if new ID exists',
        )
    
    def handle(self, *args, **options):
        old_id = options['old_id']
        new_id = options['new_id']
        force = options['force']
        
        try:
            # Check if old category exists
            old_category = Category.objects.get(id=old_id)
            self.stdout.write(f"Found category: {old_category.name} (ID: {old_id})")
            
            # Check if new ID already exists
            if Category.objects.filter(id=new_id).exists() and not force:
                self.stdout.write(
                    self.style.ERROR(f"Category with ID {new_id} already exists. Use --force to override.")
                )
                return
            
            # Perform the change in a transaction
            with transaction.atomic():
                # Use raw SQL to change the primary key
                from django.db import connection
                with connection.cursor() as cursor:
                    # Update the category ID
                    cursor.execute(
                        "UPDATE shop_category SET id = %s WHERE id = %s",
                        [new_id, old_id]
                    )
                    
                    # Update any child categories that reference this as parent
                    cursor.execute(
                        "UPDATE shop_category SET parent_id = %s WHERE parent_id = %s",
                        [new_id, old_id]
                    )
                    
                    # Update any products that reference this category
                    cursor.execute(
                        "UPDATE shop_product SET category_id = %s WHERE category_id = %s",
                        [new_id, old_id]
                    )
                    
                    # Update any category attributes
                    cursor.execute(
                        "UPDATE shop_categoryattribute SET category_id = %s WHERE category_id = %s",
                        [new_id, old_id]
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully changed category ID from {old_id} to {new_id}')
            )
            
        except Category.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Category with ID {old_id} does not exist")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error changing category ID: {str(e)}")
            ) 