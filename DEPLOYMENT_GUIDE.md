# 🚀 Deployment Guide

## Quick Deploy to Render.com (Recommended)

### 1. Prepare Your Code
```bash
# Make sure all files are committed to Git
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Deploy to Render
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Create Web Service"

### 3. Environment Variables (Optional)
Render will automatically set these, but you can customize:
- `SECRET_KEY`: Auto-generated
- `DATABASE_URL`: Auto-generated from PostgreSQL service
- `DEBUG`: Set to `False` for production

### 4. Your API Will Be Available At:
```
https://your-app-name.onrender.com/shop/api/categories/direct/
```

## Alternative: Railway.app

### 1. Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add PostgreSQL service
4. Deploy

### 2. Set Environment Variables
- `SECRET_KEY`: Generate a secure key
- `DATABASE_URL`: Railway will provide this
- `DEBUG`: `False`

## Testing Your Deployed API

Once deployed, test your API:

```bash
# Test the direct categories API
curl https://your-app-name.onrender.com/shop/api/categories/direct/

# Or visit in browser
https://your-app-name.onrender.com/shop/api/categories/direct/
```

## Local Development vs Production

### Local Development
```bash
python manage.py runserver 8000
# API: http://127.0.0.1:8000/shop/api/categories/direct/
```

### Production
```bash
# Deployed automatically
# API: https://your-app-name.onrender.com/shop/api/categories/direct/
```

## Troubleshooting

### Common Issues:
1. **Database migrations**: Run `python manage.py migrate` in production
2. **Static files**: Ensure `python manage.py collectstatic` runs
3. **Environment variables**: Check all required vars are set

### Check Logs:
- Render: Dashboard → Your Service → Logs
- Railway: Dashboard → Your Service → Logs

## Security Notes

✅ Production settings include:
- `DEBUG = False`
- Secure cookies
- HTTPS redirect
- XSS protection
- CSRF protection

🔒 Remember to:
- Use strong SECRET_KEY
- Keep database credentials secure
- Monitor logs for issues 