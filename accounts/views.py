from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta
import uuid
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from .serializers import EmailTokenObtainPairSerializer, CustomTokenRefreshSerializer, UserSerializer, CustomerInfoSerializer
from .forms import (
    CustomerRegistrationForm,
    CustomerLoginForm,
    CustomerPasswordResetForm,
    CustomerSetPasswordForm
)
from .models import Customer, Address
from shop.models import Product
from .utils import is_rate_limited, get_client_ip
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import requests
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that checks if the user still exists and is active
    before refreshing the token.
    """
    serializer_class = CustomTokenRefreshSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            
            # Get the user ID from the refresh token
            user_id = serializer.validated_data.get('user_id')
            
            if not user_id:
                return Response(
                    {"detail": "Invalid refresh token."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if user exists and is active
            try:
                user = User.objects.get(id=user_id)
                if not user.is_active:
                    return Response(
                        {"detail": "User account is disabled."},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            except User.DoesNotExist:
                return Response(
                    {"detail": "User no longer exists."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # If we get here, the user exists and is active
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

class CustomerUserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        from .models import Customer
        # Try to get the customer by email from the request user
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        serializer = CustomerInfoSerializer(customer)
        return Response(serializer.data)

class CustomerAddressView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        """Get the current user's address information"""
        from .models import Customer
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        # Get the latest address object
        address = customer.addresses.order_by('-created_at').first()
        if address:
            address_data = {
                'street_address': address.street_address,
                'city': address.city,
                'state': address.province,
                'country': address.country,
                'postal_code': address.postal_code,
                'full_address': f"{address.street_address}, {address.city}, {address.province}, {address.country}, {address.postal_code}",
                'label': address.label,
            }
        else:
            address_data = {
                'street_address': customer.street_address,
                'city': customer.city,
                'state': customer.state,
                'country': customer.country,
                'postal_code': customer.postal_code,
                'full_address': customer.get_full_address(),
                'legacy_address': customer.address  # Keep the old text field for backward compatibility
            }
        return Response(address_data)

    def put(self, request):
        """Update the current user's address information"""
        from .models import Customer
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        
        # Update address fields
        address_fields = ['street_address', 'city', 'state', 'country', 'postal_code']
        for field in address_fields:
            if field in request.data:
                setattr(customer, field, request.data[field])
        
        customer.save()
        
        # Return updated address
        address_data = {
            'street_address': customer.street_address,
            'city': customer.city,
            'state': customer.state,
            'country': customer.country,
            'postal_code': customer.postal_code,
            'full_address': customer.get_full_address(),
            'legacy_address': customer.address
        }
        return Response(address_data)

class CustomerAddressesListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        from .models import Customer
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        addresses = customer.addresses.order_by('-created_at')[:4]
        data = [
            {
                'id': addr.id,
                'label': addr.label,
                'receiver_name': addr.receiver_name,
                'street_address': addr.street_address,
                'city': addr.city,
                'state': addr.province,
                'country': addr.country,
                'postal_code': addr.postal_code,
                'unit': addr.vahed,  # <-- always use 'unit' in API
                'phone': addr.phone,
                'full_address': addr.full_address,
                'created_at': addr.created_at,
                'updated_at': addr.updated_at,
            }
            for addr in addresses
        ]
        return Response({'addresses': data})

    def post(self, request):
        from .models import Customer, Address
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        if customer.addresses.count() >= 2:
            return Response({'detail': 'You can only have up to 2 addresses.'}, status=400)
        required_fields = ['street_address', 'city', 'unit', 'phone', 'receiver_name']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'detail': f'{field} is required.'}, status=400)
        
        try:
            address = Address.objects.create(
                customer=customer,
                label=request.data.get('label', ''),
                receiver_name=request.data['receiver_name'],
                street_address=request.data['street_address'],
                city=request.data['city'],
                province=request.data.get('state', ''),
                vahed=request.data['unit'],  # <-- map 'unit' from request to vahed in model
                phone=request.data['phone'],
                country=request.data.get('country', 'ایران'),
                postal_code=request.data.get('postal_code', ''),
            )
            return Response({'detail': 'Address created successfully.', 'address_id': address.id}, status=201)
        except Exception as e:
            return Response({'detail': str(e)}, status=400)

class CustomerAddressUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def put(self, request, address_id):
        """Update a specific address by ID"""
        from .models import Customer, Address
        
        # Get the customer
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        
        # Get the specific address
        try:
            address = Address.objects.get(id=address_id, customer=customer)
        except Address.DoesNotExist:
            return Response({'detail': 'Address not found', 'code': 'address_not_found'}, status=404)
        
        # Validate required fields
        required_fields = ['street_address', 'city', 'unit', 'phone', 'receiver_name']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'detail': f'{field} is required.'}, status=400)
        
        try:
            # Update the address
            address.label = request.data.get('label', address.label)
            address.receiver_name = request.data.get('receiver_name', address.receiver_name)
            address.street_address = request.data['street_address']
            address.city = request.data['city']
            address.province = request.data.get('state', address.province)
            address.vahed = request.data['unit']  # Map 'unit' from request to vahed in model
            address.phone = request.data['phone']
            address.country = request.data.get('country', address.country)
            address.postal_code = request.data.get('postal_code', address.postal_code)
            
            address.save()
            
            # Return updated address
            address_data = {
                'id': address.id,
                'label': address.label,
                'receiver_name': address.receiver_name,
                'street_address': address.street_address,
                'city': address.city,
                'state': address.province,
                'country': address.country,
                'postal_code': address.postal_code,
                'unit': address.vahed,  # Use 'unit' in API response
                'phone': address.phone,
                'full_address': address.full_address,
                'created_at': address.created_at,
                'updated_at': address.updated_at,
            }
            return Response(address_data)
        except Exception as e:
            return Response({'detail': str(e)}, status=400)

    def delete(self, request, address_id):
        """Delete a specific address by ID"""
        from .models import Customer, Address
        
        # Get the customer
        customer = Customer.objects.filter(email=request.user.email).first()
        if not customer:
            return Response({'detail': 'Customer not found', 'code': 'customer_not_found'}, status=404)
        
        # Get the specific address
        try:
            address = Address.objects.get(id=address_id, customer=customer)
        except Address.DoesNotExist:
            return Response({'detail': 'Address not found', 'code': 'address_not_found'}, status=404)
        
        # Delete the address
        address.delete()
        return Response({'detail': 'Address deleted successfully.'}, status=200)

