import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Bars3Icon } from '@heroicons/react/24/outline';

// Components
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Patients from './components/Patients';
import Alerts from './components/Alerts';
import Analytics from './components/Analytics';
import PatientDetail from './components/PatientDetail';
import Settings from './components/Settings';
import AddPatientModal from './components/AddPatientModal';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';

// Context
import { AuthProvider } from './contexts/AuthContext';
import { AlertProvider } from './contexts/AlertContext';

import './App.css';

// Layout component for the main app structure
const DashboardLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showAddPatientModal, setShowAddPatientModal] = useState(false);
  const location = useLocation();

  const handlePatientAdded = (newPatient) => {
    // Force a page refresh to update all components with new data
    window.location.reload();
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header - Always visible */}
      <Header />
      
      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />
        
        {/* Main Content */}
        <div className="flex-1 lg:ml-0">
          {/* Mobile Navigation Bar */}
          <div className="bg-white shadow-sm border-b border-gray-200 lg:hidden">
            <div className="px-4 py-3">
              <div className="flex items-center justify-between">
                <button
                  onClick={toggleSidebar}
                  className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                >
                  <Bars3Icon className="w-6 h-6" />
                </button>
                <h1 className="text-lg font-semibold text-blue-900">CarePulse</h1>
                <div className="w-10"></div> {/* Spacer */}
              </div>
            </div>
          </div>

          {/* Page Content */}
          <main className="p-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                {React.cloneElement(children, {
                  onAddPatient: () => setShowAddPatientModal(true)
                })}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>

      {/* Add Patient Modal */}
      <AddPatientModal
        isOpen={showAddPatientModal}
        onClose={() => setShowAddPatientModal(false)}
        onPatientAdded={handlePatientAdded}
      />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <AlertProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Default redirect to dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              
              {/* Protected dashboard routes */}
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Dashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/patients" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Patients />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/patients/:patientId" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <PatientDetail />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/alerts" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Alerts />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/analytics" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Analytics />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              
              <Route path="/settings" element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Settings />
                  </DashboardLayout>
                </ProtectedRoute>
              } />
              
              {/* Fallback for unknown routes */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </Router>
      </AlertProvider>
    </AuthProvider>
  );
}

export default App;