from django import forms
from .models import EditedImage

class ImageUploadForm(forms.ModelForm):
    """Form for uploading images to be edited."""
    
    class Meta:
        model = EditedImage
        fields = ['original_image']
        
    def clean_original_image(self):
        """Validate that uploaded image is of an acceptable format and size."""
        image = self.cleaned_data.get('original_image')
        
        # Check file format
        if image:
            ext = image.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                raise forms.ValidationError(
                    "Unsupported file format. Please upload a JPG, PNG, or WEBP image."
                )
            
            # Check file size (limit to 10MB)
            if image.size > 10 * 1024 * 1024:  # 10MB in bytes
                raise forms.ValidationError(
                    "The image file is too large. Maximum size is 10MB."
                )
                
        return image 