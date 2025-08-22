#!/usr/bin/env python3
"""
Generate critical alerts for high-risk patients
"""
import requests
import json
import time

API_BASE = "http://localhost:8080"

def get_high_risk_patients():
    """Get patients with high risk scores"""
    try:
        response = requests.get(f"{API_BASE}/patients")
        if response.ok:
            data = response.json()
            patients = data.get('patients', [])
            # Find patients with risk > 0.6
            high_risk = [p for p in patients if p.get('risk_score', 0) > 0.6]
            return high_risk
        return []
    except Exception as e:
        print(f"Error getting patients: {e}")
        return []

def add_critical_vitals(patient_id, patient_name):
    """Add critical vital signs to trigger alert"""
    critical_vitals = {
        "heart_rate": 145,           # Critical (>120)
        "blood_pressure_systolic": 220,  # Critical (>180) 
        "blood_pressure_diastolic": 95,
        "respiratory_rate": 35,      # Critical (>30)
        "temperature": 39.8,         # Critical (>39)
        "oxygen_saturation": 82,     # Critical (<88)
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/patients/{patient_id}/vitals",
            json=critical_vitals,
            headers={"Content-Type": "application/json"}
        )
        
        if response.ok:
            result = response.json()
            risk_score = result.get('risk_score', 0)
            print(f"✅ Added critical vitals for {patient_name}")
            print(f"   Risk Score: {risk_score}")
            return True
        else:
            print(f"❌ Failed to add vitals for {patient_name}: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error adding vitals for {patient_name}: {e}")
        return False

def check_alerts_created():
    """Check if alerts were created"""
    try:
        response = requests.get(f"{API_BASE}/alerts/active")
        if response.ok:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"\n🔔 Current active alerts: {len(alerts)}")
            
            for i, alert in enumerate(alerts):
                patient = alert.get('patient_name', 'Unknown')
                severity = alert.get('severity', 'unknown')
                risk = alert.get('risk_score', 0)
                print(f"  {i+1}. {patient} - {severity.upper()} (Risk: {risk})")
            
            return len(alerts)
        return 0
    except Exception as e:
        print(f"Error checking alerts: {e}")
        return 0

def main():
    print("🚨 Generating Critical Alerts for Dashboard")
    print("=" * 50)
    
    # Get high-risk patients
    print("1️⃣ Finding high-risk patients...")
    high_risk_patients = get_high_risk_patients()
    
    if not high_risk_patients:
        print("No high-risk patients found. Adding critical vitals to first few patients...")
        # Get any patients if no high-risk ones
        try:
            response = requests.get(f"{API_BASE}/patients")
            if response.ok:
                data = response.json()
                patients = data.get('patients', [])
                high_risk_patients = patients[:3]  # Take first 3 patients
        except:
            pass
    
    if not high_risk_patients:
        print("❌ No patients found in system")
        return
    
    print(f"Found {len(high_risk_patients)} patients to create alerts for:")
    for patient in high_risk_patients:
        name = patient.get('name', 'Unknown')
        current_risk = patient.get('risk_score', 0)
        print(f"  - {name} (Current risk: {current_risk})")
    
    # Add critical vitals to trigger alerts
    print(f"\n2️⃣ Adding critical vitals to trigger alerts...")
    success_count = 0
    
    for patient in high_risk_patients:
        patient_id = patient.get('patient_id')
        patient_name = patient.get('name', f'Patient {patient_id}')
        
        if add_critical_vitals(patient_id, patient_name):
            success_count += 1
            time.sleep(1)  # Small delay between requests
    
    print(f"\n3️⃣ Successfully processed {success_count}/{len(high_risk_patients)} patients")
    
    # Wait a moment for alerts to be processed
    print("\n4️⃣ Waiting for alerts to be generated...")
    time.sleep(3)
    
    # Check results
    print("5️⃣ Checking generated alerts...")
    alert_count = check_alerts_created()
    
    if alert_count > 0:
        print(f"\n✅ SUCCESS! Generated {alert_count} critical alerts")
        print("🎯 Go to http://localhost:3000/dashboard to see them!")
        print("📱 The alerts should appear in the 'Active Alerts' section")
    else:
        print(f"\n⚠️ No alerts were generated. This might indicate:")
        print("   - Backend alert generation logic issue")
        print("   - Database connection problem")
        print("   - Risk score calculation not triggering alerts")
    
    print(f"\n🏁 Alert generation completed!")

if __name__ == "__main__":
    main()