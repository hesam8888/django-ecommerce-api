from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from accounts.views import EmailTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # JWT endpoints
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Admin and other endpoints
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
    path('shop/', include('shop.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('image-editor/', include('image_editor.urls')),
    path('admin/shop/productimage/<int:image_id>/delete/', views.delete_product_image, name='delete_product_image'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 