from django.db import models
import os
from django.conf import settings
from django.utils import timezone

# Create your models here.

class EditedImage(models.Model):
    """Model to store uploaded and edited images."""
    original_image = models.ImageField(upload_to='edited_images/originals/')
    edited_image = models.ImageField(upload_to='edited_images/edited/', blank=True, null=True)
    upload_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Image {self.id} - {os.path.basename(self.original_image.name)}"
    
    def delete(self, *args, **kwargs):
        """
        Override delete to handle image file deletion carefully.
        We ensure the image file exists before trying to delete it.
        """
        try:
            # Delete the original image file if it exists
            if self.original_image and hasattr(self.original_image, 'path'):
                if os.path.isfile(self.original_image.path):
                    os.remove(self.original_image.path)
            
            # Delete the edited image file if it exists
            if self.edited_image and hasattr(self.edited_image, 'path'):
                if os.path.isfile(self.edited_image.path):
                    os.remove(self.edited_image.path)
        except Exception as e:
            print(f"Error deleting image files: {e}")
                
        super().delete(*args, **kwargs)
