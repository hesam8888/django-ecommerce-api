from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer, Address
from myshop.admin import admin_site

class AddressInline(admin.TabularInline):
    model = Address
    extra = 0

class CustomerAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'city', 'state', 'country', 'is_active', 'is_staff', 'is_email_verified', 'login_method', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_email_verified', 'date_joined', 'country', 'state')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'street_address', 'city', 'state', 'country')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth')}),
        ('Address Information', {'fields': ('street_address', 'city', 'state', 'country', 'postal_code', 'address')}),
        ('Login Method', {'fields': ('login_method',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Email verification', {'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        ('Password reset', {'fields': ('password_reset_token', 'password_reset_sent_at')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at', 'email_verification_token', 'password_reset_token')
    inlines = [AddressInline]

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete users
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Only superusers can change users
        return request.user.is_superuser

# Register the Customer model with the custom admin site
admin_site.register(Customer, CustomerAdmin)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('customer', 'label', 'receiver_name', 'street_address', 'city', 'province', 'vahed', 'phone', 'country', 'postal_code', 'full_address', 'created_at')
    search_fields = ('customer__email', 'label', 'receiver_name', 'street_address', 'city', 'country', 'vahed', 'phone')
    list_filter = ('customer', 'country', 'city', 'label', 'province')
    readonly_fields = ('full_address', 'created_at', 'updated_at')
    fields = ('customer', 'label', 'receiver_name', 'street_address', 'city', 'province', 'vahed', 'phone', 'country', 'postal_code', 'full_address')

# Register Address with the custom admin site after the class is defined
admin_site.register(Address, AddressAdmin)
