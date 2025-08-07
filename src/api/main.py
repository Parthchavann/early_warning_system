from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os
import asyncio
from sqlalchemy.orm import Session

from ..models.patient import (
    Patient, VitalSigns, ClinicalNote, RiskScore, Alert, 
    PredictionRequest, PredictionResponse, AlertSeverity
)
from ..models.database import DatabaseManager
from ..ml_models.deterioration_models import DeteriorationPredictor
from ..feature_engineering.feature_store import PatientFeatureExtractor
from ..utils.vector_search import PatientSimilarityService
from ..monitoring.metrics import MetricsCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GlobalState:
    def __init__(self):
        self.db_manager = None
        self.ml_predictor = None
        self.feature_extractor = None
        self.similarity_service = None
        self.metrics_collector = None
        self.is_ready = False

global_state = GlobalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up EWS API...")
    
    try:
        global_state.db_manager = DatabaseManager()
        global_state.db_manager.create_tables()
        
        global_state.ml_predictor = DeteriorationPredictor()
        
        model_path = os.getenv("MODEL_PATH", "/models/deterioration_model.joblib")
        if os.path.exists(model_path):
            global_state.ml_predictor.load_model(model_path)
            logger.info("Loaded trained model")
        else:
            logger.warning("No trained model found, using default configuration")
            
        global_state.feature_extractor = PatientFeatureExtractor()
        
        global_state.similarity_service = PatientSimilarityService()
        
        global_state.metrics_collector = MetricsCollector()
        
        global_state.is_ready = True
        logger.info("EWS API ready to serve requests")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise
    
    yield
    
    logger.info("Shutting down EWS API...")

