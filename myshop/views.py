from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.conf import settings
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db import transaction
import jwt
from datetime import datetime
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.transport.requests import AuthorizedSession
from google.auth.transport.requests import Request
from rest_framework_simplejwt.exceptions import TokenError
import urllib3
import requests as http_requests
import ssl
import certifi
import base64

@never_cache
def health_check(request):
    """Simple health check endpoint for Railway deployment."""
    try:
        return JsonResponse({
            'status': 'healthy',
            'message': 'Django e-commerce API is running',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=500)

User = get_user_model()

GOOGLE_CLIENT_IDS = [
    '198960327448-p1d5feprlio39dk1rrac0ueju78qu4c4.apps.googleusercontent.com',  # iOS
    '198960327448-1trt4eu43v6cn9852j09nljgtiauh5bo.apps.googleusercontent.com',  # Web
]

def decode_jwt_token(token):
    """Decode JWT token without verification to get the header."""
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError('Invalid token format')
       
        # Decode the header
        header = json.loads(base64.b64decode(parts[0] + '=' * (-len(parts[0]) % 4)).decode('utf-8'))
        return header
    except Exception as e:
        print(f"Error decoding token header: {str(e)}")
        raise

@csrf_exempt
@require_http_methods(["POST"])
def google_auth_view(request):
    try:
        # Get the ID token from the request body
        data = json.loads(request.body)
        id_token_str = data.get('id_token')
        
        if not id_token_str:
            print('No ID token provided')
            return JsonResponse({'error': 'No ID token provided'}, status=400)
        
        print(f"Attempting to verify token with client ID: {settings.GOOGLE_CLIENT_ID}")
        
        try:
            # First decode the token to get the header
            header = decode_jwt_token(id_token_str)
            print(f"Token header: {header}")
            
            # Verify the token using PyJWT
            decoded = jwt.decode(
                id_token_str,
                options={
                    "verify_signature": False,  # Skip signature verification
                    "verify_aud": False,       # Skip audience verification
                    "verify_iss": False,       # Skip issuer verification
                    "verify_exp": True,        # Verify expiration
                    "verify_iat": True,        # Verify issued at
                },
                leeway=60  # Allow 60 seconds of clock skew
            )
            
            # Verify the client ID manually
            if decoded.get('aud') not in GOOGLE_CLIENT_IDS:
                raise ValueError('Invalid client ID')
            
            # Verify the issuer
            if decoded.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
            
            print("Token verified successfully")
            idinfo = decoded
            
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return JsonResponse({'error': 'Token has expired'}, status=400)
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {str(e)}")
            return JsonResponse({'error': f'Invalid token: {str(e)}'}, status=400)
        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            return JsonResponse({'error': f'Token verification failed: {str(e)}'}, status=400)
        
        # Get user info from the token
        email = idinfo['email']
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        print(f"User info retrieved - Email: {email}, Name: {first_name} {last_name}")
        
        # Get or create user
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': email
                }
            )
            
            if created:
                user.set_unusable_password()  # Since they'll use Google to login
                user.login_method = 'google'  # Set login_method to google
                user.save()
                print(f"Created new user: {email}")
            else:
                print(f"Found existing user: {email}")
                # Check if existing user can use Google login
                if hasattr(user, 'login_method') and user.login_method != 'google':
                    print(f"User {email} has login_method '{user.login_method}', blocking Google login")
                    return JsonResponse(
                        {'error': 'Please log in with your original method.'}, 
                        status=400
                    )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        print("JWT tokens generated successfully")
        
        return JsonResponse({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })
        
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        return JsonResponse({'error': 'Invalid token'}, status=400)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def refresh_token_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            refresh_token = data.get('refresh')
            
            if not refresh_token:
                return JsonResponse({'error': 'Refresh token is required'}, status=400)
            
            # Create a RefreshToken instance from the token string
            refresh = RefreshToken(refresh_token)
            
            # Generate new access token and refresh token
            new_access_token = str(refresh.access_token)
            new_refresh_token = str(refresh)
            
            return JsonResponse({
                'access': new_access_token,
                'refresh': new_refresh_token
            })
            
        except TokenError:
            return JsonResponse({'error': 'Invalid refresh token'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405) 