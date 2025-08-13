"""
Application configuration settings
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_KEY: str = "secure-api-key-change-in-production"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://ews_user:secure_password@localhost:5432/patient_ews"
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_VITALS: str = "patient-vitals"
    KAFKA_TOPIC_NOTES: str = "clinical-notes"
    KAFKA_TOPIC_ALERTS: str = "deterioration-alerts"
    
    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "patient_deterioration"
    
    # Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "patient_embeddings"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Model Configuration
    MODEL_REGISTRY_PATH: str = "/app/models"
    PREDICTION_THRESHOLD: float = 0.7
    ALERT_COOLDOWN_HOURS: int = 4
    
    # Security
    JWT_SECRET_KEY: str = "your-jwt-secret-change-in-production"
    ENCRYPTION_KEY: str = "your-encryption-key-change-in-production"
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()