#!/usr/bin/env python3
"""
Test script to verify ICC profile handling
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from PIL import Image
import warnings
from io import BytesIO

# Suppress ICC profile warnings for testing
warnings.filterwarnings('ignore', category=UserWarning, module='PIL')

def test_icc_handling():
    """Test ICC profile handling with a sample image"""
    
    # Create a simple test image
    test_img = Image.new('RGB', (100, 100), color='red')
    
    # Save with ICC profile info (simulating problematic image)
    output = BytesIO()
    test_img.save(output, format='JPEG', icc_profile=b'fake_icc_profile')
    output.seek(0)
    
    print("Testing ICC profile handling...")
    
    try:
        # Try to open the image normally
        img = Image.open(output)
        print("✓ Image opened successfully")
        
        # Check if ICC profile exists
        if hasattr(img, 'info') and 'icc_profile' in img.info:
            print("✓ ICC profile detected")
            
            # Test the safe_open_image function
            from shop.utils import safe_open_image
            safe_img = safe_open_image(output)
            
            # Check if ICC profile was stripped
            if not (hasattr(safe_img, 'info') and 'icc_profile' in safe_img.info):
                print("✓ ICC profile successfully stripped")
            else:
                print("✗ ICC profile still present")
                
        else:
            print("✓ No ICC profile found (normal)")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("ICC profile handling test completed!")

if __name__ == "__main__":
    test_icc_handling() 