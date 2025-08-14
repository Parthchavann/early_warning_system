# Patient Deterioration System - Deployment Guide

## 🚀 Production Deployment

This guide covers deploying the Patient Deterioration System in production.

### Quick Start

The simplest way to deploy is using the production server:

```bash
# 1. Build the React application
npm run build

# 2. Start the production server
python3 production_server.py
```

The application will be available at: http://localhost:8000

### Deployment Options

#### Option 1: Standalone Production Server

**Requirements:**
- Python 3.8+
- Node.js 16+ (for building the React app)
- SQLite3

**Steps:**

1. **Prepare the application:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Start production server:**
   ```bash
   python3 production_server.py
   ```

3. **Access the application:**
   - Web Interface: http://localhost:8000
   - API Health Check: http://localhost:8000/health

#### Option 2: Docker Deployment

**Requirements:**
- Docker
- Docker Compose

**Steps:**

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose -f docker-compose.production.yml up --build
   ```

2. **Access the application:**
   - Web Interface: http://localhost:8000

#### Option 3: Simple Deployment Script

Use the provided deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

### Production Configuration

#### Environment Variables

Create a `.env.production` file:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_API_KEY=secure-api-key-change-in-production
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
INLINE_RUNTIME_CHUNK=false
```

#### Security Configuration

⚠️ **Important Security Settings:**

1. **Change default credentials:**
   - Default user: test@example.com / password123
   - Create new admin users after deployment

2. **Update API key:**
   - Change `REACT_APP_API_KEY` to a secure random string
   - Update `production_server.py` JWT secret

3. **Database security:**
   - Ensure SQLite database file has proper permissions
   - Consider using PostgreSQL for production

### System Requirements

- **CPU:** 1 core minimum, 2 cores recommended
- **RAM:** 512MB minimum, 1GB recommended
- **Storage:** 1GB minimum for application and database
- **Network:** Port 8000 should be accessible

### Default Test Credentials

- **Email:** test@example.com
- **Password:** password123
- **Role:** nurse

### Health Monitoring

Monitor application health via:
- **Health endpoint:** GET /health
- **Expected response:** `{"status": "healthy", "timestamp": "..."}`

### Production Features

The production server includes:

✅ **Optimized serving** - Compressed React build
✅ **API endpoints** - All backend functionality
✅ **Database management** - Automatic SQLite setup
✅ **Static file serving** - Efficient file delivery
✅ **Health monitoring** - Built-in health checks
✅ **Error handling** - Graceful error responses
✅ **Security headers** - Basic security configuration

### Troubleshooting

#### Common Issues

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill <PID>
```

**Database errors:**
```bash
# Check database file permissions
ls -la patient_ews.db
# Recreate database (will lose data)
rm patient_ews.db
python3 production_server.py
```

**Build errors:**
```bash
# Clear npm cache
npm cache clean --force
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Scaling Considerations

For production deployments at scale:

1. **Load balancer:** Use nginx or Apache as reverse proxy
2. **Database:** Migrate to PostgreSQL or MySQL
3. **SSL/TLS:** Configure HTTPS certificates
4. **Monitoring:** Add logging and monitoring tools
5. **Backup:** Implement database backup strategy

### Support

For deployment issues:
1. Check the application logs
2. Verify all dependencies are installed
3. Ensure ports are available
4. Check file permissions

---

**🎉 Your Patient Deterioration System is now ready for production!**