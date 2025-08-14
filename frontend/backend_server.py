#!/usr/bin/env python3
"""
Backend API Server for Patient Deterioration System
Serves only API endpoints (no static files)
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

def calculate_risk_score(vitals):
    """Calculate risk score using original algorithm"""
    if not vitals:
        return 0.1
    
    latest = vitals[-1]
    risk_factors = 0
    
    # Heart rate thresholds
    if latest['heart_rate'] < 50 or latest['heart_rate'] > 120:
        risk_factors += 1
    
    # Blood pressure thresholds  
    if latest['blood_pressure_systolic'] < 90 or latest['blood_pressure_systolic'] > 160:
        risk_factors += 1
    
    # Respiratory rate thresholds
    if latest['respiratory_rate'] < 10 or latest['respiratory_rate'] > 24:
        risk_factors += 1
    
    # Temperature thresholds
    if latest['temperature'] < 35.0 or latest['temperature'] > 38.5:
        risk_factors += 1
    
    # Oxygen saturation thresholds
    if latest['oxygen_saturation'] < 90:
        risk_factors += 1
    
    # Calculate final risk score
    final_risk = min(0.9, risk_factors * 0.2 + 0.1)
    return final_risk

class BackendAPIHandler(http.server.BaseHTTPRequestHandler):
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:3000')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        # Add security headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
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
            
            # Remove /api prefix if present
            if path.startswith('/api'):
                path = path[4:]
            
            response = None
            
            # Authentication endpoints
            if path == '/auth/login' and self.command == 'POST':
                response = self.login()
            elif path == '/auth/verify' and self.command == 'GET':
                response = self.verify_auth()
            elif path == '/health':
                response = {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
            elif path == '/alerts/active':
                response = self.get_active_alerts()
            elif path == '/patients' and self.command == 'GET':
                response = self.get_patients()
            elif path == '/stats':
                response = self.get_stats()
            elif path == '/analytics' or path == '/analytics/data':
                response = self.get_analytics_data()
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
    
    def login(self):
        """Handle user login"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            credentials = json.loads(post_data)
            
            email = credentials.get('email')
            password = credentials.get('password')
            
            if not email or not password:
                return {"success": False, "message": "Email and password are required"}
            
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
            
            # Return user info from token
            return {
                "success": True,
                "user": {
                    "user_id": payload.get('user_id'),
                    "email": payload.get('email'),
                    "role": payload.get('role'),
                    "name": "Demo User"  # Since we don't store full name in token
                }
            }
            
        except Exception as e:
            print(f"Auth verification error: {e}")
            return {"success": False, "message": "Token verification failed"}
    
    def get_active_alerts(self):
        """Get active alerts from database"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Get active alerts with patient information
            query = """
                SELECT 
                    a.alert_id,
                    a.patient_id,
                    p.name as patient_name,
                    a.severity,
                    a.message,
                    a.risk_score,
                    a.created_at
                FROM alerts a
                LEFT JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.is_acknowledged = 0 OR a.is_acknowledged IS NULL
                ORDER BY a.created_at DESC
                LIMIT 50
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
                    "timestamp": row[6]
                })
            
            conn.close()
            return {"alerts": alerts, "count": len(alerts)}
            
        except Exception as e:
            print(f"Database error in get_active_alerts: {e}")
            # Fallback to empty alerts
            return {"alerts": [], "count": 0}
    
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
                    p.primary_diagnosis,
                    COALESCE(
                        (SELECT vs.heart_rate FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 0
                    ) as latest_hr,
                    COALESCE(
                        (SELECT vs.blood_pressure_systolic FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 0
                    ) as latest_bp_sys,
                    COALESCE(
                        (SELECT vs.temperature FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 0
                    ) as latest_temp,
                    COALESCE(
                        (SELECT vs.oxygen_saturation FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 0
                    ) as latest_o2
                FROM patients p
                ORDER BY p.admission_date DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            patients = []
            for row in rows:
                # Calculate risk score based on latest vitals
                vitals = [{
                    'heart_rate': row[5] or 70,
                    'blood_pressure_systolic': row[6] or 120,
                    'temperature': row[7] or 37.0,
                    'oxygen_saturation': row[8] or 98,
                    'respiratory_rate': 16  # Default since not in query
                }]
                
                risk_score = calculate_risk_score(vitals)
                
                # Determine status based on risk score
                if risk_score > 0.7:
                    status = "critical"
                elif risk_score > 0.5:
                    status = "warning"
                else:
                    status = "stable"
                
                patients.append({
                    "patient_id": row[0],
                    "name": row[1],
                    "age": row[2] or 0,
                    "admission_date": row[3],
                    "condition": row[4],
                    "risk_score": round(risk_score, 2),
                    "status": status,
                    "vitals": {
                        "heart_rate": row[5] or 0,
                        "blood_pressure": f"{row[6] or 120}/80",
                        "temperature": row[7] or 37.0,
                        "oxygen_saturation": row[8] or 98
                    }
                })
            
            conn.close()
            return {"patients": patients, "count": len(patients)}
            
        except Exception as e:
            print(f"Database error in get_patients: {e}")
            # Fallback to empty list if database fails
            return {"patients": [], "count": 0}
    
    def get_stats(self):
        """Get dashboard stats from database"""
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cursor = conn.cursor()
            
            # Get total patients
            cursor.execute("SELECT COUNT(*) FROM patients")
            total_patients = cursor.fetchone()[0]
            
            # Get active alerts 
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE is_acknowledged = 0 OR is_acknowledged IS NULL")
            active_alerts = cursor.fetchone()[0]
            
            # Get patients with risk calculation (simplified to avoid recursion)
            cursor.execute("""
                SELECT 
                    COALESCE(
                        (SELECT vs.heart_rate FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 70
                    ) as hr,
                    COALESCE(
                        (SELECT vs.blood_pressure_systolic FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 120
                    ) as bp,
                    COALESCE(
                        (SELECT vs.temperature FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 37.0
                    ) as temp,
                    COALESCE(
                        (SELECT vs.oxygen_saturation FROM vital_signs vs 
                         WHERE vs.patient_id = p.id 
                         ORDER BY vs.timestamp DESC LIMIT 1), 98
                    ) as o2
                FROM patients p
            """)
            
            rows = cursor.fetchall()
            high_risk_count = 0
            total_risk = 0
            
            for row in rows:
                # Simple risk calculation
                risk_factors = 0
                hr, bp, temp, o2 = row
                
                if hr < 50 or hr > 120:
                    risk_factors += 1
                if bp < 90 or bp > 160:
                    risk_factors += 1
                if temp < 35.0 or temp > 38.5:
                    risk_factors += 1
                if o2 < 90:
                    risk_factors += 1
                
                risk_score = min(0.9, risk_factors * 0.2 + 0.1)
                total_risk += risk_score
                
                if risk_score > 0.7:
                    high_risk_count += 1
            
            avg_risk = total_risk / len(rows) if rows else 0
            
            conn.close()
            
            return {
                "total_patients": total_patients,
                "active_alerts": active_alerts,
                "high_risk_patients": high_risk_count,
                "average_risk_score": round(avg_risk, 2)
            }
            
        except Exception as e:
            print(f"Database error in get_stats: {e}")
            # Fallback stats
            return {
                "total_patients": 0,
                "active_alerts": 0,
                "high_risk_patients": 0,
                "average_risk_score": 0.0
            }
    
    def get_analytics_data(self):
        """Get analytics data from database"""
        try:
            # Get real stats
            stats = self.get_stats()
            
            # Generate trend data based on real stats (simplified for demo)
            total_patients = stats.get('total_patients', 0)
            avg_risk = stats.get('average_risk_score', 0.0)
            
            # Create trend data (last 5 time periods)
            risk_scores = [
                max(0.1, avg_risk - 0.1),
                max(0.1, avg_risk - 0.05), 
                avg_risk,
                min(0.9, avg_risk + 0.02),
                min(0.9, avg_risk + 0.05)
            ]
            
            alert_counts = [0, 1, 0, 2, 0]  # Sample alert trend
            
            return {
                "total_patients": total_patients,
                "active_alerts": stats.get('active_alerts', 0),
                "average_risk_score": avg_risk,
                "trends": {
                    "risk_scores": risk_scores,
                    "alert_counts": alert_counts
                },
                "departments": [
                    {"name": "ICU", "patients": max(0, total_patients // 3)},
                    {"name": "Emergency", "patients": max(0, total_patients // 3)}, 
                    {"name": "General", "patients": max(0, total_patients - 2 * (total_patients // 3))}
                ],
                "risk_distribution": {
                    "low": max(0, total_patients - stats.get('high_risk_patients', 0) - 2),
                    "medium": 2,
                    "high": stats.get('high_risk_patients', 0)
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
                admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vital_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                heart_rate INTEGER,
                blood_pressure_systolic INTEGER,
                blood_pressure_diastolic INTEGER,
                respiratory_rate INTEGER,
                temperature REAL,
                oxygen_saturation INTEGER,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                risk_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Backend database initialized")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Patient Deterioration System - Backend API Server")
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
    
    with ReuseAddrTCPServer(("", PORT), BackendAPIHandler) as httpd:
        print(f"Backend API server running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down backend server...")