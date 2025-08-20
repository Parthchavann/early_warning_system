#!/usr/bin/env python3
"""
Add test data to the patient monitoring system
"""
import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8080"

# Test patients with different risk levels
test_patients = [
    {
        "patient_id": "P001",
        "name": "John Smith",
        "age": 65,
        "gender": "Male", 
        "room": "ICU-101",
        "admission_date": "2025-08-20T10:00:00Z",
        "vitals": {
            "heart_rate": 85,
            "blood_pressure_systolic": 125,
            "blood_pressure_diastolic": 82,
            "respiratory_rate": 16,
            "temperature": 37.1,
            "oxygen_saturation": 97
        }
    },
    {
        "patient_id": "P002", 
        "name": "Mary Johnson",
        "age": 72,
        "gender": "Female",
        "room": "Ward-205",
        "admission_date": "2025-08-20T08:30:00Z",
        "vitals": {
            "heart_rate": 110,
            "blood_pressure_systolic": 155,
            "blood_pressure_diastolic": 95,
            "respiratory_rate": 22,
            "temperature": 38.2,
            "oxygen_saturation": 92
        }
    },
    {
        "patient_id": "P003",
        "name": "Robert Davis", 
        "age": 58,
        "gender": "Male",
        "room": "ICU-103",
        "admission_date": "2025-08-20T12:15:00Z",
        "vitals": {
            "heart_rate": 145,
            "blood_pressure_systolic": 210,
            "blood_pressure_diastolic": 115,
            "respiratory_rate": 32,
            "temperature": 39.8,
            "oxygen_saturation": 85
        }
    },
    {
        "patient_id": "P004",
        "name": "Susan Wilson",
        "age": 45,
        "gender": "Female", 
        "room": "Ward-301",
        "admission_date": "2025-08-20T14:00:00Z",
        "vitals": {
            "heart_rate": 75,
            "blood_pressure_systolic": 118,
            "blood_pressure_diastolic": 78,
            "respiratory_rate": 14,
            "temperature": 36.8,
            "oxygen_saturation": 99
        }
    }
]

def add_patient(patient_data):
    """Add a patient to the system"""
    try:
        # Extract vitals from patient data
        vitals = patient_data.pop('vitals')
        
        # Create patient
        response = requests.post(f"{BASE_URL}/patients", json=patient_data, timeout=10)
        print(f"Creating patient {patient_data['name']}: {response.status_code}")
        
        if response.status_code == 200:
            # Add vitals
            vitals_response = requests.post(
                f"{BASE_URL}/patients/{patient_data['patient_id']}/vitals", 
                json=vitals, 
                timeout=10
            )
            print(f"Adding vitals for {patient_data['name']}: {vitals_response.status_code}")
            
            if vitals_response.status_code == 200:
                vitals_result = vitals_response.json()
                print(f"Risk score for {patient_data['name']}: {vitals_result.get('risk_score', 'N/A')}")
                
            # Get risk prediction
            try:
                predict_response = requests.post(
                    f"{BASE_URL}/patients/{patient_data['patient_id']}/predict",
                    timeout=10
                )
                if predict_response.status_code == 200:
                    prediction = predict_response.json()
                    print(f"Prediction for {patient_data['name']}: Risk {prediction['risk_score']['overall_risk']:.2f}")
                    print(f"Alerts: {len(prediction.get('alerts', []))}")
            except Exception as e:
                print(f"Prediction failed for {patient_data['name']}: {e}")
        
        print("-" * 50)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error adding patient {patient_data.get('name', 'Unknown')}: {e}")
        return False

def main():
    print("Adding test data to Patient Monitoring System...")
    print("=" * 50)
    
    success_count = 0
    for patient in test_patients:
        if add_patient(patient.copy()):
            success_count += 1
        time.sleep(1)  # Small delay between requests
    
    print(f"\nSummary: {success_count}/{len(test_patients)} patients added successfully")
    
    # Check final stats
    try:
        stats_response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"Total patients: {stats['total_patients']}")
            print(f"High risk patients: {stats['high_risk_patients']}")
            print(f"Active alerts: {stats['active_alerts']}")
    except Exception as e:
        print(f"Error getting stats: {e}")

if __name__ == "__main__":
    main()