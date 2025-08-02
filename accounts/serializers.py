from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Customer, Address

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = get_user_model().EMAIL_FIELD
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user_id to both access and refresh tokens
        data['user_id'] = self.user.id
        return data

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user_id to the response
        refresh = self.token_class(attrs["refresh"])
        data['user_id'] = refresh.payload.get('user_id')
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name', 'is_active', 'is_email_verified', 'login_method')

class CustomerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'first_name', 'last_name', 'is_active', 'is_email_verified', 'login_method')

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'label', 'receiver_name', 'street_address', 'city', 'province', 'vahed', 'phone', 'country', 'postal_code', 'full_address', 'created_at', 'updated_at')
        read_only_fields = ('id', 'full_address', 'created_at', 'updated_at')
        extra_kwargs = {
            'receiver_name': {'required': True},
            'phone': {'required': True},
        } 