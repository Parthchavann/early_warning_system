#!/usr/bin/env python3
"""
Debug script to check risk_score values and identify NaN issue
"""
import sqlite3
import json

# Connect to database
conn = sqlite3.connect('patient_ews.db')
cursor = conn.cursor()

print("=== DEBUG: RISK SCORE INVESTIGATION ===")
print()

# Check patient data
print("1. PATIENT DATA:")
cursor.execute("SELECT patient_id, age, gender FROM patients LIMIT 5")
patients = cursor.fetchall()
for p in patients:
    print(f"  Patient: {p[0]}, Age: {p[1]}, Gender: {p[2]}")

print()

# Check vital signs data  
print("2. VITAL SIGNS DATA:")
cursor.execute("""
    SELECT patient_id, heart_rate, blood_pressure_systolic, 
           respiratory_rate, temperature, oxygen_saturation 
    FROM vital_signs 
    LIMIT 5
""")
vitals = cursor.fetchall()
for v in vitals:
    print(f"  Patient: {v[0]}")
    print(f"    HR: {v[1]}, BP: {v[2]}, RR: {v[3]}, Temp: {v[4]}, O2: {v[5]}")

print()

# Test risk calculation
def fallback_risk_calculation(vitals_data):
    if not vitals_data:
        return 0.1
        
    risk_factors = 0
    
    # Heart rate check
    hr = vitals_data.get('heart_rate')
    if hr is not None and (hr < 50 or hr > 120):
        risk_factors += 1
    
    # Blood pressure check
    bp_sys = vitals_data.get('blood_pressure_systolic')
    if bp_sys is not None and (bp_sys < 90 or bp_sys > 160):
        risk_factors += 1
    
    # Respiratory rate check
    rr = vitals_data.get('respiratory_rate')
    if rr is not None and (rr < 10 or rr > 24):
        risk_factors += 1
    
    # Temperature check
    temp = vitals_data.get('temperature')
    if temp is not None and (temp < 36 or temp > 38.5):
        risk_factors += 1
    
    # Oxygen saturation check
    spo2 = vitals_data.get('oxygen_saturation')
    if spo2 is not None and spo2 < 94:
        risk_factors += 1
    
    # Calculate final risk score
    final_risk = min(0.9, risk_factors * 0.2 + 0.1)
    
    return final_risk

print("3. RISK SCORE CALCULATION TEST:")
cursor.execute("""
    SELECT p.patient_id, 
           v.heart_rate, v.blood_pressure_systolic, v.blood_pressure_diastolic,
           v.respiratory_rate, v.temperature, v.oxygen_saturation
    FROM patients p
    LEFT JOIN vital_signs v ON p.patient_id = v.patient_id
    LIMIT 5
""")

patients_with_vitals = cursor.fetchall()
for row in patients_with_vitals:
    patient_id = row[0]
    
    vitals = None
    if row[1] is not None:  # has vital signs
        vitals = {
            'heart_rate': row[1],
            'blood_pressure_systolic': row[2], 
            'blood_pressure_diastolic': row[3],
            'respiratory_rate': row[4],
            'temperature': row[5],
            'oxygen_saturation': row[6]
        }
    
    risk_score = fallback_risk_calculation(vitals)
    
    print(f"  Patient: {patient_id}")
    print(f"    Vitals: {vitals}")
    print(f"    Risk Score: {risk_score} ({type(risk_score).__name__})")
    print(f"    JSON: {json.dumps(risk_score)}")
    print()

# Check for any NULL/None values that could cause NaN
print("4. CHECKING FOR NULL VALUES:")
cursor.execute("""
    SELECT COUNT(*) as total_patients,
           COUNT(CASE WHEN age IS NULL THEN 1 END) as null_age,
           COUNT(CASE WHEN gender IS NULL THEN 1 END) as null_gender
    FROM patients
""")
null_check = cursor.fetchone()
print(f"  Total patients: {null_check[0]}")
print(f"  NULL ages: {null_check[1]}")  
print(f"  NULL genders: {null_check[2]}")

cursor.execute("""
    SELECT COUNT(*) as total_vitals,
           COUNT(CASE WHEN heart_rate IS NULL THEN 1 END) as null_hr,
           COUNT(CASE WHEN blood_pressure_systolic IS NULL THEN 1 END) as null_bp,
           COUNT(CASE WHEN temperature IS NULL THEN 1 END) as null_temp
    FROM vital_signs
""")
vitals_null_check = cursor.fetchone()
print(f"  Total vitals: {vitals_null_check[0]}")
print(f"  NULL heart_rate: {vitals_null_check[1]}")
print(f"  NULL blood_pressure: {vitals_null_check[2]}")
print(f"  NULL temperature: {vitals_null_check[3]}")

print()
print("=== END DEBUG ===")

conn.close()