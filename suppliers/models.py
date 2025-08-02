import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string

class User(AbstractUser):
    """Custom user model for the suppliers app"""
    is_supplier = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)

    # Fix field clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='supplier_set',
        related_query_name='supplier'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='supplier_set',
        related_query_name='supplier'
    )

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        
    def __str__(self):
        return str(self.username)

    @property
    def is_supplier_admin(self):
        """Check if user has a supplier admin record"""
        return hasattr(self, 'supplier_admin_profile') and self.supplier_admin_profile.is_active

class Supplier(models.Model):
    """Model for supplier information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_profile')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Create a record in DeletedSupplier before deleting
        DeletedSupplier.objects.create(
            original_id=self.id,
            name=self.name,
            email=self.email,
            phone=self.phone,
            address=self.address,
            description=self.description,
            deleted_by=kwargs.get('deleted_by'),
            deletion_reason=kwargs.get('deletion_reason', '')
        )
        super().delete(*args, **kwargs)

class Store(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.supplier.name})"

class SupplierAdmin(models.Model):
    """Model for supplier admin information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier_admin_profile')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='admins')
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('supplier admin')
        verbose_name_plural = _('supplier admins')

    def __str__(self):
        return f"{self.user.username} - {self.supplier.name}"

class SupplierInvitation(models.Model):
    """New simplified supplier invitation model"""
    email = models.EmailField(help_text="Supplier's email address")
    store_name = models.CharField(max_length=100, help_text="Name of the store/brand")
    owner_name = models.CharField(max_length=100, blank=True, help_text="Owner's full name")
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Store address")
    
    # Invitation details
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Email Sent'),
            ('accepted', 'Accepted'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    
    # Admin tracking
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sent_invitations',
        help_text="Admin who sent this invitation"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Admin notes about this invitation")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Supplier Invitation'
        verbose_name_plural = 'Supplier Invitations'

    def save(self, *args, **kwargs):
        # Generate token and expiry if this is a new invitation
        if not self.pk:
            self.token = get_random_string(length=32)
            self.expires_at = timezone.now() + timedelta(hours=72)  # 3 days expiry
        
        super().save(*args, **kwargs)
        
        # Send email if this is a new invitation and not already sent
        if not self.is_sent and self.status == 'pending':
            self.send_invitation_email()

    def is_valid(self):
        """Check if invitation is still valid"""
        return (
            not self.is_used and
            self.status in ['pending', 'sent'] and
            timezone.now() < self.expires_at
        )

    def send_invitation_email(self):
        """Send invitation email to supplier"""
        try:
            # Generate registration URL
            registration_url = reverse('suppliers:register', kwargs={'token': self.token})
            full_url = f"{settings.SITE_URL}{registration_url}"
            
            # Email content
            subject = f"Invitation to join {self.store_name} as a supplier"
            
            message = f"""
Dear {self.owner_name},

You have been invited to join {self.store_name} as a supplier on our platform.

Store Information:
- Store Name: {self.store_name}
- Your Email: {self.email}
- Contact Phone: {self.phone or 'Not provided'}

To complete your registration, please click the following link:
{full_url}

This invitation will expire in 72 hours.

If you have any questions, please contact us.

Best regards,
Your Platform Team
            """
            
            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.email],
                fail_silently=False,
            )
            
            # Update status
            self.is_sent = True
            self.status = 'sent'
            self.save(update_fields=['is_sent', 'status'])
            
            return True
            
        except Exception as e:
            print(f"Error sending invitation email: {e}")
            return False

    def mark_as_used(self, user):
        """Mark invitation as used when supplier registers"""
        self.is_used = True
        self.status = 'accepted'
        self.save(update_fields=['is_used', 'status'])

    def __str__(self):
        return f"Invitation for {self.email} - {self.store_name}"

class BackupLog(models.Model):
    """Model for tracking database backup operations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True, help_text="Size in bytes")
    error_message = models.TextField(blank=True, null=True)
    backup_type = models.CharField(max_length=50, default='full', help_text="Type of backup (full, incremental, etc.)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='backup_logs')

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Backup Log'
        verbose_name_plural = 'Backup Logs'

    def __str__(self):
        return f"{self.filename} - {self.status} ({self.started_at})"

    def mark_completed(self, file_size=None):
        self.status = 'completed'
        self.completed_at = timezone.now()
        if file_size is not None:
            self.file_size = file_size
        self.save()

    def mark_failed(self, error_message):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()

    @property
    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return timezone.now() - self.started_at

    @property
    def file_size_display(self):
        if not self.file_size:
            return "N/A"
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

class DeletedSupplier(models.Model):
    """Model for tracking deleted suppliers"""
    original_id = models.IntegerField(help_text="Original ID of the supplier")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    description = models.TextField(blank=True)
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deleted_suppliers')
    deletion_reason = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('deleted supplier')
        verbose_name_plural = _('deleted suppliers')
        ordering = ['-deleted_at']

    def __str__(self):
        return f"Deleted: {self.name}"
