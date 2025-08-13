import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ExclamationTriangleIcon,
  BellIcon,
  ArrowPathIcon,
  CheckIcon,
  XMarkIcon,
  ClockIcon,
  UserIcon,
  HeartIcon,
  EyeIcon,
  FunnelIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { useAlerts } from '../contexts/AlertContext';

const Alerts = () => {
  // Use global alert context
  const { 
    alerts, 
    loading, 
    error, 
    acknowledgeAlert, 
    dismissAlert, 
    refreshAlerts 
  } = useAlerts();
  
  const [filter, setFilter] = useState('all'); // all, critical, high, medium, acknowledged
  const [sortBy, setSortBy] = useState('timestamp'); // timestamp, severity, patient
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedAlert, setExpandedAlert] = useState(null);

  const getSeverityColor = (severity, riskScore) => {
    if (severity === 'critical' || (riskScore && riskScore >= 0.8)) {
      return 'border-red-500 bg-red-50';
    } else if (severity === 'high' || (riskScore && riskScore >= 0.6)) {
      return 'border-yellow-500 bg-yellow-50';
    } else if (severity === 'medium' || (riskScore && riskScore >= 0.4)) {
      return 'border-blue-500 bg-blue-50';
    }
    return 'border-gray-300 bg-gray-50';
  };

  const getSeverityIcon = (severity, riskScore) => {
    if (severity === 'critical' || (riskScore && riskScore >= 0.8)) {
      return <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />;
    } else if (severity === 'high' || (riskScore && riskScore >= 0.6)) {
      return <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600" />;
    }
    return <BellIcon className="w-6 h-6 text-blue-600" />;
  };

  const getRiskLevelColor = (riskScore) => {
    if (riskScore >= 0.8) return 'text-red-600 bg-red-100';
    if (riskScore >= 0.6) return 'text-yellow-600 bg-yellow-100';
    if (riskScore >= 0.4) return 'text-blue-600 bg-blue-100';
    return 'text-green-600 bg-green-100';
  };

  const getRiskLevelText = (riskScore) => {
    if (riskScore >= 0.8) return 'Critical';
    if (riskScore >= 0.6) return 'High';
    if (riskScore >= 0.4) return 'Medium';
    return 'Low';
  };

  const filteredAndSortedAlerts = alerts
    .filter(alert => {
      // Filter by status
      if (filter === 'acknowledged' && !alert.is_acknowledged) return false;
      if (filter === 'critical' && alert.severity !== 'critical' && (alert.risk_score < 0.8)) return false;
      if (filter === 'high' && alert.severity !== 'high' && (alert.risk_score < 0.6 || alert.risk_score >= 0.8)) return false;
      if (filter === 'medium' && alert.severity !== 'medium' && (alert.risk_score < 0.4 || alert.risk_score >= 0.6)) return false;
      
      // Filter by search term
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          alert.patient_name?.toLowerCase().includes(term) ||
          alert.patient_id?.toLowerCase().includes(term) ||
          alert.department?.toLowerCase().includes(term) ||
          alert.message?.toLowerCase().includes(term)
        );
      }
      
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'severity':
          const severityOrder = { critical: 3, high: 2, medium: 1, low: 0 };
          return (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);
        case 'patient':
          return (a.patient_name || '').localeCompare(b.patient_name || '');
        case 'timestamp':
        default:
          return new Date(b.timestamp || b.created_at) - new Date(a.timestamp || a.created_at);
      }
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Alerts</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button
              onClick={refreshAlerts}
              className="mt-2 text-sm text-red-600 hover:text-red-500 flex items-center space-x-1"
            >
              <ArrowPathIcon className="w-4 h-4" />
              <span>Try again</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alert Management</h1>
          <p className="text-gray-600">Monitor and manage all system alerts</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Live Updates</span>
          </div>
          <button
            onClick={refreshAlerts}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
          >
            <ArrowPathIcon className="w-5 h-5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-red-100">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => !a.is_acknowledged).length}
              </p>
              <p className="text-sm font-medium text-gray-600">Active Alerts</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-red-100">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.severity === 'critical' || (a.risk_score >= 0.8)).length}
              </p>
              <p className="text-sm font-medium text-gray-600">Critical</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-yellow-100">
              <ExclamationTriangleIcon className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.severity === 'high' || (a.risk_score >= 0.6 && a.risk_score < 0.8)).length}
              </p>
              <p className="text-sm font-medium text-gray-600">High Risk</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-green-100">
              <CheckIcon className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {alerts.filter(a => a.is_acknowledged).length}
              </p>
              <p className="text-sm font-medium text-gray-600">Acknowledged</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Search */}
          <div className="flex-1 min-w-0 max-w-md">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search patients, departments, or messages..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <FunnelIcon className="w-5 h-5 text-gray-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Alerts</option>
                <option value="critical">Critical Only</option>
                <option value="high">High Risk Only</option>
                <option value="medium">Medium Risk Only</option>
                <option value="acknowledged">Acknowledged</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="timestamp">Time</option>
                <option value="severity">Severity</option>
                <option value="patient">Patient</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAndSortedAlerts.length > 0 ? (
          <AnimatePresence>
            {filteredAndSortedAlerts.map((alert, index) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
                className={`bg-white rounded-lg shadow-sm border-l-4 p-6 ${getSeverityColor(alert.severity, alert.risk_score)} ${
                  alert.is_acknowledged ? 'opacity-75' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4 flex-1">
                    {/* Alert Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getSeverityIcon(alert.severity, alert.risk_score)}
                    </div>

                    {/* Alert Content */}
                    <div className="flex-1 min-w-0">
                      {/* Alert Header */}
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-bold text-gray-900">
                          {alert.title || 'Critical Alert'}
                        </h3>
                        <div className="flex items-center space-x-2">
                          {alert.risk_score !== undefined && (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${getRiskLevelColor(alert.risk_score)}`}>
                              {getRiskLevelText(alert.risk_score)} ({(alert.risk_score * 100).toFixed(1)}%)
                            </span>
                          )}
                          {alert.is_acknowledged && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                              Acknowledged
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Patient Info Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div className="bg-white border border-gray-200 rounded-md p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <UserIcon className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700">Patient</span>
                          </div>
                          <p className="font-semibold text-gray-900">
                            {alert.patient_name || `ID: ${alert.patient_id}`}
                          </p>
                          <p className="text-sm text-gray-600">
                            {alert.age ? `${alert.age}y` : 'Age N/A'} 
                            {alert.gender ? ` • ${alert.gender}` : ''}
                          </p>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-md p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <HeartIcon className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700">Location</span>
                          </div>
                          <p className="font-semibold text-gray-900">
                            {alert.department || 'General Ward'}
                          </p>
                          <p className="text-sm text-gray-600">
                            {alert.room_number ? `Room ${alert.room_number}` : 'Room N/A'}
                            {alert.bed_number ? ` • Bed ${alert.bed_number}` : ''}
                          </p>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-md p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <ClockIcon className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700">Time</span>
                          </div>
                          <p className="font-semibold text-gray-900">
                            {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : 'Just now'}
                          </p>
                          <p className="text-sm text-gray-600">
                            {alert.timestamp ? new Date(alert.timestamp).toLocaleDateString() : 'Today'}
                          </p>
                        </div>
                      </div>

                      {/* Alert Message */}
                      <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mb-4">
                        <p className="text-sm font-medium text-gray-800 mb-1">Alert Details:</p>
                        <p className="text-sm text-gray-700">{alert.message}</p>
                      </div>

                      {/* Expandable Vital Signs */}
                      {alert.vitals && (
                        <div className="border border-gray-200 rounded-md mb-4">
                          <button
                            onClick={() => setExpandedAlert(expandedAlert === alert.id ? null : alert.id)}
                            className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50"
                          >
                            <span className="text-sm font-medium text-gray-700">Current Vital Signs</span>
                            {expandedAlert === alert.id ? (
                              <ChevronUpIcon className="w-4 h-4 text-gray-500" />
                            ) : (
                              <ChevronDownIcon className="w-4 h-4 text-gray-500" />
                            )}
                          </button>
                          
                          {expandedAlert === alert.id && (
                            <div className="border-t border-gray-200 p-3 bg-gray-50">
                              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                                {alert.vitals.heart_rate && (
                                  <div className="text-center">
                                    <p className="font-bold text-gray-900">{alert.vitals.heart_rate}</p>
                                    <p className="text-gray-600">HR (bpm)</p>
                                  </div>
                                )}
                                {alert.vitals.blood_pressure_systolic && (
                                  <div className="text-center">
                                    <p className="font-bold text-gray-900">
                                      {alert.vitals.blood_pressure_systolic}/{alert.vitals.blood_pressure_diastolic}
                                    </p>
                                    <p className="text-gray-600">BP (mmHg)</p>
                                  </div>
                                )}
                                {alert.vitals.respiratory_rate && (
                                  <div className="text-center">
                                    <p className="font-bold text-gray-900">{alert.vitals.respiratory_rate}</p>
                                    <p className="text-gray-600">RR (/min)</p>
                                  </div>
                                )}
                                {alert.vitals.temperature && (
                                  <div className="text-center">
                                    <p className="font-bold text-gray-900">{alert.vitals.temperature}</p>
                                    <p className="text-gray-600">Temp (°C)</p>
                                  </div>
                                )}
                                {alert.vitals.oxygen_saturation && (
                                  <div className="text-center">
                                    <p className="font-bold text-gray-900">{alert.vitals.oxygen_saturation}</p>
                                    <p className="text-gray-600">O2 (%)</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex items-center justify-between pt-3">
                        <div className="flex space-x-3">
                          <Link
                            to={`/patients/${alert.patient_id}`}
                            className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                          >
                            <EyeIcon className="w-4 h-4" />
                            <span>View Patient</span>
                          </Link>
                          
                          {!alert.is_acknowledged && (
                            <button
                              onClick={() => acknowledgeAlert(alert.id)}
                              className="inline-flex items-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                            >
                              <CheckIcon className="w-4 h-4" />
                              <span>Acknowledge</span>
                            </button>
                          )}
                          
                          <button
                            onClick={() => dismissAlert(alert.id)}
                            className="inline-flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                          >
                            <XMarkIcon className="w-4 h-4" />
                            <span>Dismiss</span>
                          </button>
                        </div>

                        <p className="text-xs text-gray-500">
                          Alert ID: {alert.id}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        ) : (
          <div className="text-center py-12">
            <BellIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {searchTerm || filter !== 'all' ? 'No matching alerts' : 'No active alerts'}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || filter !== 'all' 
                ? 'Try adjusting your search or filter criteria.' 
                : 'All patients are stable.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;