#!/usr/bin/env python3
"""
Test script to verify deployment is working
"""

import requests
import json
import sys

def test_local_api():
    """Test the local API"""
    print("🔍 Testing Local API...")
    try:
        response = requests.get('http://127.0.0.1:8000/shop/api/categories/direct/')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local API Working!")
            print(f"   Categories found: {data.get('count', 0)}")
            return True
        else:
            print(f"❌ Local API Error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Local server not running. Start with: python manage.py runserver 8000")
        return False

def test_production_api(production_url):
    """Test the production API"""
    print(f"\n🌐 Testing Production API: {production_url}")
    try:
        response = requests.get(production_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Production API Working!")
            print(f"   Categories found: {data.get('count', 0)}")
            print(f"   Success: {data.get('success', False)}")
            return True
        else:
            print(f"❌ Production API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to production server")
        return False
    except requests.exceptions.Timeout:
        print("❌ Production server timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 Deployment Test Script")
    print("=" * 50)
    
    # Test local API
    local_ok = test_local_api()
    
    # Test production API if URL provided
    if len(sys.argv) > 1:
        production_url = sys.argv[1]
        production_ok = test_production_api(production_url)
    else:
        print("\n💡 To test production, run:")
        print("   python test_deployment.py https://your-app-name.onrender.com/shop/api/categories/direct/")
        production_ok = None
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   Local API: {'✅ Working' if local_ok else '❌ Failed'}")
    if production_ok is not None:
        print(f"   Production API: {'✅ Working' if production_ok else '❌ Failed'}")
    
    if local_ok and (production_ok is None or production_ok):
        print("\n🎉 All tests passed! Your API is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main() 