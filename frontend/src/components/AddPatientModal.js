import React, { useState } from 'react';
import { patientAPI } from '../services/api';

const AddPatientModal = ({ isOpen, onClose, onPatientAdded }) => {
  const [formData, setFormData] = useState({
    patient_id: '',
    name: '',
    age: '',
    gender: '',
    admission_date: '',
    department: '',
    medical_history: '',
    current_medications: '',
    mrn: '',
    primary_diagnosis: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.patient_id.trim()) {
      newErrors.patient_id = 'Patient ID is required';
    }
    
    if (!formData.name.trim()) {
      newErrors.name = 'Patient name is required';
    }
    
    if (!formData.age || formData.age < 1 || formData.age > 150) {
      newErrors.age = 'Please enter a valid age (1-150)';
    }
    
    if (!formData.gender) {
      newErrors.gender = 'Please select gender';
    }
    
    if (!formData.admission_date) {
      newErrors.admission_date = 'Admission date is required';
    }
    
    if (!formData.department.trim()) {
      newErrors.department = 'Department is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      const patientData = {
        ...formData,
        age: parseInt(formData.age),
        admission_date: new Date(formData.admission_date).toISOString(),
        created_at: new Date().toISOString()
      };
      
      console.log('Saving patient:', patientData);
      
      const response = await patientAPI.createPatient(patientData);
      
      console.log('Patient saved successfully:', response.data);
      
      // Reset form
      setFormData({
        patient_id: '',
        name: '',
        age: '',
        gender: '',
        admission_date: '',
        department: '',
        medical_history: '',
        current_medications: '',
        mrn: '',
        primary_diagnosis: ''
      });
      
      // Notify parent component
      if (onPatientAdded) {
        onPatientAdded(response.data);
      }
      
      // Close modal
      onClose();
      
      // Show success message
      alert('Patient added successfully!');
      
    } catch (error) {
      console.error('Error saving patient:', error);
      
      let errorMessage = 'Failed to save patient. ';
      
      if (error.response?.status === 400) {
        errorMessage += error.response.data?.detail || 'Invalid data provided.';
      } else if (error.response?.status === 409) {
        errorMessage += 'Patient with this ID already exists.';
      } else if (error.response?.status >= 500) {
        errorMessage += 'Server error. Please try again later.';
      } else {
        errorMessage += error.message || 'Please check your connection and try again.';
      }
      
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      patient_id: '',
      name: '',
      age: '',
      gender: '',
      admission_date: '',
      department: '',
      medical_history: '',
      current_medications: '',
      mrn: '',
      primary_diagnosis: ''
    });
    setErrors({});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
          <h2 className="text-xl font-bold">Add New Patient</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Patient ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Patient ID *
              </label>
              <input
                type="text"
                name="patient_id"
                value={formData.patient_id}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.patient_id ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., PATIENT_001"
                disabled={loading}
              />
              {errors.patient_id && (
                <p className="text-red-500 text-xs mt-1">{errors.patient_id}</p>
              )}
            </div>

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Patient full name"
                disabled={loading}
              />
              {errors.name && (
                <p className="text-red-500 text-xs mt-1">{errors.name}</p>
              )}
            </div>

            {/* Age */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Age *
              </label>
              <input
                type="number"
                name="age"
                value={formData.age}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.age ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Age in years"
                min="1"
                max="150"
                disabled={loading}
              />
              {errors.age && (
                <p className="text-red-500 text-xs mt-1">{errors.age}</p>
              )}
            </div>

            {/* Gender */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gender *
              </label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.gender ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              >
                <option value="">Select Gender</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
              {errors.gender && (
                <p className="text-red-500 text-xs mt-1">{errors.gender}</p>
              )}
            </div>

            {/* Admission Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Admission Date *
              </label>
              <input
                type="date"
                name="admission_date"
                value={formData.admission_date}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.admission_date ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={loading}
              />
              {errors.admission_date && (
                <p className="text-red-500 text-xs mt-1">{errors.admission_date}</p>
              )}
            </div>

            {/* MRN */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                MRN (Medical Record Number)
              </label>
              <input
                type="text"
                name="mrn"
                value={formData.mrn}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., MRN_12345"
                disabled={loading}
              />
            </div>

            {/* Primary Diagnosis */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Primary Diagnosis
              </label>
              <input
                type="text"
                name="primary_diagnosis"
                value={formData.primary_diagnosis}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Pneumonia, Heart Failure"
                disabled={loading}
              />
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Department *
              </label>
              <input
                type="text"
                name="department"
                value={formData.department}
                onChange={handleInputChange}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.department ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., ICU, Emergency, Cardiology"
                disabled={loading}
              />
              {errors.department && (
                <p className="text-red-500 text-xs mt-1">{errors.department}</p>
              )}
            </div>
          </div>

          {/* Medical History */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Medical History
            </label>
            <textarea
              name="medical_history"
              value={formData.medical_history}
              onChange={handleInputChange}
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Previous medical conditions, surgeries, etc."
              disabled={loading}
            />
          </div>

          {/* Current Medications */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Medications
            </label>
            <textarea
              name="current_medications"
              value={formData.current_medications}
              onChange={handleInputChange}
              rows="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Current medications and dosages"
              disabled={loading}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? 'Saving...' : 'Save Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddPatientModal;