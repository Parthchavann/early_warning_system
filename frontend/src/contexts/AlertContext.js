import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { alertAPI } from '../services/api';

const AlertContext = createContext();

export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlerts must be used within an AlertProvider');
  }
  return context;
};

export const AlertProvider = ({ children }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await alertAPI.getActiveAlerts();
      
      // Handle the correct response structure
      let alertsData = [];
      if (response.data && response.data.alerts && Array.isArray(response.data.alerts)) {
        alertsData = response.data.alerts.map(alert => ({
          ...alert,
          id: alert.alert_id || alert.id, // Map alert_id to id for frontend compatibility
          is_acknowledged: alert.is_acknowledged || alert.acknowledged || false
        }));
      } else if (Array.isArray(response.data)) {
        alertsData = response.data.map(alert => ({
          ...alert,
          id: alert.alert_id || alert.id,
          is_acknowledged: alert.is_acknowledged || alert.acknowledged || false
        }));
      }
      
      
      setAlerts(alertsData);
      setLastUpdated(new Date());
      return alertsData;
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      setError('Failed to load alerts');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const acknowledgeAlert = useCallback(async (alertId) => {
    try {
      // Optimistically update the UI
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, is_acknowledged: true } : alert
      ));
      
      // Make API call to acknowledge alert on server
      await alertAPI.acknowledgeAlert(alertId);
      
      console.log(`Alert ${alertId} acknowledged`);
      setLastUpdated(new Date());
      
      // Refresh alerts to ensure consistency
      setTimeout(() => fetchAlerts(), 500);
      
      return true;
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      // Revert optimistic update on error by fetching fresh data
      await fetchAlerts();
      return false;
    }
  }, [fetchAlerts]);

  const dismissAlert = useCallback(async (alertId) => {
    try {
      // Optimistically update the UI
      setAlerts(prev => prev.filter(alert => alert.id !== alertId));
      
      // Make API call to dismiss alert on server
      await alertAPI.dismissAlert(alertId);
      
      console.log(`Alert ${alertId} dismissed`);
      setLastUpdated(new Date());
      
      // Refresh alerts to ensure consistency
      setTimeout(() => fetchAlerts(), 500);
      
      return true;
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
      // Revert optimistic update on error by fetching fresh data
      await fetchAlerts();
      return false;
    }
  }, [fetchAlerts]);

  const refreshAlerts = useCallback(() => {
    return fetchAlerts();
  }, [fetchAlerts]);

  // Auto-refresh alerts every 30 seconds
  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  // Computed values
  const activeAlerts = alerts.filter(alert => !alert.is_acknowledged);
  const criticalAlerts = alerts.filter(alert => 
    alert.severity === 'critical' || (alert.risk_score && alert.risk_score >= 0.8)
  );
  const highRiskAlerts = alerts.filter(alert => 
    alert.severity === 'high' || (alert.risk_score && alert.risk_score >= 0.6 && alert.risk_score < 0.8)
  );
  const acknowledgedAlerts = alerts.filter(alert => alert.is_acknowledged);

  const stats = {
    total: alerts.length,
    active: activeAlerts.length,
    critical: criticalAlerts.length,
    highRisk: highRiskAlerts.length,
    acknowledged: acknowledgedAlerts.length
  };

  const value = {
    // State
    alerts,
    loading,
    error,
    lastUpdated,
    stats,
    
    // Computed arrays
    activeAlerts,
    criticalAlerts,
    highRiskAlerts,
    acknowledgedAlerts,
    
    // Actions
    fetchAlerts,
    acknowledgeAlert,
    dismissAlert,
    refreshAlerts
  };

  return (
    <AlertContext.Provider value={value}>
      {children}
    </AlertContext.Provider>
  );
};

export default AlertContext;