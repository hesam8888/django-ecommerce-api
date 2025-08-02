from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'localhost', '127.0.0.1']

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your_cpanel_db_name',
        'USER': 'your_cpanel_db_user',
        'PASSWORD': 'your_cpanel_db_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Allow all hosts for development server
ALLOWED_HOSTS = ['*'] 