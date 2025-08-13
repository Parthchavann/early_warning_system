#!/usr/bin/env python3
"""
Fix for delete_alert function to handle auto-generated alerts properly
"""

def delete_alert_fixed(self, alert_id):
    """Delete/dismiss an alert - FIXED VERSION"""
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('patient_ews.db', timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        
        # Handle auto-generated alerts (ID starts with "auto_")
        if alert_id.startswith('auto_'):
            # Extract patient ID from auto-generated alert ID  
            patient_id = alert_id.replace('auto_', '')
            
            print(f"🔧 Handling auto-generated alert dismissal: {alert_id} for patient {patient_id}")
            
            # Create a dismissed alert record to prevent regeneration
            cursor.execute("""
                INSERT OR REPLACE INTO alerts (id, patient_id, severity, message, 
                                              is_acknowledged, acknowledged_at, created_at)
                VALUES (?, ?, 'critical', 'Auto-generated alert dismissed', 1, ?, ?)
            """, (
                alert_id,
                patient_id,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Successfully dismissed auto-generated alert: {alert_id}")
            return {"message": "Alert dismissed successfully", "alert_id": alert_id}
        
        # Handle regular database alerts
        cursor.execute("SELECT id FROM alerts WHERE id = ?", (alert_id,))
        if not cursor.fetchone():
            conn.close()
            return {"error": "Alert not found"}
        
        # Delete the regular alert
        cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully dismissed database alert: {alert_id}")
        return {"message": "Alert dismissed successfully", "alert_id": alert_id}
        
    except Exception as e:
        print(f"❌ Error dismissing alert: {e}")
        return {"error": f"Failed to dismiss alert: {str(e)}"}

if __name__ == "__main__":
    print("This is the fixed delete_alert function implementation.")
    print("The main fix is to detect auto-generated alerts (starting with 'auto_')")
    print("and create dismissed alert records instead of trying to delete non-existent database records.")