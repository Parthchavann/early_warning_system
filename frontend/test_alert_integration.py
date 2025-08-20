#!/usr/bin/env python3
"""
Test full alert integration from backend to frontend expectations
"""
import requests
import json

def test_full_integration():
    print("🧪 Testing Full Alert Integration")
    print("="*60)
    
    # Step 1: Test backend API
    print("1️⃣ Testing Backend API...")
    try:
        response = requests.get('http://localhost:8080/alerts/active')
        if response.ok:
            backend_data = response.json()
            backend_alerts = backend_data.get('alerts', [])
            print(f"   ✅ Backend: {len(backend_alerts)} alerts")
            
            critical_count = sum(1 for a in backend_alerts if a.get('severity') == 'critical')
            print(f"   🚨 Critical: {critical_count}")
        else:
            print(f"   ❌ Backend API failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Backend error: {e}")
        return
    
    # Step 2: Simulate AlertContext processing
    print("\n2️⃣ Simulating AlertContext Processing...")
    try:
        # Exact same logic as AlertContext
        alertsData = []
        if backend_data and backend_data.get('alerts') and isinstance(backend_data['alerts'], list):
            alertsData = [
                {
                    **alert,
                    'id': alert.get('alert_id') or alert.get('id'),
                    'is_acknowledged': alert.get('is_acknowledged') or alert.get('acknowledged') or False
                }
                for alert in backend_data['alerts']
            ]
        
        # Filter like AlertContext
        activeAlerts = [alert for alert in alertsData if not alert.get('is_acknowledged')]
        criticalAlerts = [alert for alert in alertsData if 
            alert.get('severity') == 'critical' or (alert.get('risk_score', 0) >= 0.8)]
        
        print(f"   ✅ Processed: {len(alertsData)} alerts")
        print(f"   🔥 Active: {len(activeAlerts)} alerts")
        print(f"   🚨 Critical: {len(criticalAlerts)} alerts")
        
        # Step 3: Check what Dashboard should receive
        print("\n3️⃣ Dashboard Should Receive...")
        print(f"   activeAlerts.length = {len(activeAlerts)}")
        
        if len(activeAlerts) > 0:
            print("   ✅ Dashboard condition: activeAlerts.length > 0 = TRUE")
            print("   📋 Dashboard should render:")
            for i, alert in enumerate(activeAlerts[:3]):  # Show first 3
                patient = alert.get('patient_name', 'Unknown')
                severity = alert.get('severity', 'unknown')
                risk = alert.get('risk_score', 0)
                print(f"      Alert {i+1}: {patient} ({severity}, risk: {risk})")
        else:
            print("   ❌ Dashboard condition: activeAlerts.length > 0 = FALSE")
            print("   📋 Dashboard would show: 'No active alerts'")
        
        # Step 4: Check for potential issues
        print("\n4️⃣ Potential Issues Check...")
        
        # Check acknowledged status
        acknowledged_alerts = [a for a in alertsData if a.get('is_acknowledged')]
        if acknowledged_alerts:
            print(f"   ⚠️  Found {len(acknowledged_alerts)} acknowledged alerts (filtered out)")
        
        # Check data structure
        for alert in alertsData[:2]:  # Check first 2 alerts
            required_fields = ['id', 'patient_name', 'severity', 'message', 'risk_score']
            missing_fields = [field for field in required_fields if not alert.get(field)]
            if missing_fields:
                print(f"   ⚠️  Alert missing fields: {missing_fields}")
        
        # Step 5: Render test
        print("\n5️⃣ Render Test...")
        if len(activeAlerts) > 0:
            print("   🎯 Dashboard SHOULD show alerts!")
            print("   📱 Expected UI: Red alert cards with patient details")
        else:
            print("   🚫 Dashboard will show 'No active alerts' message")
            print("   🔍 This might be why you don't see critical alerts")
        
        # Final summary
        print(f"\n📊 SUMMARY:")
        print(f"   Backend alerts: {len(backend_alerts)}")
        print(f"   Active alerts for Dashboard: {len(activeAlerts)}")
        print(f"   Critical alerts: {len(criticalAlerts)}")
        
        if len(activeAlerts) != len(backend_alerts):
            print(f"   ⚠️  Mismatch detected! Backend has {len(backend_alerts)} but Dashboard gets {len(activeAlerts)}")
        
    except Exception as e:
        print(f"   ❌ Processing error: {e}")

if __name__ == "__main__":
    test_full_integration()