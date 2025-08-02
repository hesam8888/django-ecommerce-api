from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth import get_user_model
from suppliers.models import Supplier, Store, SupplierAdmin, SupplierInvitation, BackupLog
from suppliers.admin import BackupLogAdmin

SupplierUser = get_user_model()

class MyShopAdminSite(AdminSite):
    def has_permission(self, request):
        """
        Allow access to the admin site if the user is:
        1. A staff member
        2. A supplier admin (has SupplierAdmin record)
        """
        if not request.user.is_active:
            return False
            
        if request.user.is_staff:
            return True
            
        # Check if user has a SupplierAdmin record
        return SupplierAdmin.objects.filter(user=request.user, is_active=True).exists()

admin_site = MyShopAdminSite(name='admin')

# Register the default models
admin_site.register(Group, GroupAdmin)

# Register supplier models with the custom admin site
admin_site.register(Supplier)
admin_site.register(Store)
admin_site.register(SupplierAdmin)
admin_site.register(SupplierInvitation)
admin_site.register(BackupLog, BackupLogAdmin) 