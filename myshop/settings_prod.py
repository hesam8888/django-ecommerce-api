from .settings import *

import os
from pathlib import Path

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Get allowed hosts from environment or use default
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Use environment variable for secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secure-secret-key-here')

# Database configuration for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'your_db_name'),
        'USER': os.environ.get('DB_USER', 'your_db_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# For Render.com, use DATABASE_URL if available
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(os.environ.get('DATABASE_URL'))

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session Configuration for production (inherit from main settings but ensure secure cookies)
SESSION_COOKIE_SECURE = True  # Use HTTPS for session cookies in production
CSRF_COOKIE_SECURE = True  # Use HTTPS for CSRF cookies in production

# Static and media files
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Update site URL for production
SITE_URL = 'https://your-domain.com'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-specific-password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER 