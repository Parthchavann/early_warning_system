#!/usr/bin/env python3
"""
Debug database content
"""
import sqlite3
import json

DB_PATH = 'patient_ews.db'

def check_database():
    """Check database content"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conn.cursor()
        
        # Check patients table
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        print(f"Total patients in DB: {patient_count}")
        
        if patient_count > 0:
            cursor.execute("SELECT * FROM patients")
            patients = cursor.fetchall()
            print("\nPatients in database:")
            for patient in patients:
                print(f"  - {patient}")
        
        # Check vitals
        cursor.execute("SELECT COUNT(*) FROM vital_signs")
        vitals_count = cursor.fetchone()[0]
        print(f"\nTotal vital signs records: {vitals_count}")
        
        if vitals_count > 0:
            cursor.execute("SELECT patient_id, COUNT(*) FROM vital_signs GROUP BY patient_id")
            vitals_by_patient = cursor.fetchall()
            print("\nVital signs by patient:")
            for patient_id, count in vitals_by_patient:
                print(f"  - {patient_id}: {count} records")
        
        # Check alerts
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alerts_count = cursor.fetchone()[0]
        print(f"\nTotal alerts: {alerts_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_database()