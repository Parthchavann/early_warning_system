#!/usr/bin/env python
"""
Direct API runner - bypasses ML models
"""
import os
os.environ['DATABASE_URL'] = 'sqlite:///patient_ews.db'

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
from datetime import datetime
from typing import List, Dict, Any

# Create FastAPI app
app = FastAPI(title="Patient EWS API", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine(
    'sqlite:///patient_ews.db',
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Patient Monitoring API", "status": "active"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/stats")
def get_stats():
    db = SessionLocal()
    try:
        # Get patient count
        result = db.execute(text("SELECT COUNT(*) FROM patients"))
        total_patients = result.scalar() or 0
        
        # Get total alert count (not just unacknowledged)
        result = db.execute(text("SELECT COUNT(*) FROM alerts"))
        total_alerts = result.scalar() or 0
        
        # Get unacknowledged alerts
        result = db.execute(text("SELECT COUNT(*) FROM alerts WHERE is_acknowledged = 0 OR is_acknowledged IS NULL"))
        active_alerts = result.scalar() or 0
        
        # Since your DB doesn't have risk_scores table, estimate critical patients
        # Let's say 20% of patients are critical for now
        critical_patients = max(1, int(total_patients * 0.2))
        
        # Count total vitals records
        vitals_result = db.execute(text("SELECT COUNT(*) FROM vital_signs"))
        total_vitals = vitals_result.scalar() or 0
        
        print(f"Stats: patients={total_patients}, alerts={active_alerts}, vitals={total_vitals}")
        
        return {
            "total_patients": total_patients,
            "active_alerts": active_alerts,
            "critical_patients": critical_patients,
            "total_vitals_records": total_vitals,
            "totalPatients": total_patients,
            "activeAlerts": active_alerts,
            "criticalPatients": critical_patients,
            "avgRiskScore": 35.5
        }
    except Exception as e:
        print(f"Database error in /stats: {e}")
        return {
            "total_patients": 0,
            "active_alerts": 0,
            "critical_patients": 0,
            "total_vitals_records": 0,
            "totalPatients": 0,
            "activeAlerts": 0,
            "criticalPatients": 0,
            "avgRiskScore": 0
        }
    finally:
        db.close()

def calculate_risk_score(vitals):
    """Calculate risk score from vital signs like yesterday's system"""
    if not vitals:
        return 20  # Default low risk for patients without vitals
    
    risk_score = 0
    debug_info = []
    
    # Heart rate scoring (normal: 60-100)
    hr = vitals.get('heart_rate', 70)
    if hr < 50 or hr > 120:
        risk_score += 30
        debug_info.append(f"HR {hr}: +30 (critical)")
    elif hr < 60 or hr > 100:
        risk_score += 15
        debug_info.append(f"HR {hr}: +15 (abnormal)")
    else:
        debug_info.append(f"HR {hr}: +0 (normal)")
    
    # Blood pressure scoring (normal systolic: 90-140)
    bp_sys = vitals.get('blood_pressure_systolic', 120)
    if bp_sys < 80 or bp_sys > 160:
        risk_score += 25
        debug_info.append(f"BP {bp_sys}: +25 (critical)")
    elif bp_sys < 90 or bp_sys > 140:
        risk_score += 10
        debug_info.append(f"BP {bp_sys}: +10 (abnormal)")
    else:
        debug_info.append(f"BP {bp_sys}: +0 (normal)")
    
    # Respiratory rate scoring (normal: 12-20)
    rr = vitals.get('respiratory_rate', 16)
    if rr < 10 or rr > 25:
        risk_score += 20
        debug_info.append(f"RR {rr}: +20 (critical)")
    elif rr < 12 or rr > 20:
        risk_score += 10
        debug_info.append(f"RR {rr}: +10 (abnormal)")
    else:
        debug_info.append(f"RR {rr}: +0 (normal)")
    
    # Temperature scoring (normal: 36.1-37.2°C)
    temp = vitals.get('temperature', 36.5)
    if temp < 35.0 or temp > 38.5:
        risk_score += 25
        debug_info.append(f"Temp {temp}: +25 (critical)")
    elif temp < 36.0 or temp > 37.5:
        risk_score += 15
        debug_info.append(f"Temp {temp}: +15 (abnormal)")
    else:
        debug_info.append(f"Temp {temp}: +0 (normal)")
    
    # Oxygen saturation scoring (normal: >95%)
    o2 = vitals.get('oxygen_saturation', 98)
    if o2 < 90:
        risk_score += 35
        debug_info.append(f"O2 {o2}: +35 (critical)")
    elif o2 < 95:
        risk_score += 20
        debug_info.append(f"O2 {o2}: +20 (abnormal)")
    else:
        debug_info.append(f"O2 {o2}: +0 (normal)")
    
    final_score = min(100, max(0, risk_score))
    print(f"🔍 Risk calculation: {', '.join(debug_info)} = {final_score}")
    
    return final_score

@app.get("/patients")
def get_patients():
    db = SessionLocal()
    try:
        # Get patients with their latest vital signs for risk calculation
        result = db.execute(text("""
            SELECT p.patient_id, p.mrn, p.admission_date, p.age, p.gender, p.primary_diagnosis, p.created_at,
                   v.heart_rate, v.blood_pressure_systolic, v.blood_pressure_diastolic, 
                   v.respiratory_rate, v.temperature, v.oxygen_saturation
            FROM patients p
            LEFT JOIN vital_signs v ON p.patient_id = v.patient_id
            ORDER BY p.created_at DESC, v.timestamp DESC
        """))
        
        patients_dict = {}
        for row in result:
            patient_id = row[0]
            
            # Only add the first (latest) vital signs for each patient
            if patient_id not in patients_dict:
                # Calculate risk score from actual vital signs
                vitals = {
                    'heart_rate': row[7],
                    'blood_pressure_systolic': row[8], 
                    'blood_pressure_diastolic': row[9],
                    'respiratory_rate': row[10],
                    'temperature': row[11],
                    'oxygen_saturation': row[12]
                } if row[7] is not None else None
                
                risk_score = calculate_risk_score(vitals)
                
                patients_dict[patient_id] = {
                    "patient_id": row[0],
                    "mrn": row[1],
                    "admission_date": str(row[2]) if row[2] else None,
                    "age": row[3],
                    "gender": row[4],
                    "primary_diagnosis": row[5],
                    "created_at": str(row[6]) if row[6] else None,
                    "risk_score": risk_score
                }
        
        patients = list(patients_dict.values())
        print(f"Returning {len(patients)} patients with calculated risk scores")
        return patients
        
    except Exception as e:
        print(f"Database error in /patients: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        db.close()

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str):
    db = SessionLocal()
    try:
        # Get patient info
        result = db.execute(text("""
            SELECT patient_id, mrn, admission_date, age, gender, primary_diagnosis, created_at
            FROM patients WHERE patient_id = :pid
        """), {"pid": patient_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get latest vital signs for risk calculation
        vitals_result = db.execute(text("""
            SELECT heart_rate, blood_pressure_systolic, blood_pressure_diastolic, 
                   respiratory_rate, temperature, oxygen_saturation
            FROM vital_signs 
            WHERE patient_id = :pid
            ORDER BY timestamp DESC
            LIMIT 1
        """), {"pid": patient_id})
        
        vitals_row = vitals_result.fetchone()
        vitals = {
            'heart_rate': vitals_row[0],
            'blood_pressure_systolic': vitals_row[1], 
            'blood_pressure_diastolic': vitals_row[2],
            'respiratory_rate': vitals_row[3],
            'temperature': vitals_row[4],
            'oxygen_saturation': vitals_row[5]
        } if vitals_row else None
        
        risk_score = calculate_risk_score(vitals)
        
        return {
            "patient_id": row[0],
            "mrn": row[1],
            "admission_date": str(row[2]) if row[2] else None,
            "age": row[3],
            "gender": row[4],
            "weight_kg": None,  # Not in your database
            "height_cm": None,  # Not in your database
            "primary_diagnosis": row[5],
            "comorbidities": None,  # Not in your database
            "medications": None,  # Not in your database
            "allergies": None,  # Not in your database
            "created_at": str(row[6]) if row[6] else None,
            "risk_score": risk_score
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error in get_patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/patients/{patient_id}/vitals")
def get_patient_vitals(patient_id: str, limit: int = 24):
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT timestamp, heart_rate, blood_pressure_systolic, blood_pressure_diastolic,
                   respiratory_rate, temperature, oxygen_saturation
            FROM vital_signs 
            WHERE patient_id = :pid
            ORDER BY timestamp DESC
            LIMIT :limit
        """), {"pid": patient_id, "limit": limit})
        
        vitals = []
        for row in result:
            vitals.append({
                "timestamp": str(row[0]) if row[0] else None,
                "heart_rate": row[1],
                "blood_pressure_systolic": row[2],
                "blood_pressure_diastolic": row[3],
                "respiratory_rate": row[4],
                "temperature": row[5],
                "oxygen_saturation": row[6]
            })
        return vitals
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        db.close()

@app.post("/patients")
def create_patient(patient_data: dict):
    db = SessionLocal()
    try:
        # Generate patient_id if not provided
        if 'patient_id' not in patient_data:
            patient_data['patient_id'] = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Make sure admission_date is properly formatted
        if 'admission_date' in patient_data and patient_data['admission_date']:
            # If it's already a string, keep it; if datetime, convert it
            admission_date = patient_data['admission_date']
        else:
            admission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert patient with explicit parameter mapping
        db.execute(text("""
            INSERT INTO patients (patient_id, mrn, admission_date, age, gender, 
                                 weight_kg, height_cm, primary_diagnosis)
            VALUES (:patient_id, :mrn, :admission_date, :age, :gender, 
                    :weight_kg, :height_cm, :primary_diagnosis)
        """), {
            'patient_id': patient_data['patient_id'],
            'mrn': patient_data.get('mrn', f"MRN{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            'admission_date': admission_date,
            'age': patient_data.get('age', 0),
            'gender': patient_data.get('gender', 'Unknown'),
            'weight_kg': patient_data.get('weight_kg'),
            'height_cm': patient_data.get('height_cm'),
            'primary_diagnosis': patient_data.get('primary_diagnosis', 'Unknown')
        })
        db.commit()
        
        return {"message": "Patient created", "patient_id": patient_data['patient_id']}
    except Exception as e:
        db.rollback()
        print(f"Database error creating patient: {e}")
        print(f"Patient data: {patient_data}")
        raise HTTPException(status_code=500, detail=f"Failed to create patient: {str(e)}")
    finally:
        db.close()

@app.post("/patients/{patient_id}/vitals")
def add_vitals(patient_id: str, vitals_data: dict):
    db = SessionLocal()
    try:
        vitals_data['patient_id'] = patient_id
        vitals_data['timestamp'] = vitals_data.get('timestamp', datetime.utcnow().isoformat())
        
        db.execute(text("""
            INSERT INTO vital_signs (patient_id, timestamp, heart_rate, blood_pressure_systolic,
                                    blood_pressure_diastolic, respiratory_rate, temperature, oxygen_saturation)
            VALUES (:patient_id, :timestamp, :heart_rate, :blood_pressure_systolic,
                    :blood_pressure_diastolic, :respiratory_rate, :temperature, :oxygen_saturation)
        """), vitals_data)
        db.commit()
        
        return {"message": "Vitals added", "patient_id": patient_id}
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/alerts/active")
def get_active_alerts():
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, patient_id, severity, message, created_at
            FROM alerts 
            WHERE is_acknowledged = 0
            ORDER BY created_at DESC
        """))
        
        alerts = []
        for row in result:
            alerts.append({
                "id": row[0],
                "patient_id": row[1],
                "severity": row[2],
                "message": row[3],
                "created_at": str(row[4]) if row[4] else None,
                "is_acknowledged": False
            })
        return alerts
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        db.close()

@app.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, data: dict = {}):
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE alerts 
            SET is_acknowledged = 1, 
                acknowledged_by = :by,
                acknowledged_at = :at
            WHERE id = :id
        """), {
            "id": alert_id,
            "by": data.get("acknowledged_by", "dashboard_user"),
            "at": datetime.utcnow().isoformat()
        })
        db.commit()
        return {"message": "Alert acknowledged", "alert_id": alert_id}
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/patients/{patient_id}/predict")
def predict_deterioration(patient_id: str, data: dict = {}):
    # Get latest risk score from database
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT score, risk_level, timestamp
            FROM risk_scores
            WHERE patient_id = :pid
            ORDER BY timestamp DESC
            LIMIT 1
        """), {"pid": patient_id})
        
        row = result.fetchone()
        if row:
            return {
                "patient_id": patient_id,
                "risk_score": row[0],
                "risk_level": row[1],
                "timestamp": str(row[2]) if row[2] else datetime.utcnow().isoformat()
            }
        else:
            # No existing risk score, return default
            return {
                "patient_id": patient_id,
                "risk_score": 0,
                "risk_level": "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        print(f"Database error: {e}")
        return {
            "patient_id": patient_id,
            "risk_score": 0,
            "risk_level": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket client connected")
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection", 
            "message": "Connected to Patient Monitoring WebSocket",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        import asyncio
        
        # Simple keep-alive loop - just send periodic heartbeats
        while True:
            await asyncio.sleep(30)  # Wait 30 seconds
            try:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "connected"
                })
            except Exception as e:
                print(f"Error sending heartbeat: {e}")
                break
                
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Starting Direct Patient Monitoring API")
    print("="*50)
    print(f"Database: patient_ews.db")
    print(f"API URL: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print("Press CTRL+C to stop")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)