from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.db.utils import IntegrityError
from .models import User, Supplier, Store, SupplierAdmin as SupplierAdminModel, SupplierInvitation, BackupLog, DeletedSupplier
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.contrib import messages
from django import forms

User = get_user_model()

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_supplier')
    list_filter = ('is_staff', 'is_supplier', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_supplier', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_supplier'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('supplier_profile', 'supplier_admin_profile')

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        # Prevent deletion of users with active supplier profiles
        if hasattr(obj, 'supplier_profile') and obj.supplier_profile.is_active:
            return False
        return True

class StoreInline(admin.TabularInline):
    model = Store
    extra = 0

class SupplierAdminInline(admin.TabularInline):
    model = SupplierAdminModel
    extra = 0

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    inlines = [SupplierAdminInline]

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'supplier')
    search_fields = ('name', 'address', 'supplier__name')

@admin.register(SupplierAdminModel)
class SupplierAdminRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'supplier', 'role', 'is_active', 'created_at')
    list_filter = ('is_active', 'role', 'created_at')
    search_fields = ('user__username', 'supplier__name', 'role')

class SupplierInvitationChangeForm(forms.ModelForm):
    class Meta:
        model = SupplierInvitation
        fields = ['email', 'store_name', 'owner_name', 'phone', 'address', 'status', 'notes']
        exclude = ['token', 'created_at', 'expires_at', 'is_used', 'is_sent', 'created_by']

class SupplierInvitationAddForm(forms.ModelForm):
    class Meta:
        model = SupplierInvitation
        fields = ['email', 'store_name', 'owner_name', 'phone', 'address', 'notes']
        exclude = ['token', 'created_at', 'expires_at', 'is_used', 'is_sent', 'status', 'created_by']

@admin.register(SupplierInvitation)
class SupplierInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'store_name', 'owner_name', 'status', 'created_at', 'is_used', 'email_status')
    list_filter = ('status', 'is_used', 'created_at', 'is_sent')
    search_fields = ('email', 'store_name', 'owner_name')
    readonly_fields = ('created_at', 'expires_at', 'is_sent', 'token')
    actions = ['send_invitation_emails']
    
    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return SupplierInvitationAddForm
        return SupplierInvitationChangeForm
    
    def get_fieldsets(self, request, obj=None):
        if obj is None:  # Add form
            fieldsets = (
                (None, {
                    'fields': ('email', 'store_name')
                }),
                ('Owner Information', {
                    'fields': ('owner_name', 'phone', 'address')
                }),
                ('Notes', {
                    'fields': ('notes',)
                }),
            )
        else:  # Change form
            fieldsets = (
                (None, {
                    'fields': ('email', 'store_name')
                }),
                ('Owner Information', {
                    'fields': ('owner_name', 'phone', 'address')
                }),
                ('Status', {
                    'fields': ('status',)
                }),
                ('Email Status', {
                    'fields': ('is_sent',)
                }),
                ('Notes', {
                    'fields': ('notes',)
                }),
            )
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        # Set the created_by field if this is a new invitation
        if not change:
            obj.created_by = request.user
        
        # Save the model (email will be sent automatically by the model's save method)
        super().save_model(request, obj, form, change)

    def email_status(self, obj):
        if obj.is_sent:
            return format_html('<span style="color:green;">✓ Sent</span>')
        return format_html('<span style="color:red;">✗ Not sent</span>')
    email_status.short_description = 'Email Status'
    
    def send_invitation_emails(self, request, queryset):
        success_count = 0
        for invitation in queryset:
            if not invitation.is_sent:
                if invitation.send_invitation_email():
                    success_count += 1
        
        if success_count:
            self.message_user(request, f"Successfully sent {success_count} invitation emails.")
        else:
            self.message_user(request, "No invitation emails were sent.", level=messages.WARNING)
    send_invitation_emails.short_description = "Send invitation emails to selected invitations"

class BackupLogAdmin(admin.ModelAdmin):
    list_display = ('filename', 'status', 'backup_type', 'started_at', 'completed_at', 'duration_display', 'file_size_display', 'created_by')
    list_filter = ('status', 'backup_type', 'started_at', 'created_by')
    search_fields = ('filename', 'error_message')
    readonly_fields = ('started_at', 'completed_at', 'file_size', 'error_message')
    date_hierarchy = 'started_at'
    
    def duration_display(self, obj):
        duration = obj.duration
        if duration:
            total_seconds = duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "N/A"
    duration_display.short_description = 'Duration'
    
    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = 'File Size'
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of backup logs
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent manual editing of backup logs

class DeletedSupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'deleted_at', 'deleted_by')
    list_filter = ('deleted_at',)
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('original_id', 'name', 'email', 'phone', 'address', 
                      'description', 'deleted_at', 'deleted_by', 'deletion_reason')
    ordering = ('-deleted_at',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Register the new admin class
admin.site.register(DeletedSupplier, DeletedSupplierAdmin)
