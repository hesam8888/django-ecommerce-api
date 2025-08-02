from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop.views import delete_product_image, home
from .admin import admin_site
from accounts.views import EmailTokenObtainPairView, UserDetailView, CustomerUserDetailView, CustomTokenRefreshView
from . import views

urlpatterns = [
    # JWT endpoints
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Admin and other endpoints
    path('admin/', admin_site.urls),
    path('', home, name='home'),  # Root URL for home page
    path('accounts/', include('accounts.urls')),  # custom urls
    path('accounts/', include('django.contrib.auth.urls')),  # built-in views
    path('accounts/', include('allauth.urls')),
    path('shop/', include('shop.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('image-editor/', include('image_editor.urls')),
    path('admin/shop/productimage/<int:image_id>/delete/', delete_product_image, name='delete_product_image'),
    path('user/', UserDetailView.as_view(), name='user_detail'),
    path('customer/user/', CustomerUserDetailView.as_view(), name='customer_user_detail'),
    path('auth/google', views.google_auth_view, name='google_auth'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




