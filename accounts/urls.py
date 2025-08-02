from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import CustomerAddressesListView, CustomerAddressUpdateView, GoogleAuthView, CustomTokenRefreshView

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<uuid:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('profile/', views.profile, name='profile'),
    path('admin/addresses/', views.admin_address_view, name='admin_addresses'),
    path('admin/addresses/update/', views.admin_update_address_field, name='admin_address_update'),
    
    # JWT Token endpoints
    path('token/', views.EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('user/', views.UserDetailView.as_view(), name='user_detail'),
    path('customer/', views.CustomerUserDetailView.as_view(), name='customer_detail'),
    path('customer/address/', views.CustomerAddressView.as_view(), name='customer_address'),
    path('customer/addresses/', CustomerAddressesListView.as_view(), name='customer_addresses'),
    path('customer/addresses/<int:address_id>/', CustomerAddressUpdateView.as_view(), name='customer_address_update'),
    path('auth/google', GoogleAuthView.as_view(), name='google-auth'),
]
