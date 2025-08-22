#!/usr/bin/env python3
"""
Production-ready backend server for Render deployment
Optimized for Render's infrastructure with PostgreSQL support
"""

import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment configuration
PORT = int(os.getenv('PORT', 10000))
DATABASE_URL = os.getenv('DATABASE_URL')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# FastAPI app
app = FastAPI(
    title="Patient Deterioration Early Warning System",
    description="ML-enhanced patient monitoring and risk assessment API",
    version="2.0.0",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    """Get database connection (PostgreSQL or SQLite fallback)"""
    if DATABASE_URL and 'postgresql' in DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return get_sqlite_connection()
    else:
        return get_sqlite_connection()

def get_sqlite_connection():
    """Fallback SQLite connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'frontend', 'patient_monitoring.db')
    if not os.path.exists(db_path):
        db_path = 'patient_monitoring.db'
    return sqlite3.connect(db_path)

# Initialize database
def init_database():
    """Initialize database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id VARCHAR PRIMARY KEY,
                name VARCHAR,
                age INTEGER,
                gender VARCHAR,
                department VARCHAR,
                admission_date TIMESTAMP,
                bed_number VARCHAR,
                room_number VARCHAR,
                risk_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create vitals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vitals (
                id SERIAL PRIMARY KEY,
                patient_id VARCHAR,
                heart_rate INTEGER,
                blood_pressure_systolic INTEGER,
                blood_pressure_diastolic INTEGER,
                respiratory_rate INTEGER,
                temperature REAL,
                oxygen_saturation INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        
        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id VARCHAR PRIMARY KEY,
                patient_id VARCHAR,
                patient_name VARCHAR,
                severity VARCHAR,
                message TEXT,
                risk_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by VARCHAR,
                acknowledged_at TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    finally:
        if conn:
            conn.close()

# Enhanced ML Risk Scoring
class RiskCalculator:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        try:
            self.model = joblib.load('risk_model.pkl')
            self.scaler = joblib.load('risk_scaler.pkl')
            logger.info("Loaded existing ML model")
        except:
            logger.info("Creating new ML model")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create and train a default model"""
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        # Train with synthetic data for demonstration
        X_train = np.random.rand(1000, 6)
        y_train = np.random.randint(0, 2, 1000)
        self.model.fit(X_train, y_train)
        self.scaler.fit(X_train)
    
    def calculate_risk_score(self, vitals: Dict) -> float:
        """Calculate comprehensive risk score using clinical thresholds and ML"""
        try:
            # Clinical rule-based scoring
            clinical_risk = self._calculate_clinical_risk(vitals)
            
            # ML-based scoring
            ml_risk = self._calculate_ml_risk(vitals)
            
            # Combine scores (70% clinical, 30% ML)
            final_risk = (clinical_risk * 0.7) + (ml_risk * 0.3)
            
            return min(max(final_risk, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Risk calculation error: {e}")
            return 0.5  # Default moderate risk
    
    def _calculate_clinical_risk(self, vitals: Dict) -> float:
        """Evidence-based clinical risk assessment"""
        risk_factors = 0
        max_risk = 10
        
        # Heart rate (normal: 60-100 bpm)
        hr = vitals.get('heart_rate', 70)
        if hr < 50 or hr > 120:
            risk_factors += 3
        elif hr < 60 or hr > 100:
            risk_factors += 1
        
        # Blood pressure (normal systolic: 90-140 mmHg)
        sbp = vitals.get('blood_pressure_systolic', 120)
        if sbp < 90 or sbp > 180:
            risk_factors += 3
        elif sbp < 100 or sbp > 140:
            risk_factors += 1
        
        # Respiratory rate (normal: 12-20 /min)
        rr = vitals.get('respiratory_rate', 16)
        if rr < 8 or rr > 30:
            risk_factors += 3
        elif rr < 12 or rr > 20:
            risk_factors += 1
        
        # Temperature (normal: 36.1-37.2°C)
        temp = vitals.get('temperature', 36.8)
        if temp < 35 or temp > 39:
            risk_factors += 3
        elif temp < 36 or temp > 37.5:
            risk_factors += 1
        
        # Oxygen saturation (normal: >95%)
        spo2 = vitals.get('oxygen_saturation', 98)
        if spo2 < 88:
            risk_factors += 3
        elif spo2 < 95:
            risk_factors += 2
        
        return risk_factors / max_risk
    
    def _calculate_ml_risk(self, vitals: Dict) -> float:
        """ML-based risk prediction"""
        try:
            features = [
                vitals.get('heart_rate', 70),
                vitals.get('blood_pressure_systolic', 120),
                vitals.get('blood_pressure_diastolic', 80),
                vitals.get('respiratory_rate', 16),
                vitals.get('temperature', 36.8),
                vitals.get('oxygen_saturation', 98)
            ]
            
            features_scaled = self.scaler.transform([features])
            risk_prob = self.model.predict_proba(features_scaled)[0][1]
            
            return float(risk_prob)
            
        except Exception as e:
            logger.warning(f"ML risk calculation failed: {e}")
            return 0.5

# Initialize risk calculator
risk_calculator = RiskCalculator()

# API Models
class PatientCreate(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    name: str = Field(..., description="Patient full name")
    age: int = Field(..., ge=0, le=150, description="Patient age")
    gender: str = Field(..., description="Patient gender")
    department: str = Field(default="General Ward", description="Hospital department")
    bed_number: Optional[str] = Field(None, description="Bed number")
    room_number: Optional[str] = Field(None, description="Room number")

class VitalsCreate(BaseModel):
    heart_rate: int = Field(..., ge=0, le=300)
    blood_pressure_systolic: int = Field(..., ge=50, le=300)
    blood_pressure_diastolic: int = Field(..., ge=30, le=200)
    respiratory_rate: int = Field(..., ge=5, le=60)
    temperature: float = Field(..., ge=30.0, le=45.0)
    oxygen_saturation: int = Field(..., ge=50, le=100)
    timestamp: Optional[str] = None

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT,
        "database": "connected" if DATABASE_URL else "sqlite_fallback"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Patient Deterioration Early Warning System",
        "version": "2.0.0",
        "status": "operational",
        "environment": ENVIRONMENT
    }

@app.post("/patients")
async def create_patient(patient: PatientCreate):
    """Create a new patient"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO patients (patient_id, name, age, gender, department, bed_number, room_number, admission_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (patient_id) DO UPDATE SET
                name = EXCLUDED.name,
                age = EXCLUDED.age,
                gender = EXCLUDED.gender,
                department = EXCLUDED.department,
                bed_number = EXCLUDED.bed_number,
                room_number = EXCLUDED.room_number
        ''', (
            patient.patient_id, patient.name, patient.age, patient.gender,
            patient.department, patient.bed_number, patient.room_number,
            datetime.now()
        ))
        
        conn.commit()
        
        return {
            "message": "Patient created successfully",
            "patient_id": patient.patient_id
        }
        
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/patients")
async def get_all_patients():
    """Get all patients"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, 
                   COUNT(v.id) as vitals_count,
                   MAX(v.timestamp) as last_vitals
            FROM patients p
            LEFT JOIN vitals v ON p.patient_id = v.patient_id
            GROUP BY p.patient_id
            ORDER BY p.created_at DESC
        ''')
        
        patients = []
        for row in cursor.fetchall():
            if isinstance(row, dict):
                patients.append(dict(row))
            else:
                patients.append({
                    'patient_id': row[0],
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'department': row[4],
                    'admission_date': row[5],
                    'bed_number': row[6],
                    'room_number': row[7],
                    'risk_score': row[8],
                    'created_at': row[9],
                    'vitals_count': row[10],
                    'last_vitals': row[11]
                })
        
        return {
            "patients": patients,
            "count": len(patients)
        }
        
    except Exception as e:
        logger.error(f"Error fetching patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/patients/{patient_id}/vitals")
async def add_vitals(patient_id: str, vitals: VitalsCreate):
    """Add vital signs for a patient"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert vitals
        timestamp = vitals.timestamp or datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO vitals (patient_id, heart_rate, blood_pressure_systolic, 
                              blood_pressure_diastolic, respiratory_rate, temperature, 
                              oxygen_saturation, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            patient_id, vitals.heart_rate, vitals.blood_pressure_systolic,
            vitals.blood_pressure_diastolic, vitals.respiratory_rate,
            vitals.temperature, vitals.oxygen_saturation, timestamp
        ))
        
        # Calculate risk score
        risk_score = risk_calculator.calculate_risk_score(vitals.dict())
        
        # Update patient risk score
        cursor.execute('''
            UPDATE patients SET risk_score = %s WHERE patient_id = %s
        ''', (risk_score, patient_id))
        
        # Generate alert if high risk
        if risk_score > 0.7:
            await generate_alert(patient_id, risk_score, cursor)
        
        conn.commit()
        
        return {
            "message": "Vitals added successfully",
            "risk_score": risk_score,
            "alert_generated": risk_score > 0.7
        }
        
    except Exception as e:
        logger.error(f"Error adding vitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

async def generate_alert(patient_id: str, risk_score: float, cursor):
    """Generate alert for high-risk patient"""
    try:
        # Get patient info
        cursor.execute('SELECT name FROM patients WHERE patient_id = %s', (patient_id,))
        result = cursor.fetchone()
        patient_name = result[0] if result else f"Patient {patient_id}"
        
        # Create alert
        alert_id = f"ALERT_{int(datetime.now().timestamp())}_{patient_id}"
        severity = "critical" if risk_score > 0.8 else "high"
        message = f"Patient {patient_id} showing signs of deterioration (Risk: {risk_score:.2f})"
        
        cursor.execute('''
            INSERT INTO alerts (alert_id, patient_id, patient_name, severity, message, risk_score)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (alert_id, patient_id, patient_name, severity, message, risk_score))
        
        logger.info(f"Generated {severity} alert for patient {patient_id}")
        
    except Exception as e:
        logger.error(f"Error generating alert: {e}")

@app.get("/alerts/active")
async def get_active_alerts():
    """Get all active (unacknowledged) alerts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT alert_id, patient_id, patient_name, severity, message, 
                   risk_score, timestamp, is_acknowledged
            FROM alerts 
            WHERE is_acknowledged = FALSE 
            ORDER BY timestamp DESC
        ''')
        
        alerts = []
        for row in cursor.fetchall():
            if isinstance(row, dict):
                alerts.append(dict(row))
            else:
                alerts.append({
                    'alert_id': row[0],
                    'patient_id': row[1],
                    'patient_name': row[2],
                    'severity': row[3],
                    'message': row[4],
                    'risk_score': row[5],
                    'timestamp': str(row[6]),
                    'is_acknowledged': row[7]
                })
        
        return {
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.get("/stats/dashboard")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total patients
        cursor.execute('SELECT COUNT(*) FROM patients')
        total_patients = cursor.fetchone()[0]
        
        # Critical patients (risk > 0.8)
        cursor.execute('SELECT COUNT(*) FROM patients WHERE risk_score > 0.8')
        critical_patients = cursor.fetchone()[0]
        
        # Active alerts
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_acknowledged = FALSE')
        active_alerts = cursor.fetchone()[0]
        
        return {
            "total_patients": total_patients,
            "critical_patients": critical_patients,
            "active_alerts": active_alerts,
            "avg_response_time": 12  # Mock data
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    logger.info(f"Starting Patient Deterioration EWS API v2.0.0")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Database: {'PostgreSQL' if DATABASE_URL else 'SQLite'}")
    
    init_database()

if __name__ == "__main__":
    uvicorn.run(
        "backend_render:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info" if DEBUG else "warning",
        access_log=DEBUG
    )