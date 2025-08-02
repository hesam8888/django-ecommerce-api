from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from .models import Customer
from django.contrib.auth import get_user_model
import re
from django.urls import reverse

User = get_user_model()

class CustomerRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    class Meta:
        model = Customer
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'date_of_birth']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False  # Set to False until email is verified
        user.login_method = 'email'  # Always set to email for this form
        if commit:
            user.save()
        return user
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Passwords do not match'))
        
        # Password validation
        if len(password1) < 8:
            raise forms.ValidationError(_('Password must be at least 8 characters long'))
        if not re.search(r'[A-Z]', password1):
            raise forms.ValidationError(_('Password must contain at least one uppercase letter'))
        if not re.search(r'[a-z]', password1):
            raise forms.ValidationError(_('Password must contain at least one lowercase letter'))
        if not re.search(r'\d', password1):
            raise forms.ValidationError(_('Password must contain at least one number'))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError(_('Password must contain at least one special character'))
        
        return password2
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove any non-digit characters
            phone = re.sub(r'\D', '', phone)
            if len(phone) < 10:
                raise forms.ValidationError(_('Please enter a valid phone number'))
        return phone

class CustomerLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            try:
                user = Customer.objects.get(email=email)
                print(f"DEBUG: Found user with email {email}")
                print(f"DEBUG: User details:")
                print(f"  - is_active: {user.is_active}")
                print(f"  - is_email_verified: {user.is_email_verified}")
                
                if not user.is_active:
                    raise forms.ValidationError("This account is inactive. Please check your email for verification link.")
                
                if not user.is_email_verified:
                    # Generate a new verification token and send a new email
                    token = user.generate_email_verification_token()
                    verification_url = reverse('accounts:verify_email', args=[token])
                    print(f"DEBUG: Generated new verification token: {token}")
                    print(f"DEBUG: New verification URL: {verification_url}")
                    raise forms.ValidationError("Please verify your email address. Check your email for the verification link.")
                
                if not user.check_password(password):
                    raise forms.ValidationError("Invalid password. Please try again.")
                
                self.user_cache = user
                print(f"DEBUG: Login successful for user {email}")
            except Customer.DoesNotExist:
                print(f"DEBUG: No user found with email {email}")
                raise forms.ValidationError("No account found with this email address. Please check your email or register.")
        return self.cleaned_data

class CustomerPasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            Customer.objects.get(email=email)
            return email
        except Customer.DoesNotExist:
            raise forms.ValidationError(_('No account found with that email address.'))

class CustomerSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
