# Render Deployment Guide

## Deploying Patient Deterioration System to Render

This guide will help you deploy the complete Patient Deterioration Early Warning System to Render.

### 🚀 Quick Deployment Steps

#### 1. Push to GitHub
```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

#### 2. Create Render Services

**A. Create PostgreSQL Database**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "PostgreSQL"
3. Configure:
   - Name: `patient-deterioration-db`
   - Database Name: `patient_deterioration_db`
   - User: `admin`
   - Plan: Free
4. Click "Create Database"
5. **Save the database connection string** (you'll need it)

**B. Deploy Backend API**
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - Name: `patient-deterioration-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `python backend_render.py`
   - Plan: Free
4. Add Environment Variables:
   - `PORT`: `10000`
   - `DATABASE_URL`: [Your PostgreSQL connection string from step A]
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: `https://patient-deterioration-frontend.onrender.com`
   - `DEBUG`: `false`
5. Click "Create Web Service"

**C. Deploy Frontend**
1. Click "New +" → "Static Site"
2. Connect your GitHub repository
3. Configure:
   - Name: `patient-deterioration-frontend`
   - Build Command: `cd frontend && npm install && npm run build`
   - Publish Directory: `frontend/build`
4. Add Environment Variables:
   - `REACT_APP_API_URL`: `https://patient-deterioration-api.onrender.com`
   - `REACT_APP_API_KEY`: `render-production-key-2024`
   - `NODE_ENV`: `production`
5. Click "Create Static Site"

### 🔧 Configuration Files Created

- **`render.yaml`**: Complete infrastructure as code
- **`backend_render.py`**: Production-optimized backend server
- **`requirements-render.txt`**: Minimal dependencies for Render
- **`Procfile`**: Process file for backend service
- **`runtime.txt`**: Python version specification
- **`frontend/.env.production`**: Frontend production environment

### 🌐 Service URLs

After deployment, your services will be available at:

- **Frontend**: `https://patient-deterioration-frontend.onrender.com`
- **Backend API**: `https://patient-deterioration-api.onrender.com`
- **Database**: Internal connection only

### 📊 Initial Data Setup

After deployment, populate your database:

1. **Create Initial Patients**: Use the frontend "Add Patient" feature
2. **Generate Test Data**: Run the included data generation scripts
3. **Test Alerts**: Add critical vitals to trigger alerts

### 🔒 Security Features

- ✅ CORS protection
- ✅ Environment-based configuration
- ✅ PostgreSQL encryption at rest
- ✅ Secure API keys
- ✅ HTTPS enforcement

### 📈 Monitoring

Monitor your deployment:

- **Render Dashboard**: View logs, metrics, and health
- **API Health**: `https://patient-deterioration-api.onrender.com/health`
- **Database Status**: Check Render PostgreSQL dashboard

### 🚨 Troubleshooting

**Common Issues:**

1. **Build Failures**
   - Check build logs in Render dashboard
   - Verify `requirements-render.txt` has all dependencies
   - Ensure Python version matches `runtime.txt`

2. **Database Connection**
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL service is running
   - Review connection string format

3. **CORS Errors**
   - Verify `CORS_ORIGINS` includes frontend URL
   - Check `REACT_APP_API_URL` points to backend

4. **Frontend Build**
   - Ensure `npm install` completes successfully
   - Check `frontend/build` directory is created
   - Verify environment variables are set

### 💰 Cost Optimization

**Free Tier Limits:**
- PostgreSQL: 1GB storage, 1GB RAM
- Web Service: 512MB RAM, shared CPU
- Static Site: 100GB bandwidth

**Scaling Options:**
- Upgrade to Starter plans for better performance
- Add auto-scaling for high traffic
- Consider paid database for production

### 🔄 Automatic Deployments

Render automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update application"
git push origin main
```

Both services will redeploy automatically!

### 📋 Environment Variables Reference

**Backend (`patient-deterioration-api`)**
```
PORT=10000
DATABASE_URL=postgresql://admin:password@host:port/patient_deterioration_db
ENVIRONMENT=production
CORS_ORIGINS=https://patient-deterioration-frontend.onrender.com
DEBUG=false
```

**Frontend (`patient-deterioration-frontend`)**
```
REACT_APP_API_URL=https://patient-deterioration-api.onrender.com
REACT_APP_API_KEY=render-production-key-2024
NODE_ENV=production
```

### 🎯 Next Steps

1. **Test the Deployment**: Visit your frontend URL
2. **Create Test Data**: Add patients and vital signs
3. **Verify Alerts**: Ensure critical alerts appear
4. **Set Up Monitoring**: Configure alerts for downtime
5. **Custom Domain** (Optional): Add your own domain name

Your Patient Deterioration System is now live on Render! 🎉