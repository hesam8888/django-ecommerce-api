# Web-based Image Editor

A simple, modern web-based image editor built with Django and JavaScript. It supports image uploading, cropping, and rotation operations.

## Features

- **Image Upload**:
  - Supports JPG, PNG, and WEBP formats
  - File validation for type and size
  - Simple and user-friendly interface

- **Image Editing**:
  - **Crop**: Select any region of the image using an interactive rectangle selector
  - **Rotate**: Rotate the image left or right in 90-degree increments
  - **Download**: Download the edited image

## Technical Details

### Backend

- Built with Django 5.x
- Uses Pillow (PIL) for image processing operations
- Stores both original and edited images for recovery
- RESTful API endpoints for image operations

### Frontend

- Clean, responsive UI with Bootstrap 5
- Uses Cropper.js for the interactive cropping functionality
- Real-time feedback with AJAX calls to the backend
- Mobile-friendly design

## Integration Guide

To embed this image editor into another web application:

1. Include the `image_editor` app in your Django project
2. Add to INSTALLED_APPS in your settings.py:
   ```python
   INSTALLED_APPS = [
       # ... other apps
       'image_editor',
   ]
   ```
3. Include the URLs in your project's main urls.py:
   ```python
   urlpatterns = [
       # ... other URL patterns
       path('image-editor/', include('image_editor.urls')),
   ]
   ```
4. Run migrations to create the necessary database tables:
   ```
   python manage.py migrate image_editor
   ```
5. Make sure your project has the required media settings for image upload/storage:
   ```python
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```
6. For development, add these lines to your urls.py:
   ```python
   if settings.DEBUG:
       urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

## Dependencies

- Django 4.2+
- Pillow 10.0+
- Bootstrap 5 (frontend)
- Cropper.js (frontend)

## License

MIT License 