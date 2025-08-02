from django.contrib.auth.backends import ModelBackend
from .models import Customer

class CustomerBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Customer.objects.get(email=email)
            if user.check_password(password):
                return user
        except Customer.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return Customer.objects.get(pk=user_id)
        except Customer.DoesNotExist:
            return None 