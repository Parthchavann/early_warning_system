#!/usr/bin/env python3
"""
Test AlertContext API call to identify potential issues
"""
import requests
import json

def test_alert_api():
    """Test the alert API that AlertContext calls"""
    try:
        print("🧪 Testing AlertContext API call...")
        print("="*50)
        
        # Test the exact call AlertContext makes
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:3000',  # Simulate frontend origin
        }
        
        response = requests.get(
            'http://localhost:8080/alerts/active',
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📦 Response Headers: {dict(response.headers)}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Response received successfully")
            print(f"📊 Raw response structure:")
            print(f"   - Type: {type(data)}")
            print(f"   - Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Check alerts array
            alerts = data.get('alerts', [])
            print(f"   - Alerts count: {len(alerts)}")
            
            if alerts:
                print(f"\n🔍 Alert details:")
                for i, alert in enumerate(alerts):
                    print(f"   Alert {i+1}:")
                    print(f"     - alert_id: {alert.get('alert_id', 'MISSING')}")
                    print(f"     - patient_name: {alert.get('patient_name', 'MISSING')}")
                    print(f"     - severity: {alert.get('severity', 'MISSING')}")
                    print(f"     - risk_score: {alert.get('risk_score', 'MISSING')}")
                    print(f"     - timestamp: {alert.get('timestamp', 'MISSING')}")
                
                # Simulate AlertContext processing
                print(f"\n🔄 Simulating AlertContext processing...")
                processed_alerts = []
                
                for alert in alerts:
                    processed = {
                        **alert,
                        'id': alert.get('alert_id') or alert.get('id'),
                        'is_acknowledged': alert.get('is_acknowledged') or alert.get('acknowledged') or False
                    }
                    processed_alerts.append(processed)
                
                # Filter like AlertContext does
                active_alerts = [a for a in processed_alerts if not a.get('is_acknowledged')]
                critical_alerts = [a for a in processed_alerts if 
                    a.get('severity') == 'critical' or (a.get('risk_score', 0) >= 0.8)]
                
                print(f"   ✅ Processed alerts: {len(processed_alerts)}")
                print(f"   🔥 Active alerts: {len(active_alerts)}")
                print(f"   🚨 Critical alerts: {len(critical_alerts)}")
                
                print(f"\n🎯 What Dashboard should receive:")
                print(f"   - activeAlerts array with {len(active_alerts)} items")
                if active_alerts:
                    print(f"   - First alert: {active_alerts[0].get('patient_name')} (ID: {active_alerts[0].get('id')})")
                
            else:
                print("❌ No alerts found in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server not running on localhost:8080")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: API call took too long")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_cors():
    """Test CORS headers specifically"""
    try:
        print(f"\n🌐 Testing CORS headers...")
        
        # Test OPTIONS preflight request
        response = requests.options(
            'http://localhost:8080/alerts/active',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        
        print(f"OPTIONS Status: {response.status_code}")
        cors_headers = {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
        print(f"CORS Headers: {cors_headers}")
        
        if 'Access-Control-Allow-Origin' in response.headers:
            allowed_origin = response.headers['Access-Control-Allow-Origin']
            print(f"✅ CORS Allow Origin: {allowed_origin}")
            if allowed_origin == 'http://localhost:3000' or allowed_origin == '*':
                print("✅ CORS properly configured for frontend")
            else:
                print(f"❌ CORS may be blocking frontend (expected http://localhost:3000, got {allowed_origin})")
        else:
            print("❌ No CORS headers found - this could block frontend requests")
            
    except Exception as e:
        print(f"❌ CORS test error: {e}")

if __name__ == "__main__":
    test_alert_api()
    test_cors()
    print("\n🏁 Alert API test completed!")