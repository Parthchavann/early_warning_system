import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeftIcon,
  HeartIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  UserIcon,
  DocumentTextIcon,
  CalendarIcon,
  BuildingOfficeIcon,
  ArrowPathIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { patientAPI } from '../services/api';

const PatientDetail = () => {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [vitals, setVitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddVitals, setShowAddVitals] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newVitals, setNewVitals] = useState({
    heart_rate: '',
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    temperature: '',
    respiratory_rate: '',
    oxygen_saturation: '',
    glasgow_coma_scale: 15
  });

  useEffect(() => {
    loadPatientData();
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [patientResponse, vitalsResponse] = await Promise.all([
        patientAPI.getPatient(patientId).catch(err => {
          console.warn('Failed to load patient details:', err);
          return { data: null };
        }),
        patientAPI.getVitals(patientId).catch(err => {
          console.warn('Failed to load vitals:', err);
          return { data: [] };
        })
      ]);

      if (!patientResponse.data) {
        setError('Patient not found');
        return;
      }

      setPatient(patientResponse.data);
      setVitals(vitalsResponse.data || []);

    } catch (error) {
      console.error('Failed to load patient data:', error);
      setError('Failed to load patient data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddVitals = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      // Add timestamp to vitals
      const vitalsData = {
        ...newVitals,
        timestamp: new Date().toISOString(),
        // Convert string values to numbers
        heart_rate: newVitals.heart_rate ? parseFloat(newVitals.heart_rate) : null,
        blood_pressure_systolic: newVitals.blood_pressure_systolic ? parseFloat(newVitals.blood_pressure_systolic) : null,
        blood_pressure_diastolic: newVitals.blood_pressure_diastolic ? parseFloat(newVitals.blood_pressure_diastolic) : null,
        temperature: newVitals.temperature ? parseFloat(newVitals.temperature) : null,
        respiratory_rate: newVitals.respiratory_rate ? parseFloat(newVitals.respiratory_rate) : null,
        oxygen_saturation: newVitals.oxygen_saturation ? parseFloat(newVitals.oxygen_saturation) : null,
        glasgow_coma_scale: parseFloat(newVitals.glasgow_coma_scale) || 15
      };

      await patientAPI.addVitals(patientId, vitalsData);
      
      // Get updated risk prediction
      try {
        const riskResponse = await patientAPI.getRiskPrediction(patientId);
        console.log('New risk prediction:', riskResponse.data);
        
        // Update patient risk score
        setPatient(prev => ({
          ...prev,
          risk_score: riskResponse.data.risk_score?.overall_risk || prev.risk_score
        }));
      } catch (riskError) {
        console.warn('Failed to get risk prediction:', riskError);
      }
      
      // Reload patient data to get updated vitals
      await loadPatientData();
      
      // Reset form
      setNewVitals({
        heart_rate: '',
        blood_pressure_systolic: '',
        blood_pressure_diastolic: '',
        temperature: '',
        respiratory_rate: '',
        oxygen_saturation: '',
        glasgow_coma_scale: 15
      });
      setShowAddVitals(false);
      
    } catch (error) {
      console.error('Failed to add vital signs:', error);
      alert('Failed to add vital signs. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field, value) => {
    setNewVitals(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getRiskLevelColor = (riskScore) => {
    if (riskScore >= 0.8) return 'bg-red-100 text-red-800 border-red-200';
    if (riskScore >= 0.6) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (riskScore >= 0.4) return 'bg-blue-100 text-blue-800 border-blue-200';
    return 'bg-green-100 text-green-800 border-green-200';
  };

  const getRiskLevelText = (riskScore) => {
    if (riskScore >= 0.8) return 'Critical Risk';
    if (riskScore >= 0.6) return 'High Risk';
    if (riskScore >= 0.4) return 'Medium Risk';
    return 'Low Risk';
  };

  const getVitalStatus = (value, normal) => {
    if (!value || !normal) return 'text-gray-500';
    if (value < normal.min || value > normal.max) return 'text-red-600';
    return 'text-green-600';
  };

  const normalRanges = {
    heart_rate: { min: 60, max: 100 },
    blood_pressure_systolic: { min: 90, max: 140 },
    blood_pressure_diastolic: { min: 60, max: 90 },
    temperature: { min: 36.1, max: 37.2 },
    respiratory_rate: { min: 12, max: 20 },
    oxygen_saturation: { min: 95, max: 100 }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Link
            to="/patients"
            className="text-gray-400 hover:text-gray-600"
          >
            <ArrowLeftIcon className="w-6 h-6" />
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Patient Details</h1>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Patient Not Found</h3>
              <p className="mt-1 text-sm text-red-700">
                {error || `No patient found with ID: ${patientId}`}
              </p>
              <div className="mt-4 space-x-3">
                <button
                  onClick={loadPatientData}
                  className="text-sm text-red-600 hover:text-red-500 flex items-center space-x-1"
                >
                  <ArrowPathIcon className="w-4 h-4" />
                  <span>Try again</span>
                </button>
                <Link
                  to="/patients"
                  className="text-sm text-red-600 hover:text-red-500"
                >
                  Back to patients list
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Link
          to="/patients"
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <ArrowLeftIcon className="w-6 h-6" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">
            {patient.name || 'Patient Details'}
          </h1>
          <p className="text-gray-600">ID: {patient.patient_id}</p>
        </div>
        <button
          onClick={loadPatientData}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
        >
          <ArrowPathIcon className="w-5 h-5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Patient Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Info */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">Patient Information</h3>
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-xl font-bold text-blue-600">
                {patient.name ? patient.name.charAt(0).toUpperCase() : 'P'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <UserIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Full Name</p>
                  <p className="font-medium text-gray-900">{patient.name || 'Not available'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <DocumentTextIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">MRN</p>
                  <p className="font-medium text-gray-900">{patient.mrn || 'Not assigned'}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <CalendarIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Age / Gender</p>
                  <p className="font-medium text-gray-900">
                    {patient.age || 'N/A'} years • {
                      patient.gender === 'M' ? 'Male' :
                      patient.gender === 'F' ? 'Female' :
                      patient.gender || 'Not specified'
                    }
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <BuildingOfficeIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Department</p>
                  <p className="font-medium text-gray-900">
                    {patient.department || 'Not assigned'}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <CalendarIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Admission Date</p>
                  <p className="font-medium text-gray-900">
                    {patient.admission_date ? 
                      new Date(patient.admission_date).toLocaleDateString() : 
                      'Not recorded'
                    }
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <DocumentTextIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">Primary Diagnosis</p>
                  <p className="font-medium text-gray-900">
                    {patient.primary_diagnosis || 'Not specified'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Medical History */}
          {patient.medical_history && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Medical History</h4>
              <p className="text-sm text-gray-700">{patient.medical_history}</p>
            </div>
          )}

          {/* Current Medications */}
          {patient.current_medications && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Current Medications</h4>
              <p className="text-sm text-gray-700">{patient.current_medications}</p>
            </div>
          )}
        </div>

        {/* Risk Assessment */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Risk Assessment</h3>

          {patient.risk_score !== undefined ? (
            <div className="space-y-4">
              <div className="text-center">
                <div className={`inline-flex items-center px-4 py-2 rounded-lg border text-lg font-medium ${getRiskLevelColor(patient.risk_score)}`}>
                  {getRiskLevelText(patient.risk_score)}
                </div>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {(patient.risk_score * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500">Deterioration Risk</p>
              </div>

              <div className="bg-gray-100 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all duration-300 ${
                    patient.risk_score >= 0.8 ? 'bg-red-500' :
                    patient.risk_score >= 0.6 ? 'bg-yellow-500' :
                    patient.risk_score >= 0.4 ? 'bg-blue-500' :
                    'bg-green-500'
                  }`}
                  style={{ width: `${patient.risk_score * 100}%` }}
                />
              </div>

              <div className="text-xs text-gray-500 space-y-1">
                <div className="flex justify-between">
                  <span>Low</span>
                  <span>Critical</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No Risk Data</h3>
              <p className="mt-1 text-sm text-gray-500">Risk assessment not available.</p>
            </div>
          )}
        </div>
      </div>

      {/* Vital Signs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Recent Vital Signs</h3>
            <p className="text-sm text-gray-600">Latest measurements and trends</p>
          </div>
          <button
            onClick={() => setShowAddVitals(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Vital Signs
          </button>
        </div>

        {vitals.length > 0 ? (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {vitals.slice(0, 1).map(vital => (
                <React.Fragment key={vital.id || 'latest'}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-3">
                      <HeartIcon className="w-8 h-8 text-red-500" />
                      <div>
                        <p className="text-sm text-gray-500">Heart Rate</p>
                        <p className={`text-xl font-bold ${getVitalStatus(vital.heart_rate, normalRanges.heart_rate)}`}>
                          {vital.heart_rate || 'N/A'} {vital.heart_rate && 'bpm'}
                        </p>
                        <p className="text-xs text-gray-400">Normal: 60-100 bpm</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 text-sm font-bold">BP</span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Blood Pressure</p>
                        <p className={`text-xl font-bold ${
                          vital.blood_pressure_systolic || vital.blood_pressure_diastolic ? 
                          'text-gray-900' : 'text-gray-500'
                        }`}>
                          {vital.blood_pressure_systolic || 'N/A'}/{vital.blood_pressure_diastolic || 'N/A'}
                        </p>
                        <p className="text-xs text-gray-400">Normal: 90-140/60-90</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-green-600 text-sm font-bold">O₂</span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Oxygen Saturation</p>
                        <p className={`text-xl font-bold ${getVitalStatus(vital.oxygen_saturation, normalRanges.oxygen_saturation)}`}>
                          {vital.oxygen_saturation || 'N/A'}{vital.oxygen_saturation && '%'}
                        </p>
                        <p className="text-xs text-gray-400">Normal: 95-100%</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                        <span className="text-yellow-600 text-sm font-bold">°C</span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Temperature</p>
                        <p className={`text-xl font-bold ${getVitalStatus(vital.temperature, normalRanges.temperature)}`}>
                          {vital.temperature || 'N/A'}{vital.temperature && '°C'}
                        </p>
                        <p className="text-xs text-gray-400">Normal: 36.1-37.2°C</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <span className="text-purple-600 text-sm font-bold">RR</span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Respiratory Rate</p>
                        <p className={`text-xl font-bold ${getVitalStatus(vital.respiratory_rate, normalRanges.respiratory_rate)}`}>
                          {vital.respiratory_rate || 'N/A'} {vital.respiratory_rate && '/min'}
                        </p>
                        <p className="text-xs text-gray-400">Normal: 12-20 /min</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="bg-gray-50 rounded-lg p-4"
                  >
                    <div className="flex items-center space-x-3">
                      <ClockIcon className="w-8 h-8 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Last Updated</p>
                        <p className="text-sm font-medium text-gray-900">
                          {vital.timestamp ? 
                            new Date(vital.timestamp).toLocaleString() : 
                            'Unknown'
                          }
                        </p>
                        <p className="text-xs text-gray-400">Automatic monitoring</p>
                      </div>
                    </div>
                  </motion.div>
                </React.Fragment>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <HeartIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Vital Signs</h3>
            <p className="mt-1 text-sm text-gray-500">No vital sign data available for this patient.</p>
          </div>
        )}
      </div>

      {/* Add Vital Signs Modal */}
      {showAddVitals && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Add Vital Signs</h3>
                <button
                  onClick={() => setShowAddVitals(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Enter current vital signs for {patient?.name || 'this patient'}
              </p>
            </div>

            <form onSubmit={handleAddVitals} className="px-6 py-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Heart Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    min="30"
                    max="220"
                    value={newVitals.heart_rate}
                    onChange={(e) => handleInputChange('heart_rate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 72"
                  />
                  <p className="text-xs text-gray-500 mt-1">Normal: 60-100 bpm</p>
                </div>

                {/* Blood Pressure Systolic */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Systolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    min="60"
                    max="250"
                    value={newVitals.blood_pressure_systolic}
                    onChange={(e) => handleInputChange('blood_pressure_systolic', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 120"
                  />
                  <p className="text-xs text-gray-500 mt-1">Normal: 90-140 mmHg</p>
                </div>

                {/* Blood Pressure Diastolic */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Diastolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    min="30"
                    max="150"
                    value={newVitals.blood_pressure_diastolic}
                    onChange={(e) => handleInputChange('blood_pressure_diastolic', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 80"
                  />
                  <p className="text-xs text-gray-500 mt-1">Normal: 60-90 mmHg</p>
                </div>

                {/* Temperature */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature (°C)
                  </label>
                  <input
                    type="number"
                    min="30"
                    max="45"
                    step="0.1"
                    value={newVitals.temperature}
                    onChange={(e) => handleInputChange('temperature', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 36.8"
                  />
                  <p className="text-xs text-gray-500 mt-1">Normal: 36.1-37.2°C</p>
                </div>

                {/* Respiratory Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Respiratory Rate (/min)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="60"
                    value={newVitals.respiratory_rate}
                    onChange={(e) => handleInputChange('respiratory_rate', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 16"
                  />
                  <p className="text-xs text-gray-500 mt-1">Normal: 12-20 /min</p>
                </div>

                {/* Oxygen Saturation */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Oxygen Saturation (%)
                  </label>
                  <input
                    type="number"
                    min="70"
                    max="100"
                    value={newVitals.oxygen_saturation}
                    onChange={(e) => handleInputChange('oxygen_saturation', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. 98"
                  />
                  <p className="text-xs text-gray-500 mt-1">Normal: 95-100%</p>
                </div>

                {/* Glasgow Coma Scale */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Glasgow Coma Scale
                  </label>
                  <select
                    value={newVitals.glasgow_coma_scale}
                    onChange={(e) => handleInputChange('glasgow_coma_scale', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {[...Array(12)].map((_, i) => (
                      <option key={i + 3} value={i + 3}>
                        {i + 3} - {i + 3 === 15 ? 'Normal' : i + 3 >= 13 ? 'Mild' : i + 3 >= 9 ? 'Moderate' : 'Severe'}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Normal: 15</p>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowAddVitals(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {isSubmitting ? 'Adding...' : 'Add Vital Signs'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default PatientDetail;