import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import { 
  ChartBarIcon,
  DocumentArrowDownIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  CheckCircleIcon,
  ServerIcon
} from '@heroicons/react/24/outline';
// Removed old API imports - now using direct fetch for real-time data
import { exportToPDF, exportToCSV } from '../utils/exportUtils';

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    loadAnalyticsData();
    
    // Set up real-time refresh every 30 seconds
    const interval = setInterval(() => {
      loadAnalyticsData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch real-time analytics data from the enhanced backend
      const response = await fetch('http://localhost:8000/analytics');
      
      if (!response.ok) {
        throw new Error(`Analytics API returned ${response.status}`);
      }
      
      const analyticsData = await response.json();
      
      if (analyticsData.error) {
        throw new Error(analyticsData.error);
      }

      // Use the real-time data directly from the backend
      const processedData = {
        totalPatients: analyticsData.totalPatients,
        avgRiskScore: analyticsData.avgRiskScore, // Already in percentage format
        alertResponseTime: analyticsData.alertResponseTime,
        predictionAccuracy: analyticsData.predictionAccuracy,
        systemUptime: analyticsData.systemUptime,
        criticalPatients: analyticsData.criticalPatients,
        highRiskPatients: analyticsData.highRiskPatients,
        patientsWithVitals: analyticsData.patientsWithVitals
      };

      // Use real chart data from backend
      setData(processedData);
      setChartData({
        departmentComparison: analyticsData.departmentComparison || [],
        riskDistribution: analyticsData.riskDistribution || [],
        patientFlow: analyticsData.patientFlow || [],
        alertFrequency: analyticsData.alertFrequency || []
      });

      console.log('✅ Analytics data loaded:', {
        patients: processedData.totalPatients,
        avgRisk: processedData.avgRiskScore + '%',
        responseTime: processedData.alertResponseTime + 'min',
        departments: analyticsData.departmentComparison?.length || 0,
        lastUpdated: analyticsData.lastUpdated,
        processedData,  // Show the processed data that goes to state
        rawData: analyticsData  // Debug: show raw data
      });
      
      console.log('📊 State will be updated with:', {
        data: processedData,
        chartData: {
          departmentComparison: analyticsData.departmentComparison || [],
          riskDistribution: analyticsData.riskDistribution || [],
          patientFlow: analyticsData.patientFlow || [],
          alertFrequency: analyticsData.alertFrequency || []
        }
      });

    } catch (error) {
      console.error('Failed to load analytics data:', error);
      setError('Failed to load analytics data: ' + error.message);
      
      // Fallback to prevent blank page
      setData({
        totalPatients: 0,
        avgRiskScore: 0,
        alertResponseTime: 0,
        predictionAccuracy: 0,
        systemUptime: 0
      });
      setChartData({
        departmentComparison: [],
        riskDistribution: [],
        patientFlow: [],
        alertFrequency: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = () => {
    if (data && chartData) {
      exportToPDF(data, chartData, 'Patient Analytics Report');
    }
  };

  const handleExportCSV = () => {
    if (data && chartData) {
      exportToCSV(data, chartData, 'patient_analytics');
    }
  };

  const kpiCards = [
    {
      title: 'Total Patients',
      value: data?.totalPatients ?? 0,
      icon: ChartBarIcon,
      color: 'blue',
      description: 'Currently monitored'
    },
    {
      title: 'Avg Risk Score',
      value: data?.avgRiskScore ?? 0,
      suffix: '%',
      icon: ArrowTrendingUpIcon,
      color: 'yellow',
      description: 'Average risk across all patients'
    },
    {
      title: 'Response Time',
      value: data?.alertResponseTime ?? 0,
      suffix: 'min',
      icon: ClockIcon,
      color: 'green',
      description: 'Average alert response time'
    },
    {
      title: 'Prediction Accuracy',
      value: data?.predictionAccuracy ?? 0,
      suffix: '%',
      icon: CheckCircleIcon,
      color: 'purple',
      description: 'ML model accuracy'
    },
    {
      title: 'System Uptime',
      value: data?.systemUptime ?? 0,
      suffix: '%',
      icon: ServerIcon,
      color: 'green',
      description: 'System availability'
    }
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: { bg: 'bg-blue-100', text: 'text-blue-600', border: 'border-blue-200' },
      yellow: { bg: 'bg-yellow-100', text: 'text-yellow-600', border: 'border-yellow-200' },
      green: { bg: 'bg-green-100', text: 'text-green-600', border: 'border-green-200' },
      purple: { bg: 'bg-purple-100', text: 'text-purple-600', border: 'border-purple-200' },
      red: { bg: 'bg-red-100', text: 'text-red-600', border: 'border-red-200' }
    };
    return colors[color] || colors.blue;
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
            <h3 className="text-sm font-medium text-red-800">Analytics Error</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button
              onClick={loadAnalyticsData}
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Performance insights and reports</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={loadAnalyticsData}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
          >
            <ArrowPathIcon className="w-5 h-5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleExportCSV}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
          >
            <DocumentArrowDownIcon className="w-5 h-5" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={handleExportPDF}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
          >
            <DocumentArrowDownIcon className="w-5 h-5" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {kpiCards.map((kpi, index) => {
          const colorClasses = getColorClasses(kpi.color);
          
          return (
            <motion.div
              key={kpi.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className={`p-3 rounded-lg ${colorClasses.bg}`}>
                  <kpi.icon className={`w-6 h-6 ${colorClasses.text}`} />
                </div>
              </div>
              <div className="mt-4">
                <p className="text-2xl font-bold text-gray-900">
                  <CountUp end={kpi.value} duration={2} decimals={kpi.title.includes('Score') || kpi.title.includes('Accuracy') || kpi.title.includes('Uptime') ? 1 : 0} />
                  {kpi.suffix && <span className="text-lg">{kpi.suffix}</span>}
                </p>
                <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                <p className="text-xs text-gray-500">{kpi.description}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Department Performance Table */}
      {chartData?.departmentComparison && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Department Performance</h3>
            <p className="text-sm text-gray-600">Comparative analysis across departments</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Department
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Patients
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Response Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Alert Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Efficiency
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {chartData.departmentComparison.map((dept, index) => (
                  <motion.tr
                    key={dept.department}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {dept.department}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {dept.patientCount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {Math.round(dept.responseTime)} min
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        dept.accuracy >= 90 ? 'bg-green-100 text-green-800' : 
                        dept.accuracy >= 85 ? 'bg-yellow-100 text-yellow-800' : 
                        'bg-red-100 text-red-800'
                      }`}>
                        {Math.round(dept.accuracy)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {Math.round(dept.alertRate)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${dept.efficiency}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-500">{Math.round(dept.efficiency)}%</span>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {/* Export Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <DocumentArrowDownIcon className="h-5 w-5 text-blue-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Export Reports</h3>
            <p className="mt-1 text-sm text-blue-700">
              Download comprehensive analytics reports in PDF or CSV format. 
              Reports include all KPIs, department performance metrics, and risk distribution data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;