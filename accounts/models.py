from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        # Generate username from email
        username = email.split('@')[0]
        # Ensure username is unique
        base_username = username
        counter = 1
        while Customer.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        extra_fields['username'] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class Customer(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Address fields
    address = models.TextField(blank=True)  # Keep for backward compatibility
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    date_of_birth = models.DateField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Fix field clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='customer_set',
        related_query_name='customer'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='customer_set',
        related_query_name='customer'
    )
    
    LOGIN_METHOD_CHOICES = [
        ('email', 'Email'),
        ('google', 'Google'),
        ('other', 'Other'),
    ]
    login_method = models.CharField(
        max_length=20,
        choices=LOGIN_METHOD_CHOICES,
        default='email',
        help_text='How the user logged in or registered (email, google, etc.)'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomerManager()
    
    class Meta:
        verbose_name = _('customer')
        verbose_name_plural = _('customers')
        
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_address(self):
        """Return formatted full address"""
        address_parts = []
        if self.street_address:
            address_parts.append(self.street_address)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        return ', '.join(address_parts) if address_parts else self.address
    
    def generate_email_verification_token(self):
        self.email_verification_token = uuid.uuid4()
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token

    def save(self, *args, **kwargs):
        if not self.username:
            # Generate username from email if not set
            self.username = self.email.split('@')[0]
            # Ensure username is unique
            base_username = self.username
            counter = 1
            while Customer.objects.filter(username=self.username).exists():
                self.username = f"{base_username}{counter}"
                counter += 1
        super().save(*args, **kwargs)

# --- SIGNAL TO CREATE CUSTOMER ON USER CREATION ---
@receiver(post_save, sender=Customer)
def create_customer_profile(sender, instance, created, **kwargs):
    # This ensures that a Customer object is created for every new user (including social login)
    if created:
        # You can add additional logic here if needed
        pass  # Customer is already the user model, so nothing to do

class Address(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, blank=True, help_text='e.g. Home, Work, etc.')
    receiver_name = models.CharField(max_length=100, blank=False, help_text='Name of the person receiving the package')
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100, blank=True)
    vahed = models.CharField(max_length=20, help_text='واحد', default="")
    phone = models.CharField(max_length=20, help_text='Phone number', default="")
    country = models.CharField(max_length=100, default='ایران')
    postal_code = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_address(self):
        parts = [
            self.receiver_name if self.receiver_name else None,
            self.street_address,
            f"واحد {self.vahed}",
            self.city,
            self.province,
            self.country,
            self.postal_code,
            f"تلفن {self.phone}"
        ]
        return ', '.join([str(p) for p in parts if p])

    def __str__(self):
        return f"{self.label or 'Address'}: {self.full_address}"
