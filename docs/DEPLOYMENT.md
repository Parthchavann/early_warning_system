# Deployment Guide

This guide provides comprehensive instructions for deploying the Patient Deterioration Early Warning System in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Configuration Management](#configuration-management)
7. [Monitoring Setup](#monitoring-setup)
8. [Security Configuration](#security-configuration)
9. [Scaling Guidelines](#scaling-guidelines)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 1Gbps

**Recommended for Production:**
- CPU: 16+ cores
- RAM: 32GB+
- Storage: 200GB+ NVMe SSD
- Network: 10Gbps

### Software Dependencies

- Docker Engine 20.10+
- Docker Compose 2.0+
- Kubernetes 1.25+ (for K8s deployment)
- Python 3.11+
- PostgreSQL 15+

### Network Requirements

**Inbound Ports:**
- 8000 (API)
- 8501 (Dashboard)
- 3000 (Grafana)
- 5000 (MLflow)
- 9090 (Prometheus)

**Outbound Access:**
- HTTPS (443) for model downloads
- SMTP for email alerts
- Cloud provider APIs (if applicable)

## Local Development

### Quick Start

1. **Clone and Setup**
```bash
git clone <repository-url>
cd patient-deterioration-system
cp .env.example .env
```

2. **Configure Environment**
```bash
# Edit .env file with local settings
vim .env

# Key settings for local development:
DATABASE_URL=postgresql://ews_user:password@localhost:5432/patient_ews
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MLFLOW_TRACKING_URI=http://localhost:5000
API_KEY=dev-api-key-not-for-production
```

3. **Start Services**
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs -f ews-api
```

4. **Initialize System**
```bash
# Initialize database
docker-compose exec ews-api python scripts/init_db.py

# Train initial model (optional)
docker-compose exec ews-api python scripts/train_model.py --n-patients 500
```

5. **Verify Deployment**
```bash
# API health check
curl http://localhost:8000/health

# Dashboard access
open http://localhost:8501

# MLflow UI
open http://localhost:5000
```

### Development Tools

**Database Access**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ews_user -d patient_ews

# View tables
\\dt
```

**Log Monitoring**
```bash
# Real-time logs
docker-compose logs -f ews-api dashboard

# Specific service logs
docker-compose logs kafka postgres
```

**Performance Testing**
```bash
# API load testing
ab -n 1000 -c 10 -H \"Authorization: Bearer dev-api-key\" \
   http://localhost:8000/health

# Database performance
docker-compose exec postgres pg_stat_statements
```

## Docker Deployment

### Production Docker Compose

1. **Production Configuration**
```bash
# Copy production template
cp docker-compose.prod.yml docker-compose.yml

# Configure secrets
echo \"secure-production-password\" | docker secret create db_password -
echo \"production-api-key-256-chars\" | docker secret create api_key -
```

2. **Environment Variables**
```bash
# Production environment file
cat > .env.prod << EOF
ENVIRONMENT=production
DATABASE_URL=postgresql://ews_user:\${DB_PASSWORD}@postgres:5432/patient_ews
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
MLFLOW_TRACKING_URI=http://mlflow:5000
API_KEY=\${API_KEY}
LOG_LEVEL=INFO
ENABLE_CORS=false
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=\${GRAFANA_PASSWORD}
EOF
```

3. **Deploy Stack**
```bash
# Deploy with production config
docker-compose -f docker-compose.yml --env-file .env.prod up -d

# Scale API services
docker-compose up -d --scale ews-api=3

# Verify deployment
docker-compose ps
```

### Health Checks

```bash
# Service health verification
curl -f http://localhost:8000/health || echo \"API unhealthy\"
curl -f http://localhost:8501/health || echo \"Dashboard unhealthy\"

# Database connectivity
docker-compose exec ews-api python -c \"
from src.models.database import DatabaseManager
db = DatabaseManager()
print('Database connection:', 'OK' if db.engine else 'FAILED')
\"

# Model loading
docker-compose exec ews-api python -c \"
from src.ml_models.deterioration_models import DeteriorationPredictor
model = DeteriorationPredictor()
print('Model loading:', 'OK' if model else 'FAILED')
\"
```

## Kubernetes Deployment

### Cluster Setup

1. **Namespace Creation**
```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl get namespaces
```

2. **Secrets Management**
```bash
# Database password
kubectl create secret generic postgres-secret \
  --from-literal=password=\"secure-production-password\" \
  -n patient-ews

# API keys and sensitive data
kubectl create secret generic ews-secrets \
  --from-literal=api-key=\"production-api-key-256-chars\" \
  --from-literal=database-url=\"postgresql://ews_user:secure-production-password@postgres-service:5432/patient_ews\" \
  --from-literal=openai-api-key=\"your-openai-key\" \
  -n patient-ews

# Verify secrets
kubectl get secrets -n patient-ews
```

3. **Storage Configuration**
```bash
# Apply storage classes (if not default)
kubectl apply -f deployment/kubernetes/storage-class.yaml

# Verify persistent volumes
kubectl get pv
kubectl get pvc -n patient-ews
```

### Application Deployment

1. **Database Deployment**
```bash
kubectl apply -f deployment/kubernetes/postgres-deployment.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n patient-ews --timeout=300s
```

2. **Supporting Services**
```bash
# Deploy Kafka, Redis, Qdrant
kubectl apply -f deployment/kubernetes/kafka-deployment.yaml
kubectl apply -f deployment/kubernetes/redis-deployment.yaml
kubectl apply -f deployment/kubernetes/qdrant-deployment.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=kafka -n patient-ews --timeout=300s
```

3. **Core Application**
```bash
# Deploy API
kubectl apply -f deployment/kubernetes/ews-api-deployment.yaml
kubectl wait --for=condition=ready pod -l app=ews-api -n patient-ews --timeout=300s

# Deploy Dashboard
kubectl apply -f deployment/kubernetes/dashboard-deployment.yaml

# Deploy monitoring
kubectl apply -f deployment/kubernetes/monitoring-deployment.yaml
```

### Service Verification

```bash
# Check all pods
kubectl get pods -n patient-ews

# Check services
kubectl get services -n patient-ews

# Check ingress (if configured)
kubectl get ingress -n patient-ews

# Check logs
kubectl logs -f deployment/ews-api -n patient-ews
```

### Autoscaling Configuration

```yaml
# horizontal-pod-autoscaler.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ews-api-hpa
  namespace: patient-ews
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ews-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

```bash
kubectl apply -f horizontal-pod-autoscaler.yaml
kubectl get hpa -n patient-ews
```

## Cloud Deployment

### AWS Deployment

1. **EKS Cluster Setup**
```bash
# Create EKS cluster
eksctl create cluster --name patient-ews-cluster \
  --version 1.28 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed

# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name patient-ews-cluster
```

2. **RDS Database**
```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier patient-ews-db \
  --db-instance-class db.t3.large \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 100 \
  --storage-type gp2 \
  --storage-encrypted \
  --db-name patient_ews \
  --master-username ews_user \
  --master-user-password \"$(openssl rand -base64 32)\" \
  --vpc-security-group-ids sg-xxxxxxxxx \
  --backup-retention-period 7 \
  --multi-az
```

3. **Managed Services Integration**
```yaml
# Update ConfigMap for AWS services
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-config
  namespace: patient-ews
data:
  region: \"us-west-2\"
  s3_bucket: \"patient-ews-artifacts\"
  rds_endpoint: \"patient-ews-db.xxxxxxxxx.us-west-2.rds.amazonaws.com\"
  elasticache_endpoint: \"patient-ews-redis.xxxxxx.cache.amazonaws.com:6379\"
```

### GCP Deployment

1. **GKE Cluster**
```bash
# Create GKE cluster
gcloud container clusters create patient-ews-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --machine-type e2-standard-4 \
  --enable-autorepair \
  --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials patient-ews-cluster --zone us-central1-a
```

2. **Cloud SQL**
```bash
# Create Cloud SQL instance
gcloud sql instances create patient-ews-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-4-16384 \
  --region=us-central1 \
  --storage-size=100GB \
  --storage-type=SSD \
  --backup-start-time=02:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03

# Create database
gcloud sql databases create patient_ews --instance=patient-ews-db
```

### Azure Deployment

1. **AKS Cluster**
```bash
# Create resource group
az group create --name patient-ews-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group patient-ews-rg \
  --name patient-ews-cluster \
  --node-count 3 \
  --enable-autoscaler \
  --min-count 1 \
  --max-count 10 \
  --node-vm-size Standard_D4s_v3 \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group patient-ews-rg --name patient-ews-cluster
```

2. **Azure Database for PostgreSQL**
```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group patient-ews-rg \
  --name patient-ews-db \
  --location eastus \
  --admin-user ews_user \
  --admin-password \"$(openssl rand -base64 32)\" \
  --sku-name GP_Gen5_4 \
  --version 15 \
  --storage-size 102400

# Create database
az postgres db create \
  --resource-group patient-ews-rg \
  --server-name patient-ews-db \
  --name patient_ews
```

## Configuration Management

### Environment-Specific Configs

**Development (`.env.dev`)**
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
KAFKA_AUTO_CREATE_TOPICS=true
ML_MODEL_CACHE=false
ENABLE_SYNTHETIC_DATA=true
```

**Staging (`.env.staging`)**
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
DEBUG=false
KAFKA_AUTO_CREATE_TOPICS=false
ML_MODEL_CACHE=true
ENABLE_SYNTHETIC_DATA=false
DATABASE_POOL_SIZE=10
```

**Production (`.env.prod`)**
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=false
KAFKA_AUTO_CREATE_TOPICS=false
ML_MODEL_CACHE=true
ENABLE_SYNTHETIC_DATA=false
DATABASE_POOL_SIZE=20
SECURE_COOKIES=true
CSRF_PROTECTION=true
```

### ConfigMaps and Secrets

```yaml
# config-map.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ews-config
  namespace: patient-ews
data:
  database_pool_size: \"20\"
  kafka_consumer_group: \"ews-consumers\"
  model_prediction_timeout: \"30\"
  alert_cooldown_hours: \"4\"
  max_concurrent_predictions: \"100\"
```

```bash
kubectl apply -f config-map.yaml
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - \"ews_rules.yml\"

scrape_configs:
  - job_name: 'ews-api'
    static_configs:
      - targets: ['ews-api-service:80']
    metrics_path: /metrics/prometheus
    scrape_interval: 30s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['kafka-exporter:9308']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboards

```bash
# Import predefined dashboards
kubectl create configmap grafana-dashboards \
  --from-file=deployment/monitoring/grafana/dashboards/ \
  -n patient-ews

# Apply dashboard provisioning
kubectl apply -f deployment/monitoring/grafana-dashboards.yaml
```

### Alert Rules

```yaml
# ews-alerts.yml
groups:
- name: patient-ews-alerts
  rules:
  - alert: HighAPILatency
    expr: histogram_quantile(0.95, ews_prediction_duration_seconds) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: \"High API latency detected\"
      description: \"95th percentile latency is {{ $value }}s\"

  - alert: ModelAccuracyDrop
    expr: ews_model_accuracy < 0.75
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: \"Model accuracy below threshold\"
      description: \"Current accuracy: {{ $value }}\"
```

## Security Configuration

### TLS/SSL Setup

1. **Certificate Management**
```bash
# Create TLS certificate (Let's Encrypt example)
certbot certonly --dns-route53 -d api.patient-ews.com -d dashboard.patient-ews.com

# Create Kubernetes secret
kubectl create secret tls ews-tls-secret \
  --cert=/etc/letsencrypt/live/patient-ews.com/fullchain.pem \
  --key=/etc/letsencrypt/live/patient-ews.com/privkey.pem \
  -n patient-ews
```

2. **Ingress with TLS**
```yaml
# ingress-tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ews-ingress
  namespace: patient-ews
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.patient-ews.com
    - dashboard.patient-ews.com
    secretName: ews-tls-secret
  rules:
  - host: api.patient-ews.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ews-api-service
            port:
              number: 80
```

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ews-network-policy
  namespace: patient-ews
spec:
  podSelector:
    matchLabels:
      app: ews-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: dashboard
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### RBAC Configuration

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ews-service-account
  namespace: patient-ews
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ews-role
  namespace: patient-ews
rules:
- apiGroups: [\"\"]
  resources: [\"pods\", \"services\", \"configmaps\", \"secrets\"]
  verbs: [\"get\", \"list\", \"watch\"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ews-role-binding
  namespace: patient-ews
subjects:
- kind: ServiceAccount
  name: ews-service-account
  namespace: patient-ews
roleRef:
  kind: Role
  name: ews-role
  apiGroup: rbac.authorization.k8s.io
```

## Scaling Guidelines

### Horizontal Scaling

**API Service Scaling**
```yaml
# Scale based on CPU and memory
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ews-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ews-api
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: pending_requests
      target:
        type: AverageValue
        averageValue: \"100\"
```

**Database Connection Pooling**
```python
# Database connection pool configuration
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_RECYCLE = 3600
DATABASE_POOL_PRE_PING = True
```

### Vertical Scaling

**Resource Requests/Limits**
```yaml
resources:
  requests:
    memory: \"1Gi\"
    cpu: \"500m\"
  limits:
    memory: \"2Gi\"
    cpu: \"2\"
```

### Performance Tuning

**API Service**
```python
# FastAPI/Uvicorn configuration
workers = 4  # CPU cores * 2
worker_class = \"uvicorn.workers.UvicornWorker\"
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

**Database Optimization**
```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

## Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check database status
kubectl logs -f deployment/postgres -n patient-ews

# Test connection from API pod
kubectl exec -it deployment/ews-api -n patient-ews -- \
  python -c \"from src.models.database import DatabaseManager; \
              db = DatabaseManager(); \
              print('Connection OK' if db.engine else 'Connection Failed')\"

# Check database configuration
kubectl get configmap ews-config -n patient-ews -o yaml
```

**2. Model Loading Issues**
```bash
# Check model files
kubectl exec -it deployment/ews-api -n patient-ews -- \
  ls -la /app/models/

# Check MLflow connection
kubectl exec -it deployment/ews-api -n patient-ews -- \
  python -c \"import mlflow; print(mlflow.get_tracking_uri())\"

# Re-download models
kubectl exec -it deployment/ews-api -n patient-ews -- \
  python scripts/download_models.py
```

**3. High Memory Usage**
```bash
# Check memory usage
kubectl top pods -n patient-ews

# Scale down resource-intensive services temporarily
kubectl scale deployment ews-api --replicas=1 -n patient-ews

# Check for memory leaks
kubectl exec -it deployment/ews-api -n patient-ews -- \
  python -c \"import gc; print(f'Objects: {len(gc.get_objects())}')\"
```

**4. Network Connectivity Issues**
```bash
# Test service connectivity
kubectl exec -it deployment/ews-api -n patient-ews -- \
  curl -f http://postgres-service:5432 || echo \"DB unreachable\"

kubectl exec -it deployment/ews-api -n patient-ews -- \
  curl -f http://kafka-service:9092 || echo \"Kafka unreachable\"

# Check DNS resolution
kubectl exec -it deployment/ews-api -n patient-ews -- \
  nslookup postgres-service
```

**5. Performance Issues**
```bash
# Check API response times
kubectl exec -it deployment/ews-api -n patient-ews -- \
  curl -w \"@curl-format.txt\" -o /dev/null -s http://localhost:8000/health

# Monitor database queries
kubectl exec -it deployment/postgres -n patient-ews -- \
  psql -U ews_user -d patient_ews -c \"SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;\"

# Check resource utilization
kubectl top nodes
kubectl top pods -n patient-ews --sort-by=memory
```

### Debugging Tools

**Log Aggregation**
```bash
# Centralized logging with ELK stack
kubectl apply -f deployment/logging/elasticsearch.yaml
kubectl apply -f deployment/logging/logstash.yaml  
kubectl apply -f deployment/logging/kibana.yaml

# Fluent Bit for log shipping
kubectl apply -f deployment/logging/fluent-bit.yaml
```

**Distributed Tracing**
```bash
# Jaeger for request tracing
kubectl apply -f deployment/tracing/jaeger.yaml

# Configure tracing in application
JAEGER_AGENT_HOST=jaeger-agent
JAEGER_AGENT_PORT=6831
JAEGER_SAMPLER_TYPE=const
JAEGER_SAMPLER_PARAM=1
```

**Health Check Scripts**
```bash
#!/bin/bash
# health-check.sh

echo \"Checking system health...\"

# API health
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo \"✓ API is healthy\"
else
    echo \"✗ API is unhealthy\"
fi

# Database health  
if kubectl exec deployment/postgres -n patient-ews -- pg_isready -U ews_user -d patient_ews > /dev/null 2>&1; then
    echo \"✓ Database is healthy\"
else
    echo \"✗ Database is unhealthy\"
fi

# MLflow health
if curl -f -s http://localhost:5000/health > /dev/null; then
    echo \"✓ MLflow is healthy\"
else
    echo \"✗ MLflow is unhealthy\"
fi

echo \"Health check complete.\"
```

This deployment guide provides comprehensive instructions for deploying the Patient Deterioration EWS across various environments. Choose the appropriate deployment method based on your infrastructure requirements and organizational constraints.