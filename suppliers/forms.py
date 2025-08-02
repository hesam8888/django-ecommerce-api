from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Supplier, Store, SupplierAdmin, SupplierInvitation
from suppliers.models import User  # Import the User model directly from suppliers app

class SupplierRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields readonly
        readonly_fields = ['username', 'email', 'first_name', 'last_name']
        for field in readonly_fields:
            if field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
                self.fields[field].widget.attrs['class'] = 'readonly-field'
                self.fields[field].help_text = "This field is pre-filled from your invitation."
        
        # Focus on password fields
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs['autofocus'] = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Note: is_supplier_admin is a property, not a field
        # The SupplierAdmin record will be created in the view
        if commit:
            user.save()
        return user

class SupplierLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username or email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Try to get user by username or email
            try:
                # First try to get by username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                try:
                    # If not found by username, try email
                    user = User.objects.get(email=username)
                except User.DoesNotExist:
                    raise forms.ValidationError("Invalid username or email")
                except User.MultipleObjectsReturned:
                    # If multiple users found with same email, get the one that is a supplier admin
                    users = User.objects.filter(email=username)
                    supplier_admins = [u for u in users if u.is_supplier_admin]
                    if not supplier_admins:
                        raise forms.ValidationError("No supplier account found with this email")
                    user = supplier_admins[0]  # Take the first supplier admin
            except User.MultipleObjectsReturned:
                # If multiple users found with same username, get the one that is a supplier admin
                users = User.objects.filter(username=username)
                supplier_admins = [u for u in users if u.is_supplier_admin]
                if not supplier_admins:
                    raise forms.ValidationError("No supplier account found with this username")
                user = supplier_admins[0]  # Take the first supplier admin

            if not user.check_password(password):
                raise forms.ValidationError("Invalid password")

            # Allow superusers even if they don't have is_supplier_admin
            if not user.is_superuser and not user.is_supplier_admin:
                raise forms.ValidationError("This account is not authorized as a supplier")

            self.user_cache = user

        return self.cleaned_data 