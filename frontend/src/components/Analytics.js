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
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8001'}/analytics`);
      
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

      {/* Interactive Data Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Donut Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300"
        >
          <div className="px-6 py-4 bg-gradient-to-r from-red-500 to-orange-500">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <ExclamationTriangleIcon className="w-6 h-6 mr-2" />
              Patient Risk Distribution
            </h3>
            <p className="text-red-100 text-sm">Real-time risk level breakdown</p>
          </div>
          <div className="p-6">
            <div className="relative h-64 flex items-center justify-center">
              {/* Donut Chart SVG */}
              <svg className="w-56 h-56 transform -rotate-90" viewBox="0 0 200 200">
                <defs>
                  <linearGradient id="criticalGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#DC2626" />
                    <stop offset="100%" stopColor="#EF4444" />
                  </linearGradient>
                  <linearGradient id="highGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#EA580C" />
                    <stop offset="100%" stopColor="#F97316" />
                  </linearGradient>
                  <linearGradient id="mediumGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#D97706" />
                    <stop offset="100%" stopColor="#F59E0B" />
                  </linearGradient>
                  <linearGradient id="lowGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#059669" />
                    <stop offset="100%" stopColor="#10B981" />
                  </linearGradient>
                </defs>
                {chartData?.riskDistribution && (() => {
                  const total = chartData.riskDistribution.reduce((sum, dept) => 
                    sum + dept.critical_risk + dept.high_risk + dept.medium_risk + dept.low_risk, 0
                  ) || 1;
                  const criticalTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.critical_risk, 0);
                  const highTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.high_risk, 0);
                  const mediumTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.medium_risk, 0);
                  const lowTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.low_risk, 0);
                  
                  const radius = 70;
                  const strokeWidth = 20;
                  const circumference = 2 * Math.PI * radius;
                  
                  const criticalPercent = (criticalTotal / total) * 100;
                  const highPercent = (highTotal / total) * 100;
                  const mediumPercent = (mediumTotal / total) * 100;
                  const lowPercent = (lowTotal / total) * 100;
                  
                  let currentOffset = 0;
                  
                  return (
                    <>
                      {/* Background circle */}
                      <circle
                        cx="100"
                        cy="100"
                        r={radius}
                        fill="none"
                        stroke="#F3F4F6"
                        strokeWidth={strokeWidth}
                      />
                      
                      {/* Critical risk segment */}
                      {criticalTotal > 0 && (
                        <circle
                          cx="100"
                          cy="100"
                          r={radius}
                          fill="none"
                          stroke="url(#criticalGradient)"
                          strokeWidth={strokeWidth}
                          strokeLinecap="round"
                          strokeDasharray={`${(criticalPercent / 100) * circumference} ${circumference}`}
                          strokeDashoffset={-currentOffset}
                          className="animate-pulse"
                        />
                      )}
                      
                      {/* High risk segment */}
                      {highTotal > 0 && (
                        <circle
                          cx="100"
                          cy="100"
                          r={radius}
                          fill="none"
                          stroke="url(#highGradient)"
                          strokeWidth={strokeWidth}
                          strokeLinecap="round"
                          strokeDasharray={`${(highPercent / 100) * circumference} ${circumference}`}
                          strokeDashoffset={-(currentOffset += (criticalPercent / 100) * circumference)}
                        />
                      )}
                      
                      {/* Medium risk segment */}
                      {mediumTotal > 0 && (
                        <circle
                          cx="100"
                          cy="100"
                          r={radius}
                          fill="none"
                          stroke="url(#mediumGradient)"
                          strokeWidth={strokeWidth}
                          strokeLinecap="round"
                          strokeDasharray={`${(mediumPercent / 100) * circumference} ${circumference}`}
                          strokeDashoffset={-(currentOffset += (highPercent / 100) * circumference)}
                        />
                      )}
                      
                      {/* Low risk segment */}
                      {lowTotal > 0 && (
                        <circle
                          cx="100"
                          cy="100"
                          r={radius}
                          fill="none"
                          stroke="url(#lowGradient)"
                          strokeWidth={strokeWidth}
                          strokeLinecap="round"
                          strokeDasharray={`${(lowPercent / 100) * circumference} ${circumference}`}
                          strokeDashoffset={-(currentOffset += (mediumPercent / 100) * circumference)}
                        />
                      )}
                    </>
                  );
                })()}
              </svg>
              
              {/* Center content */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-3xl font-bold text-gray-800">
                  {chartData?.riskDistribution ? 
                    chartData.riskDistribution.reduce((sum, dept) => 
                      sum + dept.critical_risk + dept.high_risk + dept.medium_risk + dept.low_risk, 0
                    ) : 0
                  }
                </div>
                <div className="text-sm text-gray-600 font-medium">Total Patients</div>
              </div>
            </div>
            
            {/* Legend */}
            <div className="grid grid-cols-2 gap-3 mt-6">
              {chartData?.riskDistribution && (() => {
                const criticalTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.critical_risk, 0);
                const highTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.high_risk, 0);
                const mediumTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.medium_risk, 0);
                const lowTotal = chartData.riskDistribution.reduce((sum, dept) => sum + dept.low_risk, 0);
                
                return (
                  <>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gradient-to-r from-red-600 to-red-500 rounded-full"></div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">Critical</div>
                        <div className="text-lg font-bold text-red-600">{criticalTotal}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gradient-to-r from-orange-600 to-orange-500 rounded-full"></div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">High Risk</div>
                        <div className="text-lg font-bold text-orange-600">{highTotal}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gradient-to-r from-yellow-600 to-yellow-500 rounded-full"></div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">Medium</div>
                        <div className="text-lg font-bold text-yellow-600">{mediumTotal}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-gradient-to-r from-green-600 to-green-500 rounded-full"></div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">Low Risk</div>
                        <div className="text-lg font-bold text-green-600">{lowTotal}</div>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </motion.div>

        {/* Alert Trends Line Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-all duration-300"
        >
          <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <ArrowTrendingUpIcon className="w-6 h-6 mr-2" />
              Alert Trends (7 Days)
            </h3>
            <p className="text-blue-100 text-sm">Daily alert frequency patterns</p>
          </div>
          <div className="p-6">
            <div className="h-64">
              {/* Line Chart SVG */}
              <svg className="w-full h-full" viewBox="0 0 400 200">
                <defs>
                  <linearGradient id="criticalLineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#DC2626" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#DC2626" stopOpacity="0.1" />
                  </linearGradient>
                  <linearGradient id="highLineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#EA580C" stopOpacity="0.6" />
                    <stop offset="100%" stopColor="#EA580C" stopOpacity="0.1" />
                  </linearGradient>
                </defs>
                
                {chartData?.alertFrequency && (() => {
                  const data = chartData.alertFrequency;
                  const maxValue = Math.max(...data.map(d => Math.max(d.critical, d.high, d.medium, d.low))) || 10;
                  const width = 400;
                  const height = 200;
                  const padding = 30;
                  const chartWidth = width - 2 * padding;
                  const chartHeight = height - 2 * padding;
                  
                  const getX = (index) => padding + (index * chartWidth) / (data.length - 1);
                  const getY = (value) => height - padding - (value * chartHeight) / maxValue;
                  
                  const criticalPath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.critical)}`).join(' ');
                  const highPath = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.high)}`).join(' ');
                  
                  return (
                    <g>
                      {/* Grid lines */}
                      {[0, 1, 2, 3, 4].map(i => (
                        <line
                          key={i}
                          x1={padding}
                          y1={padding + (i * chartHeight) / 4}
                          x2={width - padding}
                          y2={padding + (i * chartHeight) / 4}
                          stroke="#F3F4F6"
                          strokeWidth="1"
                        />
                      ))}
                      
                      {/* Critical alerts line with area */}
                      <path
                        d={`${criticalPath} L ${getX(data.length - 1)} ${height - padding} L ${padding} ${height - padding} Z`}
                        fill="url(#criticalLineGradient)"
                      />
                      <path
                        d={criticalPath}
                        fill="none"
                        stroke="#DC2626"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      
                      {/* High risk alerts line with area */}
                      <path
                        d={`${highPath} L ${getX(data.length - 1)} ${height - padding} L ${padding} ${height - padding} Z`}
                        fill="url(#highLineGradient)"
                      />
                      <path
                        d={highPath}
                        fill="none"
                        stroke="#EA580C"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      
                      {/* Data points */}
                      {data.map((d, i) => (
                        <g key={i}>
                          <circle
                            cx={getX(i)}
                            cy={getY(d.critical)}
                            r="4"
                            fill="#DC2626"
                            className="hover:r-6 transition-all cursor-pointer"
                          />
                          <circle
                            cx={getX(i)}
                            cy={getY(d.high)}
                            r="3"
                            fill="#EA580C"
                            className="hover:r-5 transition-all cursor-pointer"
                          />
                        </g>
                      ))}
                      
                      {/* X-axis labels */}
                      {data.map((d, i) => (
                        <text
                          key={i}
                          x={getX(i)}
                          y={height - 5}
                          textAnchor="middle"
                          className="text-xs fill-gray-500"
                        >
                          {new Date(d.date).getDate()}
                        </text>
                      ))}
                    </g>
                  );
                })()}
              </svg>
            </div>
            
            {/* Chart Legend */}
            <div className="flex items-center justify-center space-x-6 mt-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-600 rounded-full"></div>
                <span className="text-sm font-medium text-gray-700">Critical Alerts</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-orange-600 rounded-full"></div>
                <span className="text-sm font-medium text-gray-700">High Risk Alerts</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>


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