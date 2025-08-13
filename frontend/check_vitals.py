#!/usr/bin/env python3
"""
Check vital signs for your real patients to see why risk scores are 0.1
"""
import sqlite3

print("=== CHECKING VITAL SIGNS FOR YOUR REAL PATIENTS ===")

conn = sqlite3.connect('patient_ews.db')
cursor = conn.cursor()

# Your real patients
real_patients = ['P20250810191419474', 'P20250810191611368']

for patient_id in real_patients:
    print(f"\n📋 PATIENT: {patient_id}")
    
    # Get patient info
    cursor.execute("SELECT age, gender, primary_diagnosis FROM patients WHERE patient_id = ?", (patient_id,))
    patient_info = cursor.fetchone()
    if patient_info:
        print(f"   Age: {patient_info[0]}, Gender: {patient_info[1]}, Diagnosis: {patient_info[2]}")
    
    # Check for vital signs
    cursor.execute("""
        SELECT timestamp, heart_rate, blood_pressure_systolic, blood_pressure_diastolic,
               respiratory_rate, temperature, oxygen_saturation
        FROM vital_signs 
        WHERE patient_id = ?
        ORDER BY timestamp DESC
    """, (patient_id,))
    
    vitals = cursor.fetchall()
    
    if vitals:
        print(f"   📊 VITAL SIGNS ({len(vitals)} records):")
        for i, v in enumerate(vitals, 1):
            print(f"      {i}. Time: {v[0]}")
            print(f"         HR: {v[1]}, BP: {v[2]}/{v[3]}, RR: {v[4]}, Temp: {v[5]}, O2: {v[6]}")
            
            # Calculate risk score manually
            risk_factors = 0
            if v[1] is not None and (v[1] < 50 or v[1] > 120):  # HR
                risk_factors += 1
            if v[2] is not None and (v[2] < 90 or v[2] > 160):  # BP systolic
                risk_factors += 1
            if v[4] is not None and (v[4] < 10 or v[4] > 24):   # RR
                risk_factors += 1
            if v[5] is not None and (v[5] < 36 or v[5] > 38.5): # Temp
                risk_factors += 1
            if v[6] is not None and v[6] < 94:                  # O2
                risk_factors += 1
            
            risk_score = round(min(0.9, risk_factors * 0.2 + 0.1), 1)
            print(f"         ⚠️ CALCULATED RISK: {risk_score} ({risk_factors} risk factors)")
    else:
        print("   ❌ NO VITAL SIGNS DATA FOUND")
        print("   ℹ️ This is why risk_score = 0.1 (default for no vitals)")

print("\n=== COMPARISON: Mock patients (for reference) ===")
cursor.execute("""
    SELECT patient_id, COUNT(*)
    FROM vital_signs 
    WHERE patient_id LIKE 'PATIENT_%'
    GROUP BY patient_id
""")
mock_vitals = cursor.fetchall()
for mv in mock_vitals:
    print(f"   {mv[0]}: {mv[1]} vital records")

conn.close()
print("\n=== END VITALS CHECK ===")