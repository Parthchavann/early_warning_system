# 🔧 Render Deployment Fix Guide

## The Problem
Your current service `patient-deterioration-frontend` is configured incorrectly:
- It's trying to build frontend with Python instead of Node.js
- You need TWO separate services, not one

## ✅ Solution: Delete and Recreate Services

### Step 1: Delete Current Service
1. Go to your Render dashboard
2. Click on `patient-deterioration-frontend` service
3. Go to **Settings** → Scroll down → **Delete Service**
4. Confirm deletion

### Step 2: Create Backend API Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub: `Parthchavann/early_warning_system`
3. Configure:
   ```
   Name: patient-deterioration-api
   Environment: Python 3
   Branch: main
   Build Command: pip install -r requirements-render.txt
   Start Command: python backend_simple.py
   ```
4. Add Environment Variables:
   ```
   PORT=10000
   ENVIRONMENT=production
   CORS_ORIGINS=https://patient-deterioration-frontend.onrender.com
   ```
5. Click **"Create Web Service"**

### Step 3: Create Frontend Static Site
1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub: `Parthchavann/early_warning_system`
3. Configure:
   ```
   Name: patient-deterioration-frontend
   Branch: main
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/build
   ```
4. Add Environment Variables:
   ```
   REACT_APP_API_URL=https://patient-deterioration-api.onrender.com
   REACT_APP_API_KEY=render-production-key-2024
   NODE_ENV=production
   ```
5. Click **"Create Static Site"**

## 🎯 Final URLs
- **Frontend**: https://patient-deterioration-frontend.onrender.com
- **Backend API**: https://patient-deterioration-api.onrender.com

## ⚠️ Important Notes
- The backend will deploy first (faster)
- Frontend takes 5-10 minutes to build
- Make sure environment variables match between services
- Test the backend health endpoint: `/health`

## 🔍 Troubleshooting
If builds still fail:
1. Check the build logs for specific errors
2. Verify GitHub repo is public and accessible
3. Ensure all files are committed and pushed
4. Try manual deploy if auto-deploy doesn't trigger