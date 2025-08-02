from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('direct-dashboard/', views.direct_dashboard, name='direct_dashboard'),
    path('register/<str:token>/', views.register_with_token, name='register'),
    path('login/', views.SupplierLoginView.as_view(), name='login'),
    path('logout/', views.supplier_logout, name='logout'),
    path('dashboard/', views.SupplierDashboardView.as_view(), name='dashboard'),
    path('products/', views.ProductsExplorerView.as_view(), name='products_explorer'),
    path('select-supplier/', views.select_supplier, name='select_supplier'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('bulk-delete-products/', views.bulk_delete_products, name='bulk_delete_products'),
    path('sold-items/', views.sold_items, name='sold_items'),
    path('test-add-product/', views.test_add_product, name='test_add_product'),
    path('send-invitation/', views.send_supplier_invitation, name='send_invitation'),
    path('api/products/<int:product_id>/', views.product_detail_api, name='product_detail_api'),
    path('api/debug/<int:product_id>/', views.product_debug_api, name='product_debug_api'),
    # Backup URLs
    path('admin/backup/', views.backup_dashboard, name='backup_dashboard'),
    path('admin/backup/create/', views.create_backup, name='create_backup'),
    path('admin/backup/status/', views.get_backup_status, name='backup_status'),
    path('admin/backup/download/<int:backup_id>/', views.download_backup, name='download_backup'),
] 