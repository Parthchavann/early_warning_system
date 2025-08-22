#!/usr/bin/env python3
"""
Simplified backend for Render deployment
Minimal dependencies, SQLite fallback
"""

import os
import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
PORT = int(os.getenv('PORT', 10000))
DATABASE_URL = os.getenv('DATABASE_URL')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# FastAPI app
app = FastAPI(
    title="Patient Deterioration Early Warning System",
    description="Patient monitoring and risk assessment API",
    version="2.0.0"
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
    """Get database connection (SQLite for now)"""
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
                patient_id TEXT PRIMARY KEY,
                name TEXT,
                age INTEGER,
                gender TEXT,
                department TEXT,
                admission_date TEXT,
                bed_number TEXT,
                room_number TEXT,
                risk_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create vitals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                heart_rate INTEGER,
                blood_pressure_systolic INTEGER,
                blood_pressure_diastolic INTEGER,
                respiratory_rate INTEGER,
                temperature REAL,
                oxygen_saturation INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        
        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                patient_id TEXT,
                patient_name TEXT,
                severity TEXT,
                message TEXT,
                risk_score REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                is_acknowledged INTEGER DEFAULT 0,
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

# Simple risk calculation
def calculate_risk_score(vitals: Dict) -> float:
    """Simple clinical risk assessment"""
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
    
    return min(risk_factors / max_risk, 1.0)

# API Models
class PatientCreate(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    department: str = "General Ward"
    bed_number: Optional[str] = None
    room_number: Optional[str] = None

class VitalsCreate(BaseModel):
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    respiratory_rate: int
    temperature: float
    oxygen_saturation: int
    timestamp: Optional[str] = None

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Patient Deterioration Early Warning System",
        "version": "2.0.0",
        "status": "operational"
    }

@app.post("/patients")
async def create_patient(patient: PatientCreate):
    """Create a new patient"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO patients 
            (patient_id, name, age, gender, department, bed_number, room_number, admission_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient.patient_id, patient.name, patient.age, patient.gender,
            patient.department, patient.bed_number, patient.room_number,
            datetime.now().isoformat()
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
            SELECT p.*, COUNT(v.id) as vitals_count
            FROM patients p
            LEFT JOIN vitals v ON p.patient_id = v.patient_id
            GROUP BY p.patient_id
            ORDER BY p.created_at DESC
        ''')
        
        patients = []
        for row in cursor.fetchall():
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
                'vitals_count': row[10]
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id, vitals.heart_rate, vitals.blood_pressure_systolic,
            vitals.blood_pressure_diastolic, vitals.respiratory_rate,
            vitals.temperature, vitals.oxygen_saturation, timestamp
        ))
        
        # Calculate risk score
        risk_score = calculate_risk_score(vitals.dict())
        
        # Update patient risk score
        cursor.execute('''
            UPDATE patients SET risk_score = ? WHERE patient_id = ?
        ''', (risk_score, patient_id))
        
        # Generate alert if high risk
        if risk_score > 0.7:
            # Get patient info
            cursor.execute('SELECT name FROM patients WHERE patient_id = ?', (patient_id,))
            result = cursor.fetchone()
            patient_name = result[0] if result else f"Patient {patient_id}"
            
            # Create alert
            alert_id = f"ALERT_{int(datetime.now().timestamp())}_{patient_id}"
            severity = "critical" if risk_score > 0.8 else "high"
            message = f"Patient {patient_id} showing signs of deterioration (Risk: {risk_score:.2f})"
            
            cursor.execute('''
                INSERT INTO alerts (alert_id, patient_id, patient_name, severity, message, risk_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (alert_id, patient_id, patient_name, severity, message, risk_score))
        
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
            WHERE is_acknowledged = 0 
            ORDER BY timestamp DESC
        ''')
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'alert_id': row[0],
                'patient_id': row[1],
                'patient_name': row[2],
                'severity': row[3],
                'message': row[4],
                'risk_score': row[5],
                'timestamp': row[6],
                'is_acknowledged': bool(row[7])
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
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE is_acknowledged = 0')
        active_alerts = cursor.fetchone()[0]
        
        return {
            "total_patients": total_patients,
            "critical_patients": critical_patients,
            "active_alerts": active_alerts,
            "avg_response_time": 12
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
    """Initialize database on startup"""
    logger.info(f"Starting Patient Deterioration EWS API v2.0.0")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Port: {PORT}")
    init_database()

if __name__ == "__main__":
    uvicorn.run(
        "backend_simple:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )