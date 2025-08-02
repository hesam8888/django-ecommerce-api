#!/usr/bin/env python3
"""
Test script to verify token refresh functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_token_refresh():
    """Test the token refresh endpoint"""
    
    # First, let's try to get a token (you'll need to provide valid credentials)
    print("Testing token refresh endpoint...")
    
    # Test the refresh endpoint directly
    refresh_url = f"{BASE_URL}/token/refresh/"
    
    # This is a sample refresh token - you'll need to replace with a real one
    test_data = {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1MTg0Mjc5MCwiaWF0IjoxNzUxNzU2MzkwLCJqdGkiOiI5ZWJhNWM2NmVkMjE0MTQ3YTFkODYxN2Q3YzM3OTMxOCIsInVzZXJfaWQiOjM0fQ.EwbJmdng_yJY36Gj7o0nEHniorgiUo16l56bwB-_fIc"
    }
    
    try:
        response = requests.post(
            refresh_url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Token refresh endpoint is working!")
            tokens = response.json()
            print(f"New access token: {tokens.get('access', 'N/A')[:50]}...")
            print(f"New refresh token: {tokens.get('refresh', 'N/A')[:50]}...")
        else:
            print("❌ Token refresh failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_token_refresh() 