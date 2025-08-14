#!/usr/bin/env python3
"""
Production HTTP server for Patient Deterioration System
Serves both the React app (static files) and API endpoints
Optimized for production deployment
"""
import http.server
import socketserver
import json
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import os
import random
import time
import hashlib
import secrets
import hmac
import base64
import mimetypes
from pathlib import Path

# Production configuration
DB_PATH = 'patient_ews.db'
STATIC_DIR = 'build'  # React build directory
JWT_SECRET = os.environ.get("JWT_SECRET", "secure-production-key-change-me")
TOKEN_EXPIRY_HOURS = 24
PORT = int(os.environ.get("PORT", 8080))

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

class ProductionHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)
    
    def end_headers(self):
        # Add security headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.send_header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        super().end_headers()
    
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # API routes
        if path.startswith('/api/') or path in ['/health', '/patients', '/alerts/active', '/analytics', '/auth/verify', '/stats']:
            self.handle_api_request()
        else:
            # Serve static files or React app
            self.serve_static_file(path)
    
    def do_POST(self):
        self.handle_api_request()
    
    def do_PUT(self):
        self.handle_api_request()
    
    def do_DELETE(self):
        self.handle_api_request()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def serve_static_file(self, path):
        """Serve static files and handle React routing"""
        if path == '/':
            path = '/index.html'
        
        file_path = Path(STATIC_DIR) / path.lstrip('/')
        
        # If file doesn't exist and it's not an API route, serve index.html (React routing)
        if not file_path.exists() and not path.startswith('/api/'):
            file_path = Path(STATIC_DIR) / 'index.html'
        
        if file_path.exists():
            self.send_response(200)
            content_type, _ = mimetypes.guess_type(str(file_path))
            if content_type:
                self.send_header('Content-Type', content_type)
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'File not found')
    
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
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
                return
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"API Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
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
    
    def get_active_alerts(self):
        """Get active alerts with sample data"""
        alerts = []
        
        # Generate some sample alerts for demo
        sample_alerts = [
            {
                "alert_id": "ALERT_001",
                "patient_id": "PAT_001",
                "patient_name": "John Smith",
                "severity": "high",
                "risk_score": 0.85,
                "message": "Critical vital signs detected",
                "timestamp": datetime.utcnow().isoformat(),
                "room": "ICU-101",
                "vitals": {
                    "heart_rate": 140,
                    "blood_pressure": "90/60",
                    "temperature": 39.2,
                    "oxygen_saturation": 88
                }
            }
        ]
        
        return {"alerts": sample_alerts, "count": len(sample_alerts)}
    
    def get_patients(self):
        """Get patients list with sample data"""
        patients = [
            {
                "patient_id": "PAT_001",
                "name": "John Smith",
                "age": 65,
                "room": "ICU-101",
                "risk_score": 0.85,
                "status": "critical"
            },
            {
                "patient_id": "PAT_002", 
                "name": "Jane Doe",
                "age": 45,
                "room": "ICU-102",
                "risk_score": 0.35,
                "status": "stable"
            }
        ]
        
        return {"patients": patients, "count": len(patients)}
    
    def get_stats(self):
        """Get dashboard stats"""
        return {
            "total_patients": 156,
            "active_alerts": 3,
            "high_risk_patients": 12,
            "average_risk_score": 0.42
        }
    
    def get_analytics_data(self):
        """Get analytics data with sample data"""
        return {
            "total_patients": 156,
            "active_alerts": 3,
            "average_risk_score": 0.42,
            "trends": {
                "risk_scores": [0.3, 0.35, 0.42, 0.38, 0.45],
                "alert_counts": [2, 4, 3, 1, 3]
            }
        }

def init_production_db():
    """Initialize production database"""
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
        print("✅ Production database initialized")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    print("="*70)
    print("🚀 Patient Deterioration System - Production Server")
    print("="*70)
    print(f"📁 Serving static files from: {STATIC_DIR}")
    print(f"📁 Database: {DB_PATH}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print("Press CTRL+C to stop")
    print("="*70 + "\n")
    
    # Initialize database
    init_production_db()
    
    # Use SO_REUSEADDR to allow reuse of port
    class ReuseAddrTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    with ReuseAddrTCPServer(("", PORT), ProductionHandler) as httpd:
        print(f"Production server running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down production server...")