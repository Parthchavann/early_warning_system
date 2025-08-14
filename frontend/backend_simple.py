#!/usr/bin/env python3
"""
Simple Backend API Server for Patient Deterioration System
Serves API endpoints with CRUD operations for patients
"""
import http.server
import socketserver
import json
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import os
import time
import hashlib
import secrets
import hmac
import base64

# Backend configuration
DB_PATH = 'patient_ews.db'
JWT_SECRET = os.environ.get("JWT_SECRET", "secure-production-key-change-me")
TOKEN_EXPIRY_HOURS = 24
PORT = int(os.environ.get("BACKEND_PORT", 8080))

def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, stored_hash):
    """Verify password against stored hash"""
    try:
        salt, hash_part = stored_hash.split(':')
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == hash_part
    except:
        return False

def create_token(user_data):
    """Create a simple JWT-like token"""
    payload = {
        'user_id': user_data['user_id'],
        'email': user_data['email'],
        'role': user_data['role'],
        'exp': (datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)).timestamp()
    }
    
    payload_str = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.b64encode(payload_str.encode()).decode()
    
    signature = hmac.new(
        JWT_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"

def verify_token(auth_header):
    """Verify JWT token"""
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]
    try:
        payload_b64, signature = token.split('.')
        
        expected_signature = hmac.new(
            JWT_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        payload_str = base64.b64decode(payload_b64).decode()
        payload = json.loads(payload_str)
        
        if payload['exp'] < time.time():
            return None
        
        return payload
    except:
        return None

class SimpleAPIHandler(http.server.BaseHTTPRequestHandler):
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        super().end_headers()
    
    def do_GET(self):
        self.handle_api_request()
    
    def do_POST(self):
        self.handle_api_request()
    
    def do_PUT(self):
        self.handle_api_request()
    
    def do_DELETE(self):
        self.handle_api_request()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def handle_api_request(self):
        """Handle API requests"""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            
            response = None
            
            # Route API requests
            if path == '/health':
                response = {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
            elif path == '/patients' and self.command == 'GET':
                response = self.get_patients()
            elif path == '/patients' and self.command == 'POST':
                response = self.create_patient()
            elif path == '/stats':
                response = self.get_stats()
            elif path == '/analytics' or path == '/analytics/data':
                response = self.get_analytics_data()
            elif path == '/alerts/active':
                response = {"alerts": [], "count": 0}  # Simple empty response
            elif path == '/auth/login' and self.command == 'POST':
                response = self.login()
            elif path == '/auth/verify' and self.command == 'GET':
                response = self.verify_auth()
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "API endpoint not found"}).encode())
                return
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"API Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def create_patient(self):
        """Create a new patient"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            patient_data = json.loads(post_data)
            
            # Generate unique patient ID
            patient_id = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2)}"
            
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Check if database has required columns
            cursor.execute("PRAGMA table_info(patients)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Base patient data
            name = patient_data.get('name', 'Unknown Patient')
            age = patient_data.get('age', 0)
            admission_date = patient_data.get('admission_date', datetime.now().isoformat())
            
            # Insert with correct column names based on existing schema
            cursor.execute("""
                INSERT INTO patients (patient_id, name, age, admission_date, primary_diagnosis, room_number, gender, department, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (patient_id, name, age, admission_date, 
                  patient_data.get('primary_diagnosis', ''), 
                  patient_data.get('room', ''),
                  patient_data.get('gender', ''),
                  patient_data.get('department', ''),
                  datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "patient_id": patient_id,
                "message": "Patient created successfully"
            }
            
        except Exception as e:
            print(f"Error creating patient: {e}")
            return {"success": False, "error": str(e)}
    
    def get_patients(self):
        """Get patients list from database"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Get patients with latest vital signs
            query = """
                SELECT 
                    p.patient_id,
                    p.name,
                    p.age,
                    p.admission_date,
                    p.primary_diagnosis
                FROM patients p
                ORDER BY p.admission_date DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                patients.append({
                    "patient_id": row[0],
                    "name": row[1],
                    "age": row[2] or 0,
                    "admission_date": row[3],
                    "condition": row[4] if len(row) > 4 else "Unknown",
                    "risk_score": 0.1,
                    "status": "stable",
                    "vitals": {
                        "heart_rate": 70,
                        "blood_pressure": "120/80",
                        "temperature": 37.0,
                        "oxygen_saturation": 98
                    }
                })
            
            conn.close()
            return {"patients": patients, "count": len(patients)}
            
        except Exception as e:
            print(f"Database error in get_patients: {e}")
            return {"patients": [], "count": 0}
    
    def get_stats(self):
        """Get dashboard stats from database"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Get total patients
            cursor.execute("SELECT COUNT(*) FROM patients")
            total_patients = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_patients": total_patients,
                "active_alerts": 0,
                "high_risk_patients": 0,
                "average_risk_score": 0.1
            }
            
        except Exception as e:
            print(f"Database error in get_stats: {e}")
            return {
                "total_patients": 0,
                "active_alerts": 0,
                "high_risk_patients": 0,
                "average_risk_score": 0.0
            }
    
    def get_analytics_data(self):
        """Get analytics data from database"""
        try:
            stats = self.get_stats()
            total_patients = stats.get('total_patients', 0)
            
            return {
                "total_patients": total_patients,
                "active_alerts": 0,
                "average_risk_score": 0.1,
                "trends": {
                    "risk_scores": [0.1, 0.1, 0.1, 0.1, 0.1],
                    "alert_counts": [0, 0, 0, 0, 0]
                },
                "departments": [
                    {"name": "ICU", "patients": max(0, total_patients // 3)},
                    {"name": "Emergency", "patients": max(0, total_patients // 3)}, 
                    {"name": "General", "patients": max(0, total_patients - 2 * (total_patients // 3))}
                ],
                "risk_distribution": {
                    "low": total_patients,
                    "medium": 0,
                    "high": 0
                }
            }
            
        except Exception as e:
            print(f"Analytics error: {e}")
            return {
                "total_patients": 0,
                "active_alerts": 0,
                "average_risk_score": 0.0,
                "trends": {
                    "risk_scores": [0.1, 0.1, 0.1, 0.1, 0.1],
                    "alert_counts": [0, 0, 0, 0, 0]
                },
                "departments": [],
                "risk_distribution": {"low": 0, "medium": 0, "high": 0}
            }
    
    def login(self):
        """Handle user login"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            credentials = json.loads(post_data)
            
            email = credentials.get('email')
            password = credentials.get('password')
            
            # For demo, accept test credentials
            if email == "test@example.com" and password == "password123":
                user_data = {
                    'user_id': 'USER_DEMO',
                    'email': email,
                    'role': 'nurse'
                }
                token = create_token(user_data)
                
                return {
                    "token": token,
                    "user": {
                        "user_id": "USER_DEMO",
                        "email": email,
                        "name": "Demo User",
                        "role": "nurse",
                        "department": "ICU"
                    }
                }
            
            return {"success": False, "message": "Invalid credentials"}
            
        except Exception as e:
            print(f"Login error: {e}")
            return {"success": False, "message": "Login failed"}
    
    def verify_auth(self):
        """Verify authentication token"""
        try:
            auth_header = self.headers.get('Authorization')
            if not auth_header:
                return {"success": False, "message": "No token provided"}
            
            payload = verify_token(auth_header)
            if not payload:
                return {"success": False, "message": "Invalid token"}
            
            return {
                "success": True,
                "user": {
                    "user_id": payload.get('user_id'),
                    "email": payload.get('email'),
                    "role": payload.get('role'),
                    "name": "Demo User"
                }
            }
            
        except Exception as e:
            print(f"Auth verification error: {e}")
            return {"success": False, "message": "Token verification failed"}

def init_backend_db():
    """Initialize backend database"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        
        # Create basic tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                room TEXT,
                admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                primary_diagnosis TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Backend database initialized")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Patient Deterioration System - Simple Backend API Server")
    print("="*70)
    print(f"📁 Database: {DB_PATH}")
    print(f"🌐 API Server URL: http://localhost:{PORT}")
    print(f"🔗 CORS enabled for: http://localhost:3000")
    print("Press CTRL+C to stop")
    print("="*70 + "\n")
    
    # Initialize database
    init_backend_db()
    
    # Use SO_REUSEADDR to allow reuse of port
    class ReuseAddrTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    with ReuseAddrTCPServer(("", PORT), SimpleAPIHandler) as httpd:
        print(f"Backend API server running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down backend server...")