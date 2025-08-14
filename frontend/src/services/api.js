import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_KEY = process.env.REACT_APP_API_KEY || 'secure-api-key-change-in-production';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000 // 10 second timeout
});

// Add auth token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else if (API_KEY) {
      config.headers.Authorization = `Bearer ${API_KEY}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status}`, response.data);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      // Handle authentication errors
      console.warn('Authentication failed. Please check API key.');
    } else if (error.response?.status === 500) {
      console.error('Server error. Please try again later.');
    } else if (error.code === 'ECONNREFUSED') {
      console.error(`Cannot connect to API server at ${API_BASE_URL}. Please ensure the server is running.`);
    }
    
    return Promise.reject(error);
  }
);

// Patient API methods
export const patientAPI = {
  // Get all patients
  getAllPatients: () => api.get('/patients'),
  
  // Get patient by ID
  getPatient: (id) => api.get(`/patients/${id}`),
  
  // Create new patient
  createPatient: (patientData) => api.post('/patients', patientData),
  
  // Update patient
  updatePatient: (id, patientData) => api.put(`/patients/${id}`, patientData),
  
  // Delete patient
  deletePatient: (id) => api.delete(`/patients/${id}`),
  
  // Add vital signs
  addVitals: (patientId, vitalsData) => api.post(`/patients/${patientId}/vitals`, vitalsData),
  
  // Get patient vital signs
  getVitals: (patientId) => api.get(`/patients/${patientId}/vitals`),
  
  // Get risk prediction
  getRiskPrediction: (patientId) => api.post(`/patients/${patientId}/predict`)
};

// Alert API methods
export const alertAPI = {
  // Get active alerts
  getActiveAlerts: () => api.get('/alerts/active'),
  
  // Acknowledge alert
  acknowledgeAlert: (alertId) => api.post(`/alerts/${alertId}/acknowledge`),
  
  // Dismiss alert (delete)
  dismissAlert: (alertId) => api.delete(`/alerts/${alertId}`),
  
  // Get alert history
  getAlertHistory: () => api.get('/alerts/history')
};

// Statistics API methods
export const statsAPI = {
  // Get dashboard statistics
  getDashboardStats: () => api.get('/stats'),
  
  // Get system health
  getSystemHealth: () => api.get('/health')
};

// Authentication API methods
export const authAPI = {
  // Login
  login: (credentials) => api.post('/auth/login', credentials),
  
  // Signup
  signup: (userData) => api.post('/auth/signup', userData),
  
  // Logout
  logout: () => api.post('/auth/logout'),
  
  // Verify token
  verifyToken: () => api.get('/auth/verify'),
  
  // Update profile
  updateProfile: (profileData) => api.put('/auth/profile', profileData),
  
  // Change password
  changePassword: (passwordData) => api.put('/auth/password', passwordData),
  
  // Refresh token
  refreshToken: () => api.post('/auth/refresh')
};

// Export default api instance
export default api;