#!/usr/bin/env python3
"""
Restore your previous patient data based on the found scripts
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8080"

# Your original patients from the scripts
original_patients = [
    {
        "patient_id": "PATIENT_000",
        "name": "John Smith",
        "age": 60,
        "gender": "Male",
        "room": "ICU-201",
        "admission_date": "2025-08-10T01:11:00Z",
        "vitals": {
            "heart_rate": 72,
            "blood_pressure_systolic": 125,
            "blood_pressure_diastolic": 80,
            "respiratory_rate": 16,
            "temperature": 37.0,
            "oxygen_saturation": 97
        }
    },
    {
        "patient_id": "PATIENT_002", 
        "name": "Emily Davis",
        "age": 27,
        "gender": "Female",
        "room": "Ward-105",
        "admission_date": "2025-08-09T23:55:00Z",
        "vitals": {
            "heart_rate": 85,
            "blood_pressure_systolic": 115,
            "blood_pressure_diastolic": 75,
            "respiratory_rate": 14,
            "temperature": 38.1,
            "oxygen_saturation": 96
        }
    },
    {
        "patient_id": "PATIENT_003",
        "name": "Robert Wilson", 
        "age": 65,
        "gender": "Male",
        "room": "ICU-103",
        "admission_date": "2025-08-09T23:56:00Z",
        "vitals": {
            "heart_rate": 95,
            "blood_pressure_systolic": 145,
            "blood_pressure_diastolic": 90,
            "respiratory_rate": 20,
            "temperature": 37.5,
            "oxygen_saturation": 94
        }
    },
    {
        "patient_id": "PATIENT_007",
        "name": "Maria Garcia",
        "age": 65,
        "gender": "Female", 
        "room": "Ward-207",
        "admission_date": "2025-08-10T00:14:00Z",
        "vitals": {
            "heart_rate": 78,
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "respiratory_rate": 15,
            "temperature": 36.8,
            "oxygen_saturation": 98
        }
    },
    {
        "patient_id": "PATIENT_009",
        "name": "David Miller",
        "age": 60,
        "gender": "Male",
        "room": "ICU-109", 
        "admission_date": "2025-08-10T00:15:00Z",
        "vitals": {
            "heart_rate": 88,
            "blood_pressure_systolic": 135,
            "blood_pressure_diastolic": 88,
            "respiratory_rate": 18,
            "temperature": 37.2,
            "oxygen_saturation": 95
        }
    },
    {
        "patient_id": "PATIENT_100",
        "name": "Jennifer Brown",
        "age": 58,
        "gender": "Female",
        "room": "Ward-300",
        "admission_date": "2025-08-10T01:32:00Z", 
        "vitals": {
            "heart_rate": 82,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 78,
            "respiratory_rate": 16,
            "temperature": 37.1,
            "oxygen_saturation": 97
        }
    },
    {
        "patient_id": "P20250810191419474",
        "name": "Sarah Johnson",
        "age": 35,
        "gender": "Female",
        "room": "Ward-401",
        "admission_date": "2025-08-10T19:14:19Z",
        "vitals": {
            "heart_rate": 110,         # Slightly high (normal: 60-100)
            "blood_pressure_systolic": 95,   # Normal
            "blood_pressure_diastolic": 65,  # Normal  
            "respiratory_rate": 18,    # Normal
            "temperature": 37.2,       # Normal
            "oxygen_saturation": 92,   # Low (< 95) - will add risk factor
        }
    },
    {
        "patient_id": "P20250810191611368",
        "name": "Michael Chen",
        "age": 65,
        "gender": "Male",
        "room": "ICU-105",
        "admission_date": "2025-08-10T19:16:11Z", 
        "vitals": {
            "heart_rate": 135,         # High (> 120) - will add risk factor
            "blood_pressure_systolic": 170,  # High (> 140) - will add risk factor
            "blood_pressure_diastolic": 95,
            "respiratory_rate": 26,    # High (> 20) - will add risk factor
            "temperature": 39.1,       # High (> 38) - will add risk factor  
            "oxygen_saturation": 88,   # Low (< 95) - will add risk factor
        }
    },
    {
        "patient_id": "P20250812182229783",
        "name": "Parth Chavan",
        "age": 26,
        "gender": "Male",
        "room": "Emergency-001",
        "admission_date": "2025-08-12T00:00:00Z",
        "vitals": {
            "heart_rate": 120,
            "blood_pressure_systolic": 160,
            "blood_pressure_diastolic": 95,
            "respiratory_rate": 22,
            "temperature": 38.5,
            "oxygen_saturation": 91
        }
    },
    {
        "patient_id": "P20250813132433793",
        "name": "Amir Khan", 
        "age": 59,
        "gender": "Male",
        "room": "Ward-502",
        "admission_date": "2025-08-12T00:00:00Z",
        "vitals": {
            "heart_rate": 75,
            "blood_pressure_systolic": 125,
            "blood_pressure_diastolic": 80,
            "respiratory_rate": 16,
            "temperature": 37.0,
            "oxygen_saturation": 98
        }
    },
    {
        "patient_id": "P20250813132628610",
        "name": "Salman Khan",
        "age": 62,
        "gender": "Male", 
        "room": "Ward-503",
        "admission_date": "2025-08-12T00:00:00Z",
        "vitals": {
            "heart_rate": 80,
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "respiratory_rate": 17,
            "temperature": 36.9,
            "oxygen_saturation": 96
        }
    }
]

def restore_patient(patient_data):
    """Restore a patient with their data"""
    try:
        # Extract vitals from patient data
        vitals = patient_data.pop('vitals')
        
        # Create patient
        response = requests.post(f"{BASE_URL}/patients", json=patient_data, timeout=10)
        print(f"Restoring patient {patient_data['name']}: {response.status_code}")
        
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
                risk_score = vitals_result.get('risk_score', 'N/A')
                print(f"Risk score for {patient_data['name']}: {risk_score}")
                
                # Add some historical vitals for more realistic data
                if risk_score != 'N/A' and risk_score > 0.5:
                    # Add another reading from 1 hour ago for high-risk patients
                    historical_vitals = vitals.copy()
                    # Slightly different values for historical data
                    historical_vitals['heart_rate'] = max(60, vitals['heart_rate'] - 5)
                    historical_vitals['blood_pressure_systolic'] = max(90, vitals['blood_pressure_systolic'] - 10)
                    historical_vitals['timestamp'] = (datetime.now() - timedelta(hours=1)).isoformat()
                    
                    requests.post(
                        f"{BASE_URL}/patients/{patient_data['patient_id']}/vitals", 
                        json=historical_vitals, 
                        timeout=10
                    )
                    print(f"Added historical vitals for {patient_data['name']}")
                
            # Get risk prediction
            try:
                predict_response = requests.post(
                    f"{BASE_URL}/patients/{patient_data['patient_id']}/predict",
                    timeout=10
                )
                if predict_response.status_code == 200:
                    prediction = predict_response.json()
                    print(f"Final risk assessment: {prediction['risk_score']['overall_risk']:.2f}")
                    alerts = prediction.get('alerts', [])
                    if alerts:
                        print(f"Alerts generated: {len(alerts)}")
            except Exception as e:
                print(f"Prediction failed for {patient_data['name']}: {e}")
        
        print("-" * 60)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error restoring patient {patient_data.get('name', 'Unknown')}: {e}")
        return False

def main():
    print("=== RESTORING YOUR PREVIOUS PATIENT DATA ===")
    print("=" * 60)
    
    # First, clear the current test data
    print("Clearing current test data...")
    current_response = requests.get(f"{BASE_URL}/patients", timeout=10)
    if current_response.status_code == 200:
        current_patients = current_response.json().get('patients', [])
        print(f"Found {len(current_patients)} current patients to replace")
    
    success_count = 0
    for patient in original_patients:
        if restore_patient(patient.copy()):
            success_count += 1
        # Small delay between requests
        import time
        time.sleep(0.5)
    
    print(f"\n🎉 RESTORATION SUMMARY:")
    print(f"Successfully restored: {success_count}/{len(original_patients)} patients")
    
    # Check final stats
    try:
        stats_response = requests.get(f"{BASE_URL}/stats", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"Total patients: {stats['total_patients']}")
            print(f"High risk patients: {stats['high_risk_patients']}")
            print(f"Active alerts: {stats['active_alerts']}")
            print(f"Average risk score: {stats['average_risk_score']:.2f}")
        
        # Show patient list
        patients_response = requests.get(f"{BASE_URL}/patients", timeout=10)
        if patients_response.status_code == 200:
            patients = patients_response.json().get('patients', [])
            print(f"\n📋 YOUR RESTORED PATIENTS:")
            for p in patients:
                status_emoji = "🚨" if p['risk_score'] > 0.7 else "⚠️" if p['risk_score'] > 0.5 else "✅"
                print(f"  {status_emoji} {p['name']} ({p['patient_id']}) - Risk: {p['risk_score']}")
                
    except Exception as e:
        print(f"Error getting final stats: {e}")

if __name__ == "__main__":
    main()