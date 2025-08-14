# Multi-stage build for Patient Deterioration System
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build React app
RUN npm run build

# Production stage
FROM python:3.11-alpine AS production

# Install system dependencies
RUN apk add --no-cache \
    sqlite \
    sqlite-dev \
    gcc \
    musl-dev

# Set working directory
WORKDIR /app

# Copy production server and built React app
COPY production_server.py .
COPY --from=build /app/build ./build

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DB_PATH=/app/data/patient_ews.db
ENV JWT_SECRET=change-me-in-production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run production server
CMD ["python3", "production_server.py"]