#!/usr/bin/env python3
"""
Test script to create critical vital signs and trigger alert
"""
import requests
import json
import time

# API base URL
API_BASE = "http://localhost:8080"

def add_critical_vitals(patient_id):
    """Add critical vital signs that should trigger an alert"""
    
    # Critical vital signs - multiple risk factors
    critical_vitals = {
        "heart_rate": 140,  # High (>120 = 2 risk factors)
        "blood_pressure_systolic": 200,  # High (>180 = 2 risk factors) 
        "blood_pressure_diastolic": 90,
        "respiratory_rate": 35,  # High (>30 = 2 risk factors)
        "temperature": 39.5,  # High (>39 = 2 risk factors)
        "oxygen_saturation": 85,  # Low (<88 = 3 risk factors)
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    try:
        print(f"🔥 Adding CRITICAL vitals for patient {patient_id}")
        print("Vitals:", json.dumps(critical_vitals, indent=2))
        
        response = requests.post(
            f"{API_BASE}/patients/{patient_id}/vitals",
            json=critical_vitals,
            headers={"Content-Type": "application/json"}
        )
        
        if response.ok:
            result = response.json()
            print(f"✅ Critical vitals added successfully!")
            print(f"Risk Score: {result.get('risk_score', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to add vitals: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error adding vitals: {e}")
        return False

def check_alerts():
    """Check current active alerts"""
    try:
        response = requests.get(f"{API_BASE}/alerts/active")
        if response.ok:
            data = response.json()
            alerts = data.get('alerts', [])
            print(f"\n🔔 Current Active Alerts: {len(alerts)}")
            
            critical_count = 0
            for alert in alerts:
                severity = alert.get('severity', 'unknown')
                patient = alert.get('patient_name', alert.get('patient_id', 'Unknown'))
                risk = alert.get('risk_score', 0)
                timestamp = alert.get('timestamp', 'Unknown')
                
                if severity == 'critical':
                    critical_count += 1
                    print(f"🚨 CRITICAL: {patient} (Risk: {risk}) - {timestamp}")
                else:
                    print(f"⚠️  {severity.upper()}: {patient} (Risk: {risk}) - {timestamp}")
            
            print(f"\n📊 Summary: {critical_count} critical alerts out of {len(alerts)} total")
            return alerts
        else:
            print(f"❌ Failed to get alerts: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error getting alerts: {e}")
        return []

def main():
    print("🧪 Testing Critical Alert Generation")
    print("="*50)
    
    # First check existing alerts
    print("1️⃣ Checking existing alerts...")
    existing_alerts = check_alerts()
    
    # Add critical vitals to a patient
    print("\n2️⃣ Adding critical vitals to trigger new alert...")
    patient_id = "P20250812182229783"  # Parth Chavan
    success = add_critical_vitals(patient_id)
    
    if success:
        print("\n3️⃣ Waiting 2 seconds for alert processing...")
        time.sleep(2)
        
        print("\n4️⃣ Checking alerts after adding critical vitals...")
        new_alerts = check_alerts()
        
        # Compare
        if len(new_alerts) > len(existing_alerts):
            print(f"\n✅ SUCCESS: New alert generated! ({len(new_alerts) - len(existing_alerts)} new alerts)")
        else:
            print(f"\n⚠️  No new alerts generated. Alert might already exist or threshold not met.")
    else:
        print("\n❌ Failed to add critical vitals")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()