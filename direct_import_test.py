import sys
import os

# Add the current directory (myshop2/myshop/) to sys.path
# This is where 'suppliers' directory is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Crucially, ensure BASE_DIR (project root) is in sys.path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print(f"Current sys.path[0]: {sys.path[0]}")
print(f"Project base directory: {BASE_DIR}")
print(f"Full path to suppliers directory: {os.path.join(BASE_DIR, 'suppliers')}")
print(f"Does suppliers directory exist? {os.path.isdir(os.path.join(BASE_DIR, 'suppliers'))}")
print(f"Does suppliers/__init__.py exist? {os.path.isfile(os.path.join(BASE_DIR, 'suppliers', '__init__.py'))}")
print(f"Does suppliers/models.py exist? {os.path.isfile(os.path.join(BASE_DIR, 'suppliers', 'models.py'))}")

print("\n--- Attempting import ---")
try:
    # Attempt to import the suppliers package first
    import suppliers
    print("Successfully imported 'suppliers' package.")
    print(f"suppliers.__path__: {getattr(suppliers, '__path__', 'N/A')}")
    print(f"suppliers.__file__: {getattr(suppliers, '__file__', 'N/A')}")

    # Now attempt to import models from suppliers
    from suppliers import models
    print("Successfully imported suppliers.models!")
    print(f"User model type: {type(models.User)}")

except ImportError as e:
    print(f"ImportError: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc() 