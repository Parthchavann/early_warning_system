#!/bin/bash

# Production Deployment Script for Patient Deterioration System
set -e

echo "🚀 Starting deployment of Patient Deterioration System..."

# Configuration
PROJECT_NAME="patient-deterioration-system"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if running as root on production
    if [[ $EUID -eq 0 ]] && [[ "$ENVIRONMENT" == "production" ]]; then
        warning "Running as root in production. Consider using a non-root user."
    fi
    
    log "✅ Prerequisites check passed"
}

# Environment setup
setup_environment() {
    log "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        log "Creating .env file from template..."
        cat > .env << EOF
# Production Environment Variables
NODE_ENV=production

# Security (CHANGE THESE IN PRODUCTION!)
JWT_SECRET=$(openssl rand -base64 32)
API_KEY=$(openssl rand -base64 24)

# Domain Configuration
CORS_ORIGIN=https://your-domain.com
DOMAIN=your-domain.com

# Database
BACKUP_INTERVAL=86400

# Logging
LOG_LEVEL=info

# SSL (if using HTTPS)
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
EOF
        warning "Created .env file with default values. Please update it with your production settings!"
    fi
    
    log "✅ Environment setup complete"
}

# Backup existing data
backup_data() {
    log "Creating backup..."
    
    mkdir -p $BACKUP_DIR
    
    # Backup database if exists
    if docker volume ls | grep -q "${PROJECT_NAME}_backend_data"; then
        log "Backing up database..."
        docker run --rm \
            -v ${PROJECT_NAME}_backend_data:/data:ro \
            -v $(pwd)/$BACKUP_DIR:/backup \
            alpine:latest \
            cp /data/patient_ews.db /backup/ || warning "Database backup failed"
    fi
    
    # Backup logs if exists  
    if docker volume ls | grep -q "${PROJECT_NAME}_backend_logs"; then
        log "Backing up logs..."
        docker run --rm \
            -v ${PROJECT_NAME}_backend_logs:/logs:ro \
            -v $(pwd)/$BACKUP_DIR:/backup \
            alpine:latest \
            sh -c "tar -czf /backup/logs.tar.gz -C /logs ." || warning "Logs backup failed"
    fi
    
    log "✅ Backup created at $BACKUP_DIR"
}

# Build and deploy
deploy() {
    log "Building and deploying application..."
    
    # Pull latest images
    log "Pulling latest base images..."
    docker-compose pull --ignore-pull-failures
    
    # Build application
    log "Building application images..."
    docker-compose build --no-cache
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose down || true
    
    # Start new containers
    log "Starting new containers..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check health
    check_health
    
    log "✅ Deployment complete"
}

# Health check
check_health() {
    log "Performing health checks..."
    
    # Check backend health
    for i in {1..10}; do
        if curl -f http://localhost:8080/health &>/dev/null; then
            log "✅ Backend is healthy"
            break
        else
            if [ $i -eq 10 ]; then
                error "Backend health check failed after 10 attempts"
            fi
            log "Waiting for backend... (attempt $i/10)"
            sleep 5
        fi
    done
    
    # Check frontend health  
    for i in {1..10}; do
        if curl -f http://localhost/health &>/dev/null; then
            log "✅ Frontend is healthy"
            break
        else
            if [ $i -eq 10 ]; then
                error "Frontend health check failed after 10 attempts"
            fi
            log "Waiting for frontend... (attempt $i/10)"
            sleep 5
        fi
    done
    
    log "✅ All services are healthy"
}

# Cleanup old images
cleanup() {
    log "Cleaning up old Docker images..."
    docker image prune -f || true
    log "✅ Cleanup complete"
}

# Show status
show_status() {
    log "=== Deployment Status ==="
    docker-compose ps
    
    echo ""
    log "=== Service URLs ==="
    log "Frontend: http://localhost"
    log "Backend API: http://localhost:8080"
    log "Health Check: http://localhost:8080/health"
    
    echo ""
    log "=== Logs ==="
    log "View logs: docker-compose logs -f"
    log "Backend logs: docker-compose logs -f backend"
    log "Frontend logs: docker-compose logs -f frontend"
}

# Main deployment flow
main() {
    log "🚀 Patient Deterioration System - Production Deployment"
    log "=================================================="
    
    check_prerequisites
    setup_environment
    backup_data
    deploy
    cleanup
    show_status
    
    log "🎉 Deployment completed successfully!"
    log "Please update your .env file with production values and restart if needed."
}

# Run main function
main "$@"