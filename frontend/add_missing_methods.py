#!/usr/bin/env python3
"""
Add missing alert methods to the backend
"""

missing_methods = '''
    def get_alert_history(self):
        """Get alert history from database"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Get all alerts with patient information
            query = """
                SELECT 
                    a.alert_id,
                    a.patient_id,
                    p.name as patient_name,
                    a.severity,
                    a.message,
                    a.risk_score,
                    a.timestamp,
                    a.acknowledged
                FROM alerts a
                LEFT JOIN patients p ON a.patient_id = p.patient_id
                ORDER BY a.timestamp DESC
                LIMIT 100
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append({
                    "alert_id": row[0],
                    "patient_id": row[1],
                    "patient_name": row[2] or "Unknown Patient",
                    "severity": row[3],
                    "message": row[4],
                    "risk_score": row[5],
                    "timestamp": row[6],
                    "acknowledged": bool(row[7])
                })
            
            conn.close()
            return {"alerts": alerts, "count": len(alerts)}
            
        except Exception as e:
            print(f"Database error in get_alert_history: {e}")
            return {"alerts": [], "count": 0}
    
    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Update alert as acknowledged
            cursor.execute("""
                UPDATE alerts 
                SET acknowledged = 1 
                WHERE alert_id = ?
            """, (alert_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {
                    "success": True,
                    "message": f"Alert {alert_id} acknowledged successfully"
                }
            else:
                conn.close()
                return {
                    "success": False,
                    "message": "Alert not found"
                }
            
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            return {"error": "Failed to acknowledge alert"}
    
    def dismiss_alert(self, alert_id):
        """Dismiss (delete) an alert"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Delete alert
            cursor.execute("""
                DELETE FROM alerts 
                WHERE alert_id = ?
            """, (alert_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {
                    "success": True,
                    "message": f"Alert {alert_id} dismissed successfully"
                }
            else:
                conn.close()
                return {
                    "success": False,
                    "message": "Alert not found"
                }
            
        except Exception as e:
            print(f"Error dismissing alert: {e}")
            return {"error": "Failed to dismiss alert"}

'''

# Read the current backend file
with open('backend_fixed_complete.py', 'r') as f:
    content = f.read()

# Find the location to insert the methods (before init_backend_db)
insert_position = content.find('def init_backend_db():')

if insert_position != -1:
    # Insert the missing methods
    new_content = content[:insert_position] + missing_methods + '\n' + content[insert_position:]
    
    # Write the updated content
    with open('backend_fixed_complete.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Missing alert methods added successfully!")
else:
    print("❌ Could not find insertion point in backend file")