@csrf_exempt
def register(request):
    if request.method == 'POST':
        # Check if it's an API request
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                form = CustomerRegistrationForm(data)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        else:
            form = CustomerRegistrationForm(request.POST)

        if form.is_valid():
            print(f"DEBUG: Registration form is valid")
            user = form.save()  # This will handle password setting and other attributes
            print(f"DEBUG: Created user with email: {user.email}")
            print(f"DEBUG: User is_active: {user.is_active}")
            
            # Generate verification token and send email
            token = user.generate_email_verification_token()
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', args=[token])
            )
            print(f"DEBUG: Generated verification URL: {verification_url}")
            
            # Prepare email content
            context = {
                'user': user,
                'verification_url': verification_url
            }
            html_message = render_to_string('accounts/email/verification_email.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                # Send verification email
                send_mail(
                    'Verify your email address',
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                print(f"DEBUG: Verification email sent to {user.email}")
                
                # Return appropriate response based on request type
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'message': 'Registration successful! Please check your email to verify your account.'
                    })
                else:
                    messages.success(request, 'Registration successful! Please check your email to verify your account.')
                    return redirect('accounts:login')
                    
            except Exception as e:
                print(f"DEBUG: Error sending verification email: {str(e)}")
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': 'Registration successful, but there was an error sending the verification email. Please contact support.'
                    }, status=500)
                else:
                    messages.error(request, 'Registration successful, but there was an error sending the verification email. Please contact support.')
                    return redirect('accounts:login')
        else:
            print(f"DEBUG: Form errors: {form.errors}")
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'error': form.errors}, status=400)
    else:
        form = CustomerRegistrationForm()
    
    # If it's not a POST request or form is invalid, render the template
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Check rate limiting
        is_limited, remaining_attempts, cooldown_remaining = is_rate_limited(
            request,
            'login_attempts',
            max_attempts=5,  # Maximum 5 attempts
            cooldown_minutes=15  # 15 minutes cooldown
        )
        
        if is_limited:
            messages.error(
                request,
                f'Too many login attempts. Please try again in {cooldown_remaining} minutes.'
            )
            return render(request, 'accounts/login.html', {'form': CustomerLoginForm()})
        
        form = CustomerLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            user.backend = 'accounts.backends.CustomerBackend'  # Specify the backend
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('accounts:home')
        else:
            messages.error(
                request,
                f'Invalid login attempt. {remaining_attempts} attempts remaining.'
            )
    else:
        form = CustomerLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def verify_email(request, token):
    print(f"DEBUG: Attempting to verify email with token: {token}")
    try:
        user = Customer.objects.get(email_verification_token=token)
        print(f"DEBUG: Found user with token: {user.email}")
        print(f"DEBUG: Current verification status: {user.is_email_verified}")
        
        if user.is_email_verified:
            print(f"DEBUG: Email already verified")
            messages.info(request, 'Your email is already verified.')
        else:
            user.is_email_verified = True
            user.is_active = True  # Make sure user is active after verification
            user.save()
            print(f"DEBUG: Email verified successfully")
            print(f"DEBUG: New verification status: {user.is_email_verified}")
            print(f"DEBUG: New active status: {user.is_active}")
            messages.success(request, 'Your email has been verified successfully!')
        return redirect('login')
    except Customer.DoesNotExist:
        print(f"DEBUG: No user found with token: {token}")
        messages.error(request, 'Invalid verification link.')
        return redirect('login')

def password_reset_request(request):
    if request.method == 'POST':
        form = CustomerPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            print(f"DEBUG: Attempting password reset for email: {email}")  # Debug log
            try:
                user = User.objects.get(email=email)
                print(f"DEBUG: Found user: {user.email}")  # Debug log
                
                # Generate a UUID token
                token = str(uuid.uuid4())
                user.password_reset_token = token
                user.password_reset_sent_at = timezone.now()
                user.save()
                
                # Send password reset email
                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', args=[token])
                )
                context = {
                    'user': user,
                    'reset_url': reset_url
                }
                html_message = render_to_string('accounts/email/password_reset_email.html', context)
                plain_message = strip_tags(html_message)
                
                send_mail(
                    'Password Reset Request',
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                messages.success(request, 'Password reset instructions have been sent to your email.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                print(f"DEBUG: No user found with email: {email}")  # Debug log
                # Let's check if there are any users in the database
                all_users = User.objects.all()
                print(f"DEBUG: Total users in database: {all_users.count()}")  # Debug log
                for user in all_users:
                    print(f"DEBUG: User in database: {user.email}")  # Debug log
                messages.error(request, 'No account found with that email address.')
    else:
        form = CustomerPasswordResetForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})

def password_reset_confirm(request, token):
    try:
        user = User.objects.get(password_reset_token=token)
        # Check if token is expired (24 hours)
        if user.password_reset_sent_at < timezone.now() - timedelta(hours=24):
            user.password_reset_token = None
            user.password_reset_sent_at = None
            user.save()
            messages.error(request, 'Password reset link has expired.')
            return redirect('accounts:password_reset_request')
        
        if request.method == 'POST':
            form = CustomerSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                # Clear the reset token
                user.password_reset_token = None
                user.password_reset_sent_at = None
                user.save()
                messages.success(request, 'Your password has been reset successfully!')
                return redirect('accounts:login')
        else:
            form = CustomerSetPasswordForm(user)
        
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    except User.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('accounts:password_reset_request')

