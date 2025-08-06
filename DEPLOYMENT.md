# Deployment Guide

This guide will help you deploy your Company Cohort Web application.

## Architecture Overview

- **Frontend**: React + Vite application
- **Backend**: FastAPI Python application
- **Recommended**: Deploy frontend and backend separately

## Option 1: Vercel (Frontend) + Railway (Backend) - Recommended

### Frontend Deployment (Vercel)

1. **Install Vercel CLI** (optional):
   ```bash
   npm install -g vercel
   ```

2. **Deploy to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Sign up/Login with your GitHub account
   - Click "New Project"
   - Import your repository
   - Vercel will automatically detect it's a Vite project
   - Add environment variable: `VITE_BACKEND_URL=https://your-backend-url.railway.app`

3. **Or deploy via CLI**:
   ```bash
   vercel
   ```

### Backend Deployment (Railway)

1. **Deploy to Railway**:
   - Go to [railway.app](https://railway.app)
   - Sign up/Login with your GitHub account
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Set the root directory to `backend/`
   - Railway will automatically detect the Python app

2. **Configure Environment Variables**:
   - In Railway dashboard, go to your project
   - Add environment variables if needed

3. **Get your backend URL**:
   - Railway will provide a URL like `https://your-app-name.railway.app`
   - Copy this URL

4. **Update Frontend Environment**:
   - In Vercel dashboard, add environment variable:
     - Name: `VITE_BACKEND_URL`
     - Value: `https://your-app-name.railway.app`

## Option 2: Netlify (Frontend) + Render (Backend)

### Frontend Deployment (Netlify)

1. **Deploy to Netlify**:
   - Go to [netlify.com](https://netlify.com)
   - Sign up/Login with your GitHub account
   - Click "New site from Git"
   - Select your repository
   - Build command: `npm run build`
   - Publish directory: `dist`

2. **Add Environment Variable**:
   - In Netlify dashboard, go to Site settings → Environment variables
   - Add: `VITE_BACKEND_URL=https://your-backend-url.onrender.com`

### Backend Deployment (Render)

1. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - Sign up/Login with your GitHub account
   - Click "New Web Service"
   - Connect your repository
   - Set root directory to `backend/`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Option 3: Heroku (Full Stack)

1. **Install Heroku CLI**:
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   ```

2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Deploy backend**:
   ```bash
   cd backend
   git add .
   git commit -m "Deploy backend"
   git push heroku main
   ```

4. **Deploy frontend**:
   ```bash
   cd ..
   npm run build
   # Copy dist folder to a separate repository or use Heroku buildpacks
   ```

## Environment Variables

### Frontend (.env.local for development)
```
VITE_BACKEND_URL=http://localhost:8000
```

### Production
Set `VITE_BACKEND_URL` to your deployed backend URL.

## CORS Configuration

Update the backend CORS origins in `backend/main.py` with your actual frontend domain:

```python
allow_origins=[
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "https://your-frontend-domain.vercel.app",  # Replace with actual domain
    "https://your-frontend-domain.netlify.app", # Replace with actual domain
],
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure your backend CORS configuration includes your frontend domain
2. **Environment Variables**: Ensure `VITE_BACKEND_URL` is set correctly in your deployment platform
3. **Build Errors**: Check that all dependencies are in `package.json` and `requirements.txt`

### Testing Deployment

1. **Test Backend**: Visit `https://your-backend-url.com/health`
2. **Test Frontend**: Visit your frontend URL and check browser console for errors
3. **Test Integration**: Try uploading data and running calculations

## Cost Considerations

- **Vercel**: Free tier includes 100GB bandwidth/month
- **Railway**: Free tier includes $5 credit/month
- **Netlify**: Free tier includes 100GB bandwidth/month
- **Render**: Free tier available with limitations
- **Heroku**: No free tier (paid plans start at $7/month)

## Recommended Setup

For a production application, we recommend:
- **Frontend**: Vercel (excellent React/Vite support)
- **Backend**: Railway (good Python/FastAPI support)
- **Database**: Add PostgreSQL if needed (Railway provides this)
- **Monitoring**: Add logging and monitoring services 