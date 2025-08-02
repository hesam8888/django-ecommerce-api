from django.core.management.base import BaseCommand
from shop.models import Category

class Command(BaseCommand):
    help = 'Automatically categorize existing categories based on their structure and content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update categories even if they already have a non-auto type'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write("Analyzing existing categories...")
        
        categories = Category.objects.all()
        updates = []
        
        for category in categories:
            current_type = category.category_type
            effective_type = category.get_effective_category_type()
            
            # Only update if it's auto or if forced
            if current_type == 'auto' or force:
                if current_type != effective_type:
                    updates.append({
                        'category': category,
                        'old_type': current_type,
                        'new_type': effective_type,
                        'reason': self._get_reason(category)
                    })
        
        if not updates:
            self.stdout.write(
                self.style.SUCCESS('No categories need updating.')
            )
            return
        
        # Display planned changes
        self.stdout.write(f"\nFound {len(updates)} categories to update:")
        self.stdout.write("-" * 80)
        
        for update in updates:
            category = update['category']
            self.stdout.write(
                f"Category: {category.name} (ID: {category.id})\n"
                f"  Current type: {update['old_type']}\n"
                f"  New type: {update['new_type']}\n"
                f"  Reason: {update['reason']}\n"
                f"  Has subcategories: {category.subcategories.exists()}\n"
                f"  Has direct products: {category.product_set.filter(is_active=True).exists()}\n"
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDry run mode - no changes made.')
            )
            return
        
        # Apply changes
        self.stdout.write("\nApplying changes...")
        
        for update in updates:
            category = update['category']
            category.category_type = update['new_type']
            category.save()
            
            self.stdout.write(
                f"Updated {category.name} to type '{update['new_type']}'"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully updated {len(updates)} categories.')
        )
        
        # Summary
        self.stdout.write("\nCategory Summary:")
        container_count = Category.objects.filter(category_type='container').count()
        direct_count = Category.objects.filter(category_type='direct').count()
        auto_count = Category.objects.filter(category_type='auto').count()
        
        self.stdout.write(f"Container categories: {container_count}")
        self.stdout.write(f"Direct categories: {direct_count}")
        self.stdout.write(f"Auto-detect categories: {auto_count}")
    
    def _get_reason(self, category):
        """Get a human-readable reason for the categorization"""
        has_subcategories = category.subcategories.exists()
        has_direct_products = category.product_set.filter(is_active=True).exists()
        
        if has_subcategories and not has_direct_products:
            return "Has subcategories, no direct products → Container"
        elif not has_subcategories and has_direct_products:
            return "No subcategories, has direct products → Direct"
        elif has_subcategories and has_direct_products:
            return "Has both subcategories and products → Container (default)"
        else:
            return "No subcategories or products → Direct (default)" 