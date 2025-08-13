#!/usr/bin/env python3
"""
Check what actual data exists in the database vs what API returns
"""
import sqlite3
import json

print("=== CHECKING YOUR REAL DATA ===")

# Connect to database
conn = sqlite3.connect('patient_ews.db')
cursor = conn.cursor()

print("\n1. ALL PATIENTS IN DATABASE:")
cursor.execute("SELECT patient_id, mrn, age, gender, primary_diagnosis, created_at FROM patients ORDER BY created_at DESC")
all_patients = cursor.fetchall()

for i, p in enumerate(all_patients, 1):
    print(f"  {i}. ID: {p[0]}")
    print(f"     MRN: {p[1]}")
    print(f"     Age: {p[2]}, Gender: {p[3]}")
    print(f"     Diagnosis: {p[4]}")
    print(f"     Created: {p[5]}")
    print()

print(f"TOTAL PATIENTS: {len(all_patients)}")

print("\n2. CHECKING FOR YOUR MANUALLY ADDED DATA:")
# Look for recent patients (likely your additions)
cursor.execute("""
    SELECT patient_id, mrn, age, gender, primary_diagnosis, created_at 
    FROM patients 
    WHERE created_at >= date('2025-08-10')
    ORDER BY created_at DESC
""")
recent_patients = cursor.fetchall()

print("Recent patients (added today):")
for p in recent_patients:
    print(f"  - {p[0]}: {p[4]} (Age {p[2]}, {p[3]})")

print("\n3. VITAL SIGNS DATA:")
cursor.execute("""
    SELECT patient_id, timestamp, heart_rate, blood_pressure_systolic, temperature, oxygen_saturation
    FROM vital_signs 
    ORDER BY timestamp DESC 
    LIMIT 10
""")
recent_vitals = cursor.fetchall()

print("Recent vital signs:")
for v in recent_vitals:
    print(f"  - {v[0]}: HR={v[2]}, BP={v[3]}, Temp={v[4]}, O2={v[5]} at {v[1]}")

print("\n4. CHECKING FOR MOCK/SAMPLE DATA:")
# Look for patterns that suggest mock data
cursor.execute("SELECT patient_id FROM patients WHERE patient_id LIKE 'PATIENT_%' AND length(patient_id) <= 11")
mock_patients = cursor.fetchall()
print(f"Potential mock patients: {len(mock_patients)}")
for mp in mock_patients:
    print(f"  - {mp[0]}")

cursor.execute("SELECT patient_id FROM patients WHERE patient_id LIKE 'P2025%'")
real_patients = cursor.fetchall()  
print(f"Real patients (P2025 format): {len(real_patients)}")
for rp in real_patients:
    print(f"  - {rp[0]}")

conn.close()
print("\n=== END DATA CHECK ===")