app = FastAPI(
    title="Patient Deterioration Early Warning System",
    description="Real-time patient deterioration prediction and alerting system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    expected_token = os.getenv("API_KEY", "your-secure-api-key")
    
    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return token

def get_db_session():
    session = global_state.db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if global_state.is_ready else "initializing",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

@app.post("/patients", response_model=Dict[str, str])
async def create_patient(
    patient: Patient,
    db: Session = Depends(get_db_session),
    token: str = Depends(verify_token)
):
    try:
        existing_patient = global_state.db_manager.get_patient_by_id(db, patient.patient_id)
        if existing_patient:
            raise HTTPException(
                status_code=400,
                detail=f"Patient {patient.patient_id} already exists"
            )
        
        patient_data = patient.dict()
        saved_patient = global_state.db_manager.save_patient(db, patient_data)
        
        global_state.metrics_collector.increment_counter("patients_created")
        
        return {"message": f"Patient {patient.patient_id} created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patients/{patient_id}/vitals")
async def add_vital_signs(
    patient_id: str,
    vitals: VitalSigns,
    db: Session = Depends(get_db_session),
    token: str = Depends(verify_token)
):
    try:
        patient = global_state.db_manager.get_patient_by_id(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        vitals_data = vitals.dict()
        vitals_data['patient_id'] = patient_id
        
        saved_vitals = global_state.db_manager.save_vital_signs(db, vitals_data)
        
        global_state.metrics_collector.increment_counter("vitals_ingested")
        
        return {"message": "Vital signs added successfully", "id": saved_vitals.id}
        
    except Exception as e:
        logger.error(f"Error adding vital signs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patients/{patient_id}/predict", response_model=PredictionResponse)
async def predict_deterioration(
    patient_id: str,
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    token: str = Depends(verify_token)
):
    try:
        start_time = datetime.utcnow()
        
        patient = global_state.db_manager.get_patient_by_id(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        recent_vitals = global_state.db_manager.get_recent_vitals(
            db, patient_id, request.lookback_hours
        )
        
        if not recent_vitals:
            raise HTTPException(
                status_code=400,
                detail="No recent vital signs found for prediction"
            )
        
        vitals_df = pd.DataFrame([{
            'patient_id': v.patient_id,
            'timestamp': v.timestamp,
            'heart_rate': v.heart_rate,
            'blood_pressure_systolic': v.blood_pressure_systolic,
            'blood_pressure_diastolic': v.blood_pressure_diastolic,
            'respiratory_rate': v.respiratory_rate,
            'temperature': v.temperature,
            'oxygen_saturation': v.oxygen_saturation,
            'glasgow_coma_scale': v.glasgow_coma_scale
        } for v in recent_vitals])
        
        if not global_state.ml_predictor.is_trained:
            logger.warning("Using fallback prediction - model not trained")
            risk_score = _fallback_risk_calculation(vitals_df)
            confidence = 0.5
            explanation = "Risk calculated using traditional Early Warning Score"
            contributing_factors = ["ews_score", "vital_trends"]
        else:
            prediction_result = global_state.ml_predictor.predict_risk(
                vitals_df, patient_id
            )
            risk_score = prediction_result['risk_score']
            confidence = prediction_result['confidence']
            explanation = prediction_result['explanation']
            contributing_factors = prediction_result.get('contributing_factors', [])
        
        risk_score_obj = RiskScore(
            timestamp=datetime.utcnow(),
            patient_id=patient_id,
            overall_risk=risk_score,
            sepsis_risk=min(risk_score * 1.2, 1.0),
            cardiac_risk=risk_score * 0.8,
            respiratory_risk=risk_score * 0.9,
            neurological_risk=risk_score * 0.7,
            confidence=confidence,
            contributing_factors=[{"factor": f, "importance": 0.1} for f in contributing_factors]
        )
        
        alerts = []
        if risk_score > 0.8:
            alert = Alert(
                alert_id=f"alert_{patient_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.utcnow(),
                patient_id=patient_id,
                severity=AlertSeverity.CRITICAL,
                alert_type="deterioration_risk",
                message=f"High risk of deterioration detected (risk score: {risk_score:.2f})",
                risk_score=risk_score_obj,
                recommended_actions=[
                    "Increase monitoring frequency",
                    "Consider ICU evaluation",
                    "Review medications and fluid status",
                    "Notify attending physician"
                ]
            )
            alerts.append(alert)
            
            alert_data = alert.dict()
            global_state.db_manager.save_alert(db, alert_data)
            
        elif risk_score > 0.6:
            alert = Alert(
                alert_id=f"alert_{patient_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.utcnow(),
                patient_id=patient_id,
                severity=AlertSeverity.HIGH,
                alert_type="deterioration_risk",
                message=f"Elevated risk of deterioration (risk score: {risk_score:.2f})",
                risk_score=risk_score_obj,
                recommended_actions=[
                    "Increase vital sign monitoring",
                    "Review patient condition",
                    "Consider additional testing"
                ]
            )
            alerts.append(alert)
            
            alert_data = alert.dict()
            global_state.db_manager.save_alert(db, alert_data)
        
        response = PredictionResponse(
            patient_id=patient_id,
            prediction_timestamp=datetime.utcnow(),
            risk_score=risk_score_obj,
            alerts=alerts,
            explanation={
                "risk_factors": contributing_factors,
                "explanation_text": explanation,
                "data_quality": "good" if len(recent_vitals) > 10 else "limited"
            }
        )
        
        prediction_time = (datetime.utcnow() - start_time).total_seconds()
        global_state.metrics_collector.record_histogram("prediction_duration_seconds", prediction_time)
        global_state.metrics_collector.record_histogram("risk_scores", risk_score)
        global_state.metrics_collector.increment_counter("predictions_made")
        
        background_tasks.add_task(
            _update_patient_similarity_index,
            patient_id, patient, vitals_df
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _fallback_risk_calculation(vitals_df: pd.DataFrame) -> float:
    if vitals_df.empty:
        return 0.1
        
    latest_vitals = vitals_df.iloc[-1]
    
    risk_factors = 0
    
    hr = latest_vitals.get('heart_rate')
    if pd.notna(hr) and (hr < 50 or hr > 120):
        risk_factors += 1
        
    bp_sys = latest_vitals.get('blood_pressure_systolic')
    if pd.notna(bp_sys) and (bp_sys < 90 or bp_sys > 160):
        risk_factors += 1
        
    rr = latest_vitals.get('respiratory_rate')
    if pd.notna(rr) and (rr < 10 or rr > 24):
        risk_factors += 1
        
    temp = latest_vitals.get('temperature')
    if pd.notna(temp) and (temp < 36 or temp > 38.5):
        risk_factors += 1
        
    spo2 = latest_vitals.get('oxygen_saturation')
    if pd.notna(spo2) and spo2 < 94:
        risk_factors += 1
        
    return min(0.9, risk_factors * 0.2 + 0.1)

async def _update_patient_similarity_index(
    patient_id: str,
    patient: Any,
    vitals_df: pd.DataFrame
):
    try:
        demographics = {
            'age': patient.age,
            'gender': patient.gender,
            'primary_diagnosis': patient.primary_diagnosis,
            'comorbidities': patient.comorbidities
        }
        
        vitals_summary = {}
        for col in ['heart_rate', 'blood_pressure_systolic', 'respiratory_rate', 'temperature']:
            if col in vitals_df.columns:
                vitals_summary[f'{col}_mean'] = vitals_df[col].mean()
                
        global_state.similarity_service.index_patient(
            patient_id,
            demographics,
            vitals_summary,
            {},
            []
        )
        
        logger.debug(f"Updated similarity index for patient {patient_id}")
        
    except Exception as e:
        logger.error(f"Error updating similarity index: {e}")

@app.get("/patients/{patient_id}/similar", response_model=List[Dict[str, Any]])
async def find_similar_patients(
    patient_id: str,
    k: int = 5,
    db: Session = Depends(get_db_session),
    token: str = Depends(verify_token)
):
    try:
        patient = global_state.db_manager.get_patient_by_id(db, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        recent_vitals = global_state.db_manager.get_recent_vitals(db, patient_id, 24)
        
        demographics = {
            'age': patient.age,
            'gender': patient.gender,
            'primary_diagnosis': patient.primary_diagnosis,
            'comorbidities': patient.comorbidities
        }
        
        vitals_summary = {}
        if recent_vitals:
            vitals_df = pd.DataFrame([{
                'heart_rate': v.heart_rate,
                'blood_pressure_systolic': v.blood_pressure_systolic,
                'respiratory_rate': v.respiratory_rate,
                'temperature': v.temperature
            } for v in recent_vitals])
            
            for col in vitals_df.columns:
                vitals_summary[f'{col}_mean'] = vitals_df[col].mean()
        
        similar_patients = global_state.similarity_service.find_similar_patients(
            patient_id,
            demographics,
            vitals_summary,
            {},
            [],
            k=k
        )
        
        return similar_patients
        
    except Exception as e:
        logger.error(f"Error finding similar patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts/active", response_model=List[Dict[str, Any]])
async def get_active_alerts(
    patient_id: Optional[str] = None,
    db: Session = Depends(get_db_session),
    token: str = Depends(verify_token)
):
    try:
        alerts = global_state.db_manager.get_active_alerts(db, patient_id)
        
        alert_list = []
        for alert in alerts:
            alert_dict = {
                'alert_id': alert.alert_id,
                'patient_id': alert.patient_id,
                'timestamp': alert.timestamp,
                'severity': alert.severity,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'recommended_actions': alert.recommended_actions,
                'created_at': alert.created_at
            }
            alert_list.append(alert_dict)
            
        return alert_list
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    db: Session = Depends(get_db_session),
    token: str = Depends(verify_token)
):
    try:
        from ..models.database import AlertRecord
        
        alert = db.query(AlertRecord).filter_by(alert_id=alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.is_acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        db.commit()
        
        global_state.metrics_collector.increment_counter("alerts_acknowledged")
        
        return {"message": f"Alert {alert_id} acknowledged by {acknowledged_by}"}
        
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    return global_state.metrics_collector.generate_prometheus_metrics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=False
    )