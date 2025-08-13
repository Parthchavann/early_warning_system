#!/usr/bin/env python3
"""
Add sample vital signs to your real patients
"""
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8002"

# Your real patients
patients = [
    "P20250810191419474",  # 35F - Test Patient - Fixed Creation
    "P20250810191611368"   # 65M - Cold
]

# Sample vital signs that will create different risk scores
vitals_data = [
    {
        "patient_id": "P20250810191419474",
        "vitals": {
            "heart_rate": 110,         # Slightly high (normal: 60-100)
            "blood_pressure_systolic": 95,   # Normal
            "blood_pressure_diastolic": 65,  # Normal  
            "respiratory_rate": 18,    # Normal
            "temperature": 37.2,       # Normal
            "oxygen_saturation": 92,   # Low (< 94) - will add 1 risk factor
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "patient_id": "P20250810191611368", 
        "vitals": {
            "heart_rate": 135,         # High (> 120) - will add 1 risk factor
            "blood_pressure_systolic": 170,  # High (> 160) - will add 1 risk factor
            "blood_pressure_diastolic": 95,
            "respiratory_rate": 26,    # High (> 24) - will add 1 risk factor
            "temperature": 39.1,       # High (> 38.5) - will add 1 risk factor  
            "oxygen_saturation": 88,   # Low (< 94) - will add 1 risk factor
            "timestamp": datetime.now().isoformat()
        }
    }
]

print("=== ADDING VITAL SIGNS TO YOUR PATIENTS ===\n")

for data in vitals_data:
    patient_id = data["patient_id"]
    vitals = data["vitals"]
    
    print(f"📋 Adding vitals to {patient_id}:")
    print(f"   HR: {vitals['heart_rate']}, BP: {vitals['blood_pressure_systolic']}/{vitals['blood_pressure_diastolic']}")
    print(f"   RR: {vitals['respiratory_rate']}, Temp: {vitals['temperature']}, O2: {vitals['oxygen_saturation']}")
    
    try:
        response = requests.post(
            f"{API_URL}/patients/{patient_id}/vitals",
            json=vitals,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS: Vitals added")
            
            # Calculate expected risk score
            risk_factors = 0
            if vitals['heart_rate'] < 50 or vitals['heart_rate'] > 120:
                risk_factors += 1
            if vitals['blood_pressure_systolic'] < 90 or vitals['blood_pressure_systolic'] > 160:
                risk_factors += 1
            if vitals['respiratory_rate'] < 10 or vitals['respiratory_rate'] > 24:
                risk_factors += 1
            if vitals['temperature'] < 36 or vitals['temperature'] > 38.5:
                risk_factors += 1
            if vitals['oxygen_saturation'] < 94:
                risk_factors += 1
            
            expected_risk = round(min(0.9, risk_factors * 0.2 + 0.1), 1)
            print(f"   📊 Expected risk score: {expected_risk} ({risk_factors} risk factors)")
            
        else:
            print(f"   ❌ FAILED: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print()

print("=== Testing updated risk scores ===")
try:
    response = requests.get(f"{API_URL}/patients")
    if response.status_code == 200:
        patients_data = response.json()
        
        print("Updated patient list:")
        for p in patients_data[:4]:  # Show first 4
            print(f"  {p['patient_id']}: risk_score = {p['risk_score']}")
    else:
        print(f"Failed to get patients: {response.status_code}")
        
except Exception as e:
    print(f"Error getting patients: {e}")

print("\n=== DONE ===")