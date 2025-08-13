import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  HeartIcon,
  EyeIcon,
  EyeSlashIcon,
  UserIcon,
  LockClosedIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const { login, signup, loading, error, clearError } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    role: 'nurse',
    department: ''
  });
  const [validationErrors, setValidationErrors] = useState({});

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear validation errors for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
    
    clearError();
  };

  const validateForm = () => {
    const errors = {};
    
    // Email validation
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }
    
    if (isSignup) {
      // Name validation
      if (!formData.name) {
        errors.name = 'Full name is required';
      } else if (formData.name.trim().length < 2) {
        errors.name = 'Please enter your full name';
      }
      
      // Confirm password validation
      if (!formData.confirmPassword) {
        errors.confirmPassword = 'Please confirm your password';
      } else if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = 'Passwords do not match';
      }
      
      // Department validation
      if (!formData.department) {
        errors.department = 'Department is required';
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      let result;
      if (isSignup) {
        result = await signup({
          email: formData.email,
          password: formData.password,
          name: formData.name,
          role: formData.role,
          department: formData.department
        });
      } else {
        result = await login({
          email: formData.email,
          password: formData.password
        });
      }
      
      if (result.success) {
        // Auth context will handle the redirect
        console.log(`${isSignup ? 'Signup' : 'Login'} successful`);
      }
    } catch (error) {
      console.error('Authentication error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full space-y-8"
      >
        {/* Header */}
        <div className="text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
            className="mx-auto w-20 h-20 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full flex items-center justify-center mb-4 shadow-lg"
          >
            <HeartIcon className="w-10 h-10 text-red-400" />
          </motion.div>
          <h2 className="text-3xl font-bold text-blue-900">CarePulse</h2>
          <p className="text-sm text-blue-600 font-medium">Early Warning System</p>
          <p className="mt-2 text-lg text-gray-700">
            {isSignup ? 'Create your account' : 'Sign in to your account'}
          </p>
        </div>

        {/* Form */}
        <motion.form
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 space-y-6"
          onSubmit={handleSubmit}
        >
          <div className="bg-white rounded-lg shadow-lg p-8 space-y-6">
            {/* Security Badge */}
            <div className="flex items-center justify-center space-x-2 bg-green-50 border border-green-200 rounded-md p-3">
              <ShieldCheckIcon className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-green-700">Secure Authentication</span>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Name field (signup only) */}
            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Full Name
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className={`pl-10 w-full px-3 py-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                      validationErrors.name ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter your full name"
                  />
                </div>
                {validationErrors.name && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
                )}
              </div>
            )}

            {/* Email field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className={`pl-10 w-full px-3 py-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    validationErrors.email ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter your email"
                  required
                />
              </div>
              {validationErrors.email && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
              )}
            </div>

            {/* Password field */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <LockClosedIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`pl-10 pr-10 w-full px-3 py-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    validationErrors.password ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-500"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {validationErrors.password && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
              )}
            </div>

            {/* Confirm Password field (signup only) */}
            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password
                </label>
                <div className="relative">
                  <LockClosedIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                    className={`pl-10 pr-10 w-full px-3 py-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                      validationErrors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Confirm your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-500"
                  >
                    {showConfirmPassword ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
                {validationErrors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.confirmPassword}</p>
                )}
              </div>
            )}

            {/* Department field (signup only) */}
            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Department
                </label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => handleInputChange('department', e.target.value)}
                  className={`w-full px-3 py-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                    validationErrors.department ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="e.g., ICU, Emergency, Cardiology"
                />
                {validationErrors.department && (
                  <p className="mt-1 text-sm text-red-600">{validationErrors.department}</p>
                )}
              </div>
            )}

            {/* Role field (signup only) */}
            {isSignup && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => handleInputChange('role', e.target.value)}
                  className="w-full px-3 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="nurse">Nurse</option>
                  <option value="doctor">Doctor</option>
                  <option value="resident">Resident</option>
                  <option value="specialist">Specialist</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            )}

            {/* Submit button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className={`w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>{isSignup ? 'Creating Account...' : 'Signing In...'}</span>
                </div>
              ) : (
                isSignup ? 'Create Account' : 'Sign In'
              )}
            </motion.button>

            {/* Toggle between login/signup */}
            <div className="text-center">
              <button
                type="button"
                onClick={() => {
                  setIsSignup(!isSignup);
                  clearError();
                  setValidationErrors({});
                  setFormData({ 
                    email: '', 
                    password: '', 
                    confirmPassword: '',
                    name: '', 
                    role: 'nurse',
                    department: ''
                  });
                }}
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                {isSignup 
                  ? 'Already have an account? Sign in' 
                  : 'Need an account? Sign up'
                }
              </button>
            </div>

            {/* Security Notice */}
            <div className="bg-blue-50 rounded-md p-4 mt-4">
              <p className="text-xs text-blue-700 text-center">
                <strong>Secure Login:</strong> Your credentials are encrypted and protected with industry-standard security measures.
              </p>
            </div>
          </div>
        </motion.form>
      </motion.div>
    </div>
  );
};

export default Login;