@login_required
def profile(request):
    # Get the user's addresses (up to 3)
    addresses = request.user.addresses.all()[:3]
    
    if request.method == 'POST':
        # Handle address deletion
        delete_address_id = request.POST.get('delete_address_id')
        if delete_address_id:
            try:
                address = request.user.addresses.get(id=delete_address_id)
                address.delete()
                messages.success(request, 'Address deleted successfully.')
                return redirect('accounts:profile')
            except Address.DoesNotExist:
                messages.error(request, 'Address not found.')
                return redirect('accounts:profile')
        
        # Handle address editing
        edit_address_id = request.POST.get('edit_address_id')
        if edit_address_id:
            try:
                address = request.user.addresses.get(id=edit_address_id)
                
                # Get form data
                label = request.POST.get('label', '').strip()
                receiver_name = request.POST.get('receiver_name', '').strip()
                street_address = request.POST.get('street_address', '').strip()
                city = request.POST.get('city', '').strip()
                province = request.POST.get('province', '').strip()
                vahed = request.POST.get('vahed', '').strip()
                country = request.POST.get('country', '').strip() or 'ایران'
                postal_code = request.POST.get('postal_code', '').strip()
                phone = request.POST.get('phone', '').strip()
                
                # Validate required fields
                if not all([label, receiver_name, street_address, city, country, phone]):
                    messages.error(request, 'Please fill in all required fields.')
                    return redirect('accounts:profile')
                
                # Update address
                address.label = label
                address.receiver_name = receiver_name
                address.street_address = street_address
                address.city = city
                address.province = province
                address.vahed = vahed
                address.country = country
                address.postal_code = postal_code
                address.phone = phone
                address.save()
                
                messages.success(request, 'Address updated successfully.')
                return redirect('accounts:profile')
                
            except Address.DoesNotExist:
                messages.error(request, 'Address not found.')
                return redirect('accounts:profile')
            except Exception as e:
                messages.error(request, f'Error updating address: {str(e)}')
                return redirect('accounts:profile')
        
        # Handle address creation
        if addresses.count() < 3:
            label = request.POST.get('label', '').strip()
            receiver_name = request.POST.get('receiver_name', '').strip()
            street_address = request.POST.get('street_address', '').strip()
            city = request.POST.get('city', '').strip()
            province = request.POST.get('province', '').strip()
            vahed = request.POST.get('vahed', '').strip()
            country = request.POST.get('country', '').strip() or 'ایران'
            postal_code = request.POST.get('postal_code', '').strip()
            phone = request.POST.get('phone', '').strip()
            
                        # Debug logging
            print(f"DEBUG - Creating address with label: '{label}'")
            print(f"DEBUG - Form data: label='{label}', receiver_name='{receiver_name}', street_address='{street_address}'")
            
            # Validate required fields
            if not all([label, receiver_name, street_address, city, country, phone]):
                missing_fields = []
                if not label: missing_fields.append('label')
                if not receiver_name: missing_fields.append('receiver_name')
                if not street_address: missing_fields.append('street_address')
                if not city: missing_fields.append('city')
                if not country: missing_fields.append('country')
                if not phone: missing_fields.append('phone')
                messages.error(request, f'Please fill in all required fields: {", ".join(missing_fields)}')
                return redirect('accounts:profile')

            try:
                new_address = request.user.addresses.create(
                    label=label,
                    receiver_name=receiver_name,
                    street_address=street_address,
                    city=city,
                    province=province,
                    vahed=vahed,
                    country=country,
                    postal_code=postal_code,
                    phone=phone
                )
                print(f"DEBUG - Address created with ID: {new_address.id}, Label: '{new_address.label}'")
                messages.success(request, f'Address "{label}" added successfully.')
                return redirect('accounts:profile')
            except Exception as e:
                print(f"DEBUG - Error creating address: {str(e)}")
                messages.error(request, f'Error creating address: {str(e)}')
                return redirect('accounts:profile')
    
    addresses = request.user.addresses.all()[:3]
    return render(request, 'accounts/profile.html', {'addresses': addresses})

