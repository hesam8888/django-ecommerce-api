from django.core.management.base import BaseCommand
from shop.models import Category

class Command(BaseCommand):
    help = 'Set up visibility and display sections for existing categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("Setting up category visibility and sections...")
        
        categories = Category.objects.all()
        updates = []
        
        for category in categories:
            # Determine visibility
            is_visible = not category.is_container_category()  # Only leaf categories visible
            
            # Determine display section
            section = category.get_display_section()
            
            # Check if updates needed
            needs_update = (
                category.is_visible != is_visible or 
                category.display_section != section
            )
            
            if needs_update:
                updates.append({
                    'category': category,
                    'old_visible': category.is_visible,
                    'new_visible': is_visible,
                    'old_section': category.display_section,
                    'new_section': section,
                    'reason': self._get_reason(category, is_visible, section)
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
                f"  Visibility: {update['old_visible']} → {update['new_visible']}\n"
                f"  Section: {update['old_section']} → {update['new_section']}\n"
                f"  Reason: {update['reason']}\n"
                f"  Type: {category.get_effective_category_type()}\n"
                f"  Product Count: {category.get_product_count()}\n"
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
            category.is_visible = update['new_visible']
            category.display_section = update['new_section']
            category.save()
            
            self.stdout.write(
                f"Updated {category.name}: visible={update['new_visible']}, section={update['new_section']}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully updated {len(updates)} categories.')
        )
        
        # Summary
        self.stdout.write("\nCategory Summary:")
        visible_count = Category.objects.filter(is_visible=True).count()
        hidden_count = Category.objects.filter(is_visible=False).count()
        
        self.stdout.write(f"Visible categories: {visible_count}")
        self.stdout.write(f"Hidden categories: {hidden_count}")
        
        # Section breakdown
        for section in ['men', 'women', 'unisex', 'general']:
            count = Category.objects.filter(display_section=section).count()
            self.stdout.write(f"{section.capitalize()} section: {count}")
    
    def _get_reason(self, category, is_visible, section):
        """Get a human-readable reason for the changes"""
        if category.is_container_category():
            return f"Container category → Hidden (is_visible=False)"
        else:
            gender = category.get_gender()
            if gender == 'مردانه':
                return f"Men's category → Visible in 'men' section"
            elif gender == 'زنانه':
                return f"Women's category → Visible in 'women' section"
            elif gender == 'یونیسکس':
                return f"Unisex category → Visible in 'unisex' section"
            else:
                return f"General category → Visible in 'general' section" 