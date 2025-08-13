"""
Database initialization script
"""
import asyncio
import os
from sqlalchemy import create_engine, text

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ews_user:secure_password@localhost:5432/patient_ews")

def init_database():
    """Initialize the database with required tables and data"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Create patients table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS patients (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50) UNIQUE NOT NULL,
                    mrn VARCHAR(50) UNIQUE NOT NULL,
                    admission_date TIMESTAMP NOT NULL,
                    age INTEGER,
                    gender VARCHAR(1),
                    primary_diagnosis TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create vital_signs table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vital_signs (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50) REFERENCES patients(patient_id),
                    timestamp TIMESTAMP NOT NULL,
                    heart_rate INTEGER,
                    blood_pressure_systolic INTEGER,
                    blood_pressure_diastolic INTEGER,
                    respiratory_rate INTEGER,
                    temperature DECIMAL(4,2),
                    oxygen_saturation INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create alerts table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50) REFERENCES patients(patient_id),
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT,
                    risk_score DECIMAL(5,4),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by VARCHAR(100),
                    acknowledged_at TIMESTAMP
                );
            """))
            
            # Create predictions table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    patient_id VARCHAR(50) REFERENCES patients(patient_id),
                    prediction_timestamp TIMESTAMP NOT NULL,
                    overall_risk DECIMAL(5,4),
                    sepsis_risk DECIMAL(5,4),
                    cardiac_risk DECIMAL(5,4),
                    respiratory_risk DECIMAL(5,4),
                    confidence DECIMAL(5,4),
                    model_version VARCHAR(50),
                    features JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            conn.commit()
            print("Database tables created successfully!")
            
            # Insert sample data for testing
            conn.execute(text("""
                INSERT INTO patients (patient_id, mrn, admission_date, age, gender, primary_diagnosis)
                VALUES ('SAMPLE_001', 'MRN_000001', '2024-01-01 10:00:00', 65, 'M', 'Pneumonia')
                ON CONFLICT (patient_id) DO NOTHING;
            """))
            
            conn.execute(text("""
                INSERT INTO vital_signs (patient_id, timestamp, heart_rate, blood_pressure_systolic, 
                                       blood_pressure_diastolic, respiratory_rate, temperature, oxygen_saturation)
                VALUES ('SAMPLE_001', '2024-01-01 14:00:00', 85, 120, 80, 16, 36.5, 98)
                ON CONFLICT DO NOTHING;
            """))
            
            conn.commit()
            print("Sample data inserted successfully!")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_database()