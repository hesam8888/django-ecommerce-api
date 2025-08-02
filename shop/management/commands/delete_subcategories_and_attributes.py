from django.core.management.base import BaseCommand
from shop.models import Category, SubcategoryAttribute, Product

class Command(BaseCommand):
    help = 'Delete all subcategories (categories with a parent) and their related subcategory attributes and products.'

    def handle(self, *args, **options):
        subcategories = Category.objects.filter(parent__isnull=False)
        subcat_count = subcategories.count()
        product_count = Product.objects.filter(category__in=subcategories).count()
        subcat_attr_count = SubcategoryAttribute.objects.filter(subcategory__in=subcategories).count()

        self.stdout.write(self.style.WARNING(f"This will delete:"))
        self.stdout.write(self.style.WARNING(f"- {subcat_count} subcategories"))
        self.stdout.write(self.style.WARNING(f"- {product_count} products in those subcategories"))
        self.stdout.write(self.style.WARNING(f"- {subcat_attr_count} subcategory attribute assignments"))
        self.stdout.write(self.style.WARNING("This operation cannot be undone!"))
        confirm = input("Type 'yes' to proceed: ")
        if confirm.strip().lower() != 'yes':
            self.stdout.write(self.style.ERROR("Aborted."))
            return

        # Delete products (will cascade with subcategory deletion, but explicit for clarity)
        Product.objects.filter(category__in=subcategories).delete()
        # Delete subcategory attributes
        SubcategoryAttribute.objects.filter(subcategory__in=subcategories).delete()
        # Delete subcategories
        subcategories.delete()

        self.stdout.write(self.style.SUCCESS("All subcategories, their products, and subcategory attributes have been deleted.")) 