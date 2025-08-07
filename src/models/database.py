from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import NullPool
import os
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class PatientRecord(Base):
    __tablename__ = "patients"
    
    patient_id = Column(String, primary_key=True)
    mrn = Column(String, unique=True, nullable=False)
    admission_date = Column(DateTime, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    primary_diagnosis = Column(String, nullable=False)
    comorbidities = Column(JSON)
    medications = Column(JSON)
    allergies = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vitals = relationship("VitalSignRecord", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResultRecord", back_populates="patient", cascade="all, delete-orphan")
    clinical_notes = relationship("ClinicalNoteRecord", back_populates="patient", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScoreRecord", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("AlertRecord", back_populates="patient", cascade="all, delete-orphan")

class VitalSignRecord(Base):
    __tablename__ = "vital_signs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    heart_rate = Column(Float)
    blood_pressure_systolic = Column(Float)
    blood_pressure_diastolic = Column(Float)
    respiratory_rate = Column(Float)
    temperature = Column(Float)
    oxygen_saturation = Column(Float)
    glasgow_coma_scale = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("PatientRecord", back_populates="vitals")

class LabResultRecord(Base):
    __tablename__ = "lab_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    test_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String)
    reference_range_min = Column(Float)
    reference_range_max = Column(Float)
    is_critical = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("PatientRecord", back_populates="lab_results")

class ClinicalNoteRecord(Base):
    __tablename__ = "clinical_notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    author_id = Column(String, nullable=False)
    author_role = Column(String, nullable=False)
    note_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    processed_content = Column(Text)
    embeddings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("PatientRecord", back_populates="clinical_notes")

class RiskScoreRecord(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    overall_risk = Column(Float, nullable=False)
    sepsis_risk = Column(Float)
    cardiac_risk = Column(Float)
    respiratory_risk = Column(Float)
    neurological_risk = Column(Float)
    confidence = Column(Float, nullable=False)
    contributing_factors = Column(JSON)
    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("PatientRecord", back_populates="risk_scores")

class AlertRecord(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.patient_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    severity = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    risk_score_id = Column(Integer, ForeignKey("risk_scores.id"))
    recommended_actions = Column(JSON)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String)
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship("PatientRecord", back_populates="alerts")

class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://ews_user:password@localhost:5432/patient_ews"
            )
        
        self.engine = create_engine(
            database_url,
            poolclass=NullPool,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
        
    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")
        
    def get_session(self) -> Session:
        return self.SessionLocal()
        
    def save_patient(self, session: Session, patient_data: dict):
        patient = PatientRecord(**patient_data)
        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient
        
    def save_vital_signs(self, session: Session, vitals_data: dict):
        vitals = VitalSignRecord(**vitals_data)
        session.add(vitals)
        session.commit()
        session.refresh(vitals)
        return vitals
        
    def save_risk_score(self, session: Session, risk_data: dict):
        risk_score = RiskScoreRecord(**risk_data)
        session.add(risk_score)
        session.commit()
        session.refresh(risk_score)
        return risk_score
        
    def save_alert(self, session: Session, alert_data: dict):
        alert = AlertRecord(**alert_data)
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert
        
    def get_patient_by_id(self, session: Session, patient_id: str):
        return session.query(PatientRecord).filter_by(patient_id=patient_id).first()
        
    def get_recent_vitals(self, session: Session, patient_id: str, hours: int = 24):
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return session.query(VitalSignRecord).filter(
            VitalSignRecord.patient_id == patient_id,
            VitalSignRecord.timestamp >= cutoff_time
        ).order_by(VitalSignRecord.timestamp.desc()).all()
        
    def get_active_alerts(self, session: Session, patient_id: Optional[str] = None):
        query = session.query(AlertRecord).filter_by(is_acknowledged=False)
        
        if patient_id:
            query = query.filter_by(patient_id=patient_id)
            
        return query.order_by(AlertRecord.timestamp.desc()).all()