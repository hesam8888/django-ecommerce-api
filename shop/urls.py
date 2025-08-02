from django.urls import path
from . import views
from .api_views import (
    CategoryProductFilterView, ProductsFilterView, debug_category1_attributes, 
    debug_category_attributes_structure, cleanup_product_attributes, assign_sample_attributes,
    WishlistListCreateAPIView, WishlistDestroyAPIView, toggle_wishlist, wishlist_status,
    api_categories_with_gender, api_products_by_gender_category, api_unified_products,
    api_organized_categories, api_direct_categories
)

app_name = 'shop'

urlpatterns = [
    path('reorder-images/', views.reorder_images, name='reorder_images'),
    path('product/<int:product_id>/sort-images/', views.sort_product_images, name='sort_product_images'),
    path('productimage/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),
    path('productimage/<int:image_id>/update-order/', views.update_image_order, name='update_image_order'),
    path('admin/products/', views.ProductsExplorerAdminView.as_view(), name='admin_products_explorer'),
    path('product/<int:product_id>/detail/', views.product_detail, name='product_detail'),
    path('get-tags-for-category/', views.get_tags_for_category, name='get_tags_for_category'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/products/advanced-search/', views.api_advanced_search, name='api_advanced_search'),
    path('api/products/search/', views.api_simple_search, name='api_simple_search'),
    path('admin/backup-logs/', views.backup_logs, name='backup_logs'),
    path('admin/backup-download/<str:filename>/', views.download_backup, name='download_backup'),
    path('admin/backup-delete/<str:filename>/', views.delete_backup, name='delete_backup'),
    path('admin/backup-trigger/', views.trigger_backup, name='trigger_backup'),
    path('admin/backup-status/', views.get_backup_status, name='backup_status'),
    path('api/categories/simple/', views.api_categories, name='api_categories'),
    path('api/category/<int:category_id>/attributes/', views.api_category_attributes, name='api_category_attributes'),
    path('api/category/<int:category_id>/filter/', CategoryProductFilterView.as_view(), name='category-product-filter'),
    path('api/products/filter/', ProductsFilterView.as_view(), name='products-filter'),
    path('api/debug/category1-attributes/', debug_category1_attributes),
    path('api/debug/category/<int:category_id>/attributes-structure/', debug_category_attributes_structure),
    path('api/cleanup-product-attributes/<int:product_id>/', cleanup_product_attributes),
    path('api/assign-sample-attributes/', assign_sample_attributes, name='assign_sample_attributes'),
    path('search/', views.search_page, name='search'),
    
    # New Arrivals URLs
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
    path('api/new-arrivals/', views.api_new_arrivals, name='api_new_arrivals'),
    path('admin/new-arrivals/', views.admin_new_arrivals, name='admin_new_arrivals'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('api/wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('api/wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('api/wishlist/status/', views.get_wishlist_status, name='get_wishlist_status'),
    path('products-with-wishlist/', views.product_list_with_wishlist, name='product_list_with_wishlist'),
    
    # REST API Wishlist endpoints
    path('api/v1/wishlist/', WishlistListCreateAPIView.as_view(), name='api_wishlist_list_create'),
    path('api/v1/wishlist/<int:pk>/', WishlistDestroyAPIView.as_view(), name='api_wishlist_destroy'),
    path('api/v1/wishlist/toggle/', toggle_wishlist, name='api_wishlist_toggle'),
    path('api/v1/wishlist/status/', wishlist_status, name='api_wishlist_status'),
    
    # Gender-based category and product API endpoints
    path('api/categories/', api_categories_with_gender, name='api_categories_gender'),
    path('api/categories/direct/', api_direct_categories, name='api_direct_categories'),
    path('api/products/', api_products_by_gender_category, name='api_products_gender'),
    path('api/products/by-gender-category/', api_products_by_gender_category, name='api_products_by_gender_category'), 
    path('api/products/unified/', api_unified_products, name='api_unified_products'),
    path('api/organized-categories/', api_organized_categories, name='api_organized_categories'),
]