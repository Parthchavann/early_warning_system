#!/usr/bin/env python3
"""
Original API format but simplified to work without ML dependencies
Using the same risk calculation logic as yesterday's system
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

os.environ['DATABASE_URL'] = 'sqlite:///patient_ews.db'

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn
from datetime import datetime
# Removed pandas/numpy dependencies

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

def _fallback_risk_calculation(vitals_data):
    """Original fallback risk calculation from main.py - returns 0.0-1.0"""
    if not vitals_data:
        print("🔍 No vitals data - returning default risk 0.1")
        return 0.1
        
    risk_factors = 0
    debug_info = []
    
    # Heart rate check (original thresholds from main.py)
    hr = vitals_data.get('heart_rate')
    if hr is not None and (hr < 50 or hr > 120):
        risk_factors += 1
        debug_info.append(f"HR {hr}: +1 (abnormal)")
    else:
        debug_info.append(f"HR {hr}: +0 (normal)")
    
    # Blood pressure check (original thresholds)
    bp_sys = vitals_data.get('blood_pressure_systolic')
    if bp_sys is not None and (bp_sys < 90 or bp_sys > 160):
        risk_factors += 1
        debug_info.append(f"BP {bp_sys}: +1 (abnormal)")
    else:
        debug_info.append(f"BP {bp_sys}: +0 (normal)")
    
    # Respiratory rate check (original thresholds)
    rr = vitals_data.get('respiratory_rate')
    if rr is not None and (rr < 10 or rr > 24):
        risk_factors += 1
        debug_info.append(f"RR {rr}: +1 (abnormal)")
    else:
        debug_info.append(f"RR {rr}: +0 (normal)")
    
    # Temperature check (original thresholds)
    temp = vitals_data.get('temperature')
    if temp is not None and (temp < 36 or temp > 38.5):
        risk_factors += 1
        debug_info.append(f"Temp {temp}: +1 (abnormal)")
    else:
        debug_info.append(f"Temp {temp}: +0 (normal)")
    
    # Oxygen saturation check (original threshold)
    spo2 = vitals_data.get('oxygen_saturation')
    if spo2 is not None and spo2 < 94:
        risk_factors += 1
        debug_info.append(f"O2 {spo2}: +1 (abnormal)")
    else:
        debug_info.append(f"O2 {spo2}: +0 (normal)")
    
    # Calculate final risk score (0.0-1.0 scale like original main.py)
    # Original formula: min(0.9, risk_factors * 0.2 + 0.1)
    final_risk = min(0.9, risk_factors * 0.2 + 0.1)
    
    print(f"🔍 Original risk calculation: {', '.join(debug_info)} = {risk_factors} factors = {final_risk}")
    
    return final_risk

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
        
        # Get alert counts
        result = db.execute(text("SELECT COUNT(*) FROM alerts"))
        total_alerts = result.scalar() or 0
        
        result = db.execute(text("SELECT COUNT(*) FROM alerts WHERE is_acknowledged = 0 OR is_acknowledged IS NULL"))
        active_alerts = result.scalar() or 0
        
        # Estimate critical patients (20% as in original)
        critical_patients = max(1, int(total_patients * 0.2))
        
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

@app.get("/patients")
def get_patients():
    db = SessionLocal()
    try:
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
            
            if patient_id not in patients_dict:
                # Get vitals for risk calculation
                vitals = None
                if row[7] is not None:  # has vital signs
                    vitals = {
                        'heart_rate': row[7],
                        'blood_pressure_systolic': row[8], 
                        'blood_pressure_diastolic': row[9],
                        'respiratory_rate': row[10],
                        'temperature': row[11],
                        'oxygen_saturation': row[12]
                    }
                
                # Use original risk calculation method
                risk_score = _fallback_risk_calculation(vitals)
                
                patients_dict[patient_id] = {
                    "patient_id": row[0],
                    "mrn": row[1],
                    "admission_date": str(row[2]) if row[2] else None,
                    "age": row[3],
                    "gender": row[4],
                    "primary_diagnosis": row[5],
                    "created_at": str(row[6]) if row[6] else None,
                    "risk_score": risk_score  # 0.0-1.0 scale like original
                }
        
        patients = list(patients_dict.values())
        print(f"Returning {len(patients)} patients with original risk score format")
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
        
        # Get latest vital signs
        vitals_result = db.execute(text("""
            SELECT heart_rate, blood_pressure_systolic, blood_pressure_diastolic, 
                   respiratory_rate, temperature, oxygen_saturation
            FROM vital_signs 
            WHERE patient_id = :pid
            ORDER BY timestamp DESC
            LIMIT 1
        """), {"pid": patient_id})
        
        vitals_row = vitals_result.fetchone()
        vitals = None
        if vitals_row:
            vitals = {
                'heart_rate': vitals_row[0],
                'blood_pressure_systolic': vitals_row[1], 
                'blood_pressure_diastolic': vitals_row[2],
                'respiratory_rate': vitals_row[3],
                'temperature': vitals_row[4],
                'oxygen_saturation': vitals_row[5]
            }
        
        risk_score = _fallback_risk_calculation(vitals)
        
        return {
            "patient_id": row[0],
            "mrn": row[1],
            "admission_date": str(row[2]) if row[2] else None,
            "age": row[3],
            "gender": row[4],
            "weight_kg": None,
            "height_cm": None,
            "primary_diagnosis": row[5],
            "comorbidities": None,
            "medications": None,
            "allergies": None,
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

@app.post("/patients/{patient_id}/predict")
def predict_deterioration(patient_id: str, data: dict = {}):
    """Prediction endpoint using original fallback calculation"""
    db = SessionLocal()
    try:
        # Get patient
        result = db.execute(text("""
            SELECT patient_id FROM patients WHERE patient_id = :pid
        """), {"pid": patient_id})
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get recent vitals 
        vitals_result = db.execute(text("""
            SELECT heart_rate, blood_pressure_systolic, blood_pressure_diastolic, 
                   respiratory_rate, temperature, oxygen_saturation
            FROM vital_signs 
            WHERE patient_id = :pid
            ORDER BY timestamp DESC
            LIMIT 1
        """), {"pid": patient_id})
        
        vitals_row = vitals_result.fetchone()
        vitals = None
        if vitals_row:
            vitals = {
                'heart_rate': vitals_row[0],
                'blood_pressure_systolic': vitals_row[1], 
                'blood_pressure_diastolic': vitals_row[2],
                'respiratory_rate': vitals_row[3],
                'temperature': vitals_row[4],
                'oxygen_saturation': vitals_row[5]
            }
        
        risk_score = _fallback_risk_calculation(vitals)
        
        # Determine risk level like original
        if risk_score > 0.8:
            risk_level = "critical"
        elif risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "patient_id": patient_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"Database error in predict: {e}")
        return {
            "patient_id": patient_id,
            "risk_score": 0.1,
            "risk_level": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
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

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket client connected")
    
    try:
        await websocket.send_json({
            "type": "connection", 
            "message": "Connected to Patient Monitoring WebSocket",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        import asyncio
        
        while True:
            await asyncio.sleep(30)
            try:
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
    print("\n" + "="*60)
    print("Starting ORIGINAL Patient Monitoring API")
    print("Using original risk calculation algorithm from main.py")
    print("="*60)
    print(f"Database: patient_ews.db")
    print(f"API URL: http://localhost:8000")
    print(f"Risk Score Format: 0.0-1.0 (like yesterday)")
    print("Press CTRL+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)