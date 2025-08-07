from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VitalSigns(BaseModel):
    timestamp: datetime
    heart_rate: Optional[float] = Field(None, ge=0, le=300)
    blood_pressure_systolic: Optional[float] = Field(None, ge=0, le=300)
    blood_pressure_diastolic: Optional[float] = Field(None, ge=0, le=200)
    respiratory_rate: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=30, le=45)
    oxygen_saturation: Optional[float] = Field(None, ge=0, le=100)
    glasgow_coma_scale: Optional[int] = Field(None, ge=3, le=15)
    
class LabResult(BaseModel):
    timestamp: datetime
    test_name: str
    value: float
    unit: str
    reference_range_min: Optional[float] = None
    reference_range_max: Optional[float] = None
    is_critical: bool = False

class ClinicalNote(BaseModel):
    timestamp: datetime
    author_id: str
    author_role: str
    note_type: str
    content: str
    processed_content: Optional[str] = None
    embeddings: Optional[List[float]] = None

class Patient(BaseModel):
    patient_id: str
    mrn: str
    admission_date: datetime
    age: int = Field(ge=0, le=150)
    gender: str
    weight_kg: Optional[float] = Field(None, ge=0, le=500)
    height_cm: Optional[float] = Field(None, ge=0, le=300)
    primary_diagnosis: str
    comorbidities: List[str] = []
    medications: List[Dict[str, Any]] = []
    allergies: List[str] = []
    
class RiskScore(BaseModel):
    timestamp: datetime
    patient_id: str
    overall_risk: float = Field(ge=0, le=1)
    sepsis_risk: float = Field(ge=0, le=1)
    cardiac_risk: float = Field(ge=0, le=1)
    respiratory_risk: float = Field(ge=0, le=1)
    neurological_risk: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    contributing_factors: List[Dict[str, Any]] = []
    
class Alert(BaseModel):
    alert_id: str
    timestamp: datetime
    patient_id: str
    severity: AlertSeverity
    alert_type: str
    message: str
    risk_score: RiskScore
    recommended_actions: List[str] = []
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
class PredictionRequest(BaseModel):
    patient_id: str
    include_historical: bool = True
    lookback_hours: int = Field(default=24, ge=1, le=168)
    
class PredictionResponse(BaseModel):
    patient_id: str
    prediction_timestamp: datetime
    risk_score: RiskScore
    alerts: List[Alert] = []
    explanation: Dict[str, Any]
    patient_summary: Optional[str] = None