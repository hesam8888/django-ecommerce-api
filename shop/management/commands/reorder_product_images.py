from django.core.management.base import BaseCommand
from shop.models import Product, ProductImage

class Command(BaseCommand):
    help = 'Reorder all product images based on their creation date'

    def handle(self, *args, **options):
        products = Product.objects.all()
        for product in products:
            images = product.images.all().order_by('created_at')
            for i, image in enumerate(images):
                image.order = i
                image.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reordered images for product {product.name}')
            ) 