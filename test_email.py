import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print("Testing email configuration...")
    print(f"Email backend: {settings.EMAIL_BACKEND}")
    print(f"Email host: {settings.EMAIL_HOST}")
    print(f"Email port: {settings.EMAIL_PORT}")
    print(f"Email user: {settings.EMAIL_HOST_USER}")
    
    try:
        send_mail(
            'Test Email from Django',
            'This is a test email to verify the email configuration.',
            settings.DEFAULT_FROM_EMAIL,
            ['hamiltonwatchbrands@gmail.com'],  # Send to the same address for testing
            fail_silently=False,
        )
        print("Test email sent successfully!")
    except Exception as e:
        print(f"Error sending test email: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email() 