@login_required
def home(request):
    from shop.models import Wishlist
    from django.db.models import Exists, OuterRef
    
    # Get user's wishlist items with product details
    wishlist_items = Wishlist.objects.filter(
        customer=request.user
    ).select_related('product', 'product__category').prefetch_related('product__images').order_by('-created_at')[:6]  # Show latest 6 items
    
    # Get all active products with wishlist status for the current user
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images').annotate(
        is_in_wishlist=Exists(
            Wishlist.objects.filter(
                customer=request.user,
                product=OuterRef('pk')
            )
        )
    )[:12]  # Limit to 12 products for performance
    
    # Group products by category
    categories = {}
    for product in products:
        if product.category not in categories:
            categories[product.category] = []
        categories[product.category].append(product)
    
    # Get wishlist count
    wishlist_count = Wishlist.objects.filter(customer=request.user).count()
    
    context = {
        'categories': categories,
        'products': products,
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_count,
    }
    return render(request, 'accounts/home.html', context)

@login_required
def admin_address_view(request):
    """Admin web page to view all user addresses"""
    from .models import Customer
    
    # Check if user is staff/admin
    if not request.user.is_staff:
        return redirect('accounts:login')
    
    # Handle POST request for updating addresses
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        try:
            customer = Customer.objects.get(id=customer_id)
            
            # Update address fields
            customer.street_address = request.POST.get('street_address', '')
            customer.city = request.POST.get('city', '')
            customer.state = request.POST.get('state', '')
            customer.country = request.POST.get('country', '')
            customer.postal_code = request.POST.get('postal_code', '')
            
            customer.save()
            
            # Redirect back to the same page with success message
            messages.success(request, f'Address updated successfully for {customer.email}')
            return redirect('accounts:admin_addresses')
            
        except Customer.DoesNotExist:
            messages.error(request, 'Customer not found')
            return redirect('accounts:admin_addresses')
    
    # Get search parameters
    search_email = request.GET.get('email', '')
    search_country = request.GET.get('country', '')
    search_city = request.GET.get('city', '')
    
    # Filter customers
    customers = Customer.objects.all()
    
    if search_email:
        customers = customers.filter(email__icontains=search_email)
    if search_country:
        customers = customers.filter(country__icontains=search_country)
    if search_city:
        customers = customers.filter(city__icontains=search_city)
    
    # Order by email
    customers = customers.order_by('email')
    
    context = {
        'customers': customers,
        'search_email': search_email,
        'search_country': search_country,
        'search_city': search_city,
        'total_count': customers.count(),
    }
    
    return render(request, 'accounts/admin_addresses.html', context)

@require_POST
@login_required
def admin_update_address_field(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    from .models import Customer
    customer_id = request.POST.get('customer_id')
    field = request.POST.get('field')
    value = request.POST.get('value', '')
    allowed_fields = ['street_address', 'city', 'state', 'country', 'postal_code']
    if field not in allowed_fields:
        return JsonResponse({'success': False, 'error': 'Invalid field'}, status=400)
    try:
        customer = Customer.objects.get(id=customer_id)
        setattr(customer, field, value)
        customer.save()
        return JsonResponse({'success': True, 'value': value})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)

class GoogleAuthView(APIView):
    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response({'error': 'Missing id_token'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the Google ID token
        google_response = requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
        )
        if google_response.status_code != 200:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)
        user_info = google_response.json()
        email = user_info.get('email')
        if not email:
            return Response({'error': 'No email in Google token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            print(f"DEBUG: Found user {user.email} with login_method {getattr(user, 'login_method', None)}")
            # Only allow Google login if login_method is 'google'
            if hasattr(user, 'login_method') and user.login_method != 'google':
                return Response(
                    {'error': 'Please log in with your original method.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # login_method is google, proceed
        except User.DoesNotExist:
            # New user: create with Google method
            user = User.objects.create_user(
                username=email,
                email=email,
                login_method='google',
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
            )
            user.set_unusable_password()
            user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })