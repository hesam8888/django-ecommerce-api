# 🚫 NEVER SEE ALLAUTH ERROR AGAIN! 

## The Problem
The `allauth` error occurs when Django tries to import `django-allauth` but it's not installed in your current Python environment.

## ✅ The Permanent Solution

### 1. Always Use Virtual Environment
```bash
# Make sure you're in the project directory
cd /path/to/myshop2/myshop

# Activate virtual environment EVERY TIME
source venv/bin/activate
```

### 2. Use the New Runserver Script
Instead of running `python manage.py runserver` directly, use:
```bash
./runserver.sh
```

This script automatically:
- ✅ Checks if virtual environment exists
- ✅ Activates the virtual environment
- ✅ Verifies all dependencies are installed
- ✅ Runs migrations if needed
- ✅ Starts the server

### 3. Manual Dependency Check
If you want to check dependencies manually:
```bash
source venv/bin/activate
python check_dependencies.py
```

### 4. If You Still Get Allauth Error
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install missing packages
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Check everything is working
python manage.py check
```

## 🔧 What Was Fixed

1. **Updated allauth settings** - Removed deprecated settings that caused warnings
2. **Created dependency checker** - Automatically verifies all packages are installed
3. **Improved runserver script** - Prevents running Django with missing dependencies
4. **Virtual environment check** - Ensures you're always using the correct environment

## 🎯 Key Rules to Follow

1. **ALWAYS** activate virtual environment first: `source venv/bin/activate`
2. **ALWAYS** use `./runserver.sh` instead of `python manage.py runserver`
3. **NEVER** run Django commands without activating virtual environment
4. **CHECK** dependencies with `python check_dependencies.py` if unsure

## 🚨 Emergency Fix
If you see the allauth error again:
```bash
cd myshop2/myshop
source venv/bin/activate
pip install django-allauth==65.8.1
python manage.py migrate
```

---
**Remember**: The virtual environment is your friend! Always activate it first! 🐍 