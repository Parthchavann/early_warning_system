#!/usr/bin/env python3
"""
Add patient names to existing patients and update schema
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('patient_ews.db')
cursor = conn.cursor()

print("=== ADDING PATIENT NAMES TO SYSTEM ===")

# Check if name column exists
try:
    cursor.execute("SELECT name FROM patients LIMIT 1")
    print("✅ Patient name column already exists")
except sqlite3.OperationalError:
    print("➕ Adding patient name column...")
    cursor.execute("ALTER TABLE patients ADD COLUMN name TEXT")
    conn.commit()
    print("✅ Patient name column added")

# Add names to existing patients that don't have them
patient_names = {
    'P20250810191419474': 'Sarah Johnson',
    'P20250810191611368': 'Michael Chen', 
    'PATIENT_000': 'John Smith',
    'PATIENT_002': 'Emily Davis',
    'PATIENT_003': 'Robert Wilson',
    'PATIENT_007': 'Maria Garcia',
    'PATIENT_009': 'David Miller',
    'PATIENT_100': 'Jennifer Brown',
    'TEST_002': 'Test Patient Alpha'
}

print("\n📝 Assigning names to patients:")
for patient_id, name in patient_names.items():
    cursor.execute("UPDATE patients SET name = ? WHERE patient_id = ? AND (name IS NULL OR name = '')", 
                   (name, patient_id))
    if cursor.rowcount > 0:
        print(f"  ✅ {patient_id} → {name}")

# Add names to any new patients without names
cursor.execute("SELECT patient_id FROM patients WHERE name IS NULL OR name = ''")
unnamed_patients = cursor.fetchall()

for i, (patient_id,) in enumerate(unnamed_patients):
    if patient_id not in patient_names:
        default_name = f"Patient {chr(65 + (i % 26))}{(i // 26) + 1}"  # Patient A1, B1, etc.
        cursor.execute("UPDATE patients SET name = ? WHERE patient_id = ?", (default_name, patient_id))
        print(f"  ✅ {patient_id} → {default_name}")

conn.commit()

# Verify all patients have names
print("\n🔍 Verification - All patients with names:")
cursor.execute("SELECT patient_id, name, age, gender FROM patients ORDER BY CASE WHEN patient_id LIKE 'P2025%' THEN 1 ELSE 2 END, patient_id")
all_patients = cursor.fetchall()

for patient in all_patients:
    print(f"  {patient[0]}: {patient[1]} ({patient[2]}yr {patient[3]})")

conn.close()
print(f"\n✅ Total patients with names: {len(all_patients)}")
print("=== PATIENT NAMES SETUP COMPLETE ===")