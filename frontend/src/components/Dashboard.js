import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import { 
  UserGroupIcon,
  ExclamationTriangleIcon,
  BellIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { patientAPI, statsAPI } from '../services/api';
import { useAlerts } from '../contexts/AlertContext';

const Dashboard = ({ onAddPatient }) => {
  const [stats, setStats] = useState(null);
  const [recentPatients, setRecentPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Use global alert context
  const { activeAlerts, acknowledgeAlert } = useAlerts();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsResponse, patientsResponse] = await Promise.all([
        statsAPI.getDashboardStats().catch(err => ({ data: null })),
        patientAPI.getAllPatients().catch(err => ({ data: [] }))
      ]);

      setStats(statsResponse.data);
      // Get the 5 most recent patients
      const patients = patientsResponse.data || [];
      setRecentPatients(patients.slice(0, 5));

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Patients',
      value: stats?.total_patients || 0,
      icon: UserGroupIcon,
      color: 'blue',
      trend: { direction: 'up', value: '12%' },
      description: 'Currently admitted'
    },
    {
      title: 'Critical Patients',
      value: stats?.critical_patients || 0,
      icon: ExclamationTriangleIcon,
      color: 'red',
      trend: { direction: 'down', value: '5%' },
      description: 'High risk scores'
    },
    {
      title: 'Active Alerts',
      value: stats?.active_alerts || 0,
      icon: BellIcon,
      color: 'yellow',
      trend: { direction: 'up', value: '8%' },
      description: 'Requires attention'
    },
    {
      title: 'Avg Response Time',
      value: stats?.avg_response_time || 0,
      icon: ClockIcon,
      color: 'green',
      trend: { direction: 'down', value: '15%' },
      description: 'Minutes to respond',
      suffix: 'min'
    }
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: {
        bg: 'bg-blue-100',
        text: 'text-blue-600',
        border: 'border-blue-200'
      },
      red: {
        bg: 'bg-red-100',
        text: 'text-red-600',
        border: 'border-red-200'
      },
      yellow: {
        bg: 'bg-yellow-100',
        text: 'text-yellow-600',
        border: 'border-yellow-200'
      },
      green: {
        bg: 'bg-green-100',
        text: 'text-green-600',
        border: 'border-green-200'
      }
    };
    return colors[color] || colors.blue;
  };

  const getRiskLevelColor = (riskScore) => {
    if (riskScore >= 0.8) return 'text-red-600 bg-red-100';
    if (riskScore >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getRiskLevelText = (riskScore) => {
    if (riskScore >= 0.8) return 'Critical';
    if (riskScore >= 0.6) return 'High';
    if (riskScore >= 0.4) return 'Medium';
    return 'Low';
  };

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
            <h3 className="text-sm font-medium text-red-800">Dashboard Error</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button
              onClick={loadDashboardData}
              className="mt-2 text-sm text-red-600 hover:text-red-500"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Patient monitoring overview</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={onAddPatient}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Add Patient</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const colorClasses = getColorClasses(stat.color);
          const TrendIcon = stat.trend.direction === 'up' ? ArrowTrendingUpIcon : ArrowTrendingDownIcon;
          const trendColor = stat.trend.direction === 'up' ? 'text-green-600' : 'text-red-600';

          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className={`p-3 rounded-lg ${colorClasses.bg}`}>
                  <stat.icon className={`w-6 h-6 ${colorClasses.text}`} />
                </div>
                <div className={`flex items-center space-x-1 ${trendColor}`}>
                  <TrendIcon className="w-4 h-4" />
                  <span className="text-sm font-medium">{stat.trend.value}</span>
                </div>
              </div>
              <div className="mt-4">
                <p className="text-2xl font-bold text-gray-900">
                  <CountUp end={stat.value} duration={2} />
                  {stat.suffix && <span className="text-lg">{stat.suffix}</span>}
                </p>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-xs text-gray-500">{stat.description}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Patients */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Recent Patients</h3>
              <Link
                to="/patients"
                className="text-blue-600 hover:text-blue-500 text-sm font-medium"
              >
                View all
              </Link>
            </div>
          </div>
          <div className="p-6">
            {recentPatients.length > 0 ? (
              <div className="space-y-4">
                {recentPatients.map((patient) => (
                  <div key={patient.patient_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          {patient.name ? patient.name.charAt(0).toUpperCase() : 'P'}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {patient.name || 'Name not available'}
                        </p>
                        <p className="text-sm text-gray-500">
                          ID: {patient.patient_id} • {patient.department || 'No dept'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {patient.risk_score !== undefined && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(patient.risk_score)}`}>
                          {getRiskLevelText(patient.risk_score)}
                        </span>
                      )}
                      <Link
                        to={`/patients/${patient.patient_id}`}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <EyeIcon className="w-5 h-5" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No recent patients</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by adding a new patient.</p>
              </div>
            )}
          </div>
        </div>

        {/* Active Alerts */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Active Alerts</h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-500">Live</span>
              </div>
            </div>
          </div>
          <div className="p-6">
            {activeAlerts.length > 0 ? (
              <div className="space-y-4">
                {activeAlerts.map((alert, index) => (
                  <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mt-1" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="text-sm font-bold text-red-800 mb-2">
                              🚨 {alert.title || 'CRITICAL ALERT'}
                            </h4>
                            
                            {/* Patient Information */}
                            <div className="bg-white border border-red-100 rounded-md p-3 mb-3">
                              <div className="grid grid-cols-2 gap-3 text-sm">
                                <div>
                                  <span className="font-medium text-gray-700">Patient:</span>
                                  <p className="text-gray-900 font-semibold">
                                    {alert.patient_name || alert.name || `ID: ${alert.patient_id || 'Unknown'}`}
                                  </p>
                                </div>
                                <div>
                                  <span className="font-medium text-gray-700">Room/Bed:</span>
                                  <p className="text-gray-900">
                                    {alert.room_number || alert.bed_number || 'Not assigned'}
                                  </p>
                                </div>
                                <div>
                                  <span className="font-medium text-gray-700">Department:</span>
                                  <p className="text-gray-900">
                                    {alert.department || 'General Ward'}
                                  </p>
                                </div>
                                <div>
                                  <span className="font-medium text-gray-700">Age/Gender:</span>
                                  <p className="text-gray-900">
                                    {alert.age ? `${alert.age}y` : 'N/A'} {alert.gender ? `• ${alert.gender}` : ''}
                                  </p>
                                </div>
                              </div>
                              
                              {/* Risk Score */}
                              {alert.risk_score !== undefined && (
                                <div className="mt-2 pt-2 border-t border-gray-100">
                                  <div className="flex items-center justify-between">
                                    <span className="font-medium text-gray-700">Risk Score:</span>
                                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${getRiskLevelColor(alert.risk_score)}`}>
                                      {getRiskLevelText(alert.risk_score)} ({(alert.risk_score * 100).toFixed(1)}%)
                                    </span>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Alert Details */}
                            <div className="bg-red-100 border border-red-200 rounded-md p-3 mb-3">
                              <p className="text-sm font-medium text-red-800 mb-1">Alert Details:</p>
                              <p className="text-sm text-red-700">
                                {alert.message || `Patient ${alert.patient_id || 'Unknown'} requires immediate attention`}
                              </p>
                              
                              {/* Vital Signs if available */}
                              {alert.vitals && (
                                <div className="mt-2 pt-2 border-t border-red-300">
                                  <p className="text-xs font-medium text-red-800 mb-1">Current Vitals:</p>
                                  <div className="grid grid-cols-2 gap-2 text-xs text-red-700">
                                    {alert.vitals.heart_rate && (
                                      <div>HR: <span className="font-bold">{alert.vitals.heart_rate} bpm</span></div>
                                    )}
                                    {alert.vitals.blood_pressure_systolic && (
                                      <div>BP: <span className="font-bold">{alert.vitals.blood_pressure_systolic}/{alert.vitals.blood_pressure_diastolic} mmHg</span></div>
                                    )}
                                    {alert.vitals.respiratory_rate && (
                                      <div>RR: <span className="font-bold">{alert.vitals.respiratory_rate} /min</span></div>
                                    )}
                                    {alert.vitals.temperature && (
                                      <div>Temp: <span className="font-bold">{alert.vitals.temperature}°C</span></div>
                                    )}
                                    {alert.vitals.oxygen_saturation && (
                                      <div>O2: <span className="font-bold">{alert.vitals.oxygen_saturation}%</span></div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Timestamp and Actions */}
                            <div className="flex items-center justify-between">
                              <p className="text-xs text-red-600 font-medium">
                                ⏰ {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Just now'}
                              </p>
                              
                              <div className="flex space-x-2">
                                <Link
                                  to={`/patients/${alert.patient_id}`}
                                  className="text-xs bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md font-medium transition-colors"
                                >
                                  View Patient
                                </Link>
                                <button 
                                  onClick={() => acknowledgeAlert(alert.id)}
                                  className="text-xs bg-white hover:bg-red-50 text-red-600 border border-red-300 px-3 py-1 rounded-md font-medium transition-colors">
                                  Acknowledge
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <BellIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No active alerts</h3>
                <p className="mt-1 text-sm text-gray-500">All patients are stable.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/patients"
            className="flex items-center p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <UserGroupIcon className="w-8 h-8 text-blue-600 mr-3" />
            <div>
              <p className="font-medium text-blue-900">Manage Patients</p>
              <p className="text-sm text-blue-700">View and edit patient records</p>
            </div>
          </Link>
          
          <Link
            to="/analytics"
            className="flex items-center p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors"
          >
            <ArrowTrendingUpIcon className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <p className="font-medium text-green-900">View Analytics</p>
              <p className="text-sm text-green-700">Reports and insights</p>
            </div>
          </Link>
          
          <button
            onClick={onAddPatient}
            className="flex items-center p-4 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors"
          >
            <PlusIcon className="w-8 h-8 text-purple-600 mr-3" />
            <div>
              <p className="font-medium text-purple-900">Add Patient</p>
              <p className="text-sm text-purple-700">Register new patient</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;