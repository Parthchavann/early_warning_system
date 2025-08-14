#!/bin/bash

# Patient Deterioration System - Deployment Script
echo "🚀 Deploying Patient Deterioration System..."

# Stop any existing development servers
echo "🛑 Stopping development servers..."
pkill -f "simple_server.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

# Build React production bundle
echo "📦 Building React production bundle..."
npm run build

# Kill any existing production server
echo "🔄 Stopping existing production server..."
pkill -f "production_server.py" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Start production server
echo "🚀 Starting production server..."
python3 production_server.py &

# Wait for server to start
sleep 3

# Check if server is running
if pgrep -f "production_server.py" > /dev/null; then
    echo "✅ Production server started successfully!"
    echo "🌐 Application available at: http://localhost:8000"
    echo "📱 Login with: test@example.com / password123"
    echo ""
    echo "To stop the server: pkill -f production_server.py"
else
    echo "❌ Failed to start production server"
    exit 1
fi