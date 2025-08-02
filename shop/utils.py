from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import warnings

# Suppress ICC profile warnings
warnings.filterwarnings('ignore', category=UserWarning, module='PIL')

def safe_open_image(image_path_or_file):
    """
    Safely open an image and strip problematic ICC profiles.
    
    Args:
        image_path_or_file: Path to image file or file-like object
    
    Returns:
        PIL.Image: Image object with ICC profile stripped if problematic
    """
    try:
        img = Image.open(image_path_or_file)
        
        # Check if image has ICC profile and strip it if present
        if hasattr(img, 'info') and 'icc_profile' in img.info:
            # Create a new image without the ICC profile
            img_data = list(img.getdata())
            new_img = Image.new(img.mode, img.size)
            new_img.putdata(img_data)
            return new_img
        
        return img
    except Exception as e:
        # If there's any error opening the image, try without ICC profile
        warnings.warn(f"Error opening image, attempting without ICC profile: {e}")
        img = Image.open(image_path_or_file)
        img_data = list(img.getdata())
        new_img = Image.new(img.mode, img.size)
        new_img.putdata(img_data)
        return new_img

def compress_image(image_file, max_size=1600):
    """
    Compress an uploaded image while maintaining quality.
    
    Args:
        image_file: The uploaded image file (InMemoryUploadedFile)
        max_size: Maximum width/height in pixels (default: 1600)
    
    Returns:
        InMemoryUploadedFile: Compressed image ready to be saved
    """
    # Skip compression if the file is too large (> 20MB)
    if hasattr(image_file, 'size') and image_file.size > 20 * 1024 * 1024:
        return image_file
        
    # Open the image using PIL with ICC profile handling
    img = safe_open_image(image_file)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Calculate new dimensions while maintaining aspect ratio
    width, height = img.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create a BytesIO object to store the compressed image
    output = BytesIO()
    
    # Save the image in WebP format with specified settings
    img.save(
        output,
        format='WEBP',
        quality=80,
        method=6,
        optimize=True,
        lossless=False,
        icc_profile=None  # Explicitly exclude ICC profile
    )
    
    # Reset the pointer to the beginning of the BytesIO object
    output.seek(0)
    
    # Create a new InMemoryUploadedFile with the original file name
    original_name = image_file.name
    if not original_name.lower().endswith('.webp'):
        original_name = os.path.splitext(original_name)[0] + '.webp'
    
    return InMemoryUploadedFile(
        output,
        'ImageField',
        original_name,
        'image/webp',
        output.getbuffer().nbytes,
        None
    ) 