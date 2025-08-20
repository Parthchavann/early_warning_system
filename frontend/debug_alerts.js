// Debug script to test AlertContext functionality
// This would be used in browser console or as a test

console.log('🔍 Debug: Testing Alert Context');

// Simulate what AlertContext fetchAlerts does
fetch('http://localhost:8080/alerts/active')
  .then(response => response.json())
  .then(data => {
    console.log('Raw backend response:', data);
    
    // Process like AlertContext
    let alertsData = [];
    if (data && data.alerts && Array.isArray(data.alerts)) {
      alertsData = data.alerts.map(alert => ({
        ...alert,
        id: alert.alert_id || alert.id,
        is_acknowledged: alert.is_acknowledged || alert.acknowledged || false
      }));
    }
    
    console.log('Processed alerts:', alertsData);
    
    // Filter like AlertContext
    const activeAlerts = alertsData.filter(alert => !alert.is_acknowledged);
    const criticalAlerts = alertsData.filter(alert => 
      alert.severity === 'critical' || (alert.risk_score && alert.risk_score >= 0.8)
    );
    
    console.log(`✅ Active alerts: ${activeAlerts.length}`);
    console.log(`🚨 Critical alerts: ${criticalAlerts.length}`);
    
    console.log('Critical alerts details:');
    criticalAlerts.forEach((alert, index) => {
      console.log(`  ${index + 1}. ${alert.patient_name} (${alert.id}) - Risk: ${alert.risk_score}`);
    });
    
    // Check if Dashboard should show these
    if (activeAlerts.length > 0) {
      console.log('🎯 Dashboard should display these alerts in the "Active Alerts" section');
    } else {
      console.log('❌ No active alerts - Dashboard will show "No active alerts" message');
    }
  })
  .catch(error => {
    console.error('❌ Error fetching alerts:', error);
  });