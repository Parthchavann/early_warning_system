import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

export const exportToPDF = (data, chartData, title = 'Analytics Report') => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.width;
  
  // Title
  doc.setFontSize(20);
  doc.text(title, pageWidth / 2, 20, { align: 'center' });
  
  // Date
  doc.setFontSize(12);
  doc.text(`Generated on: ${new Date().toLocaleString()}`, pageWidth / 2, 30, { align: 'center' });
  
  let yPosition = 50;
  
  // KPI Summary
  if (data) {
    doc.setFontSize(16);
    doc.text('Key Performance Indicators', 20, yPosition);
    yPosition += 10;
    
    const kpiData = [
      ['Total Patients', data.totalPatients || 0],
      ['Average Risk Score', `${data.avgRiskScore || 0}%`],
      ['Response Time', `${data.alertResponseTime || 0} min`],
      ['Prediction Accuracy', `${data.predictionAccuracy || 0}%`],
      ['System Uptime', `${data.systemUptime || 0}%`]
    ];
    
    autoTable(doc, {
      startY: yPosition,
      head: [['Metric', 'Value']],
      body: kpiData,
      theme: 'grid',
      headStyles: { fillColor: [59, 130, 246] },
      margin: { left: 20, right: 20 }
    });
    
    yPosition = doc.lastAutoTable.finalY + 20;
  }
  
  // Department Statistics
  if (chartData && chartData.departmentComparison) {
    doc.setFontSize(16);
    doc.text('Department Performance', 20, yPosition);
    yPosition += 10;
    
    const deptData = chartData.departmentComparison.map(dept => [
      dept.department,
      Math.round(dept.responseTime) + ' min',
      Math.round(dept.accuracy) + '%',
      Math.round(dept.alertRate),
      Math.round(dept.efficiency) + '%'
    ]);
    
    autoTable(doc, {
      startY: yPosition,
      head: [['Department', 'Response Time', 'Accuracy', 'Alert Rate', 'Efficiency']],
      body: deptData,
      theme: 'grid',
      headStyles: { fillColor: [59, 130, 246] },
      margin: { left: 20, right: 20 }
    });
    
    yPosition = doc.lastAutoTable.finalY + 20;
  }
  
  // Risk Distribution Summary
  if (chartData && chartData.riskDistribution) {
    // Add new page if needed
    if (yPosition > 250) {
      doc.addPage();
      yPosition = 20;
    }
    
    doc.setFontSize(16);
    doc.text('Risk Distribution by Department', 20, yPosition);
    yPosition += 10;
    
    const riskData = chartData.riskDistribution.map(dept => [
      dept.department,
      dept.lowRisk || 0,
      dept.mediumRisk || 0,
      dept.highRisk || 0,
      dept.criticalRisk || 0,
      (dept.lowRisk + dept.mediumRisk + dept.highRisk + dept.criticalRisk) || 0
    ]);
    
    autoTable(doc, {
      startY: yPosition,
      head: [['Department', 'Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk', 'Total']],
      body: riskData,
      theme: 'grid',
      headStyles: { fillColor: [239, 68, 68] },
      margin: { left: 20, right: 20 }
    });
  }
  
  // Save the PDF
  doc.save(`${title.toLowerCase().replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`);
};

export const exportToCSV = (data, chartData, filename = 'analytics_data') => {
  let csvContent = '';
  
  // Add KPI data
  if (data) {
    csvContent += 'Key Performance Indicators\n';
    csvContent += 'Metric,Value\n';
    csvContent += `Total Patients,${data.totalPatients || 0}\n`;
    csvContent += `Average Risk Score,${data.avgRiskScore || 0}%\n`;
    csvContent += `Response Time,${data.alertResponseTime || 0} min\n`;
    csvContent += `Prediction Accuracy,${data.predictionAccuracy || 0}%\n`;
    csvContent += `System Uptime,${data.systemUptime || 0}%\n\n`;
  }
  
  // Add department comparison data
  if (chartData && chartData.departmentComparison) {
    csvContent += 'Department Performance\n';
    csvContent += 'Department,Response Time (min),Accuracy (%),Alert Rate,Efficiency (%)\n';
    
    chartData.departmentComparison.forEach(dept => {
      csvContent += `${dept.department},${Math.round(dept.responseTime)},${Math.round(dept.accuracy)},${Math.round(dept.alertRate)},${Math.round(dept.efficiency)}\n`;
    });
    csvContent += '\n';
  }
  
  // Add risk distribution data
  if (chartData && chartData.riskDistribution) {
    csvContent += 'Risk Distribution by Department\n';
    csvContent += 'Department,Low Risk,Medium Risk,High Risk,Critical Risk,Total\n';
    
    chartData.riskDistribution.forEach(dept => {
      const total = (dept.lowRisk || 0) + (dept.mediumRisk || 0) + (dept.highRisk || 0) + (dept.criticalRisk || 0);
      csvContent += `${dept.department},${dept.lowRisk || 0},${dept.mediumRisk || 0},${dept.highRisk || 0},${dept.criticalRisk || 0},${total}\n`;
    });
    csvContent += '\n';
  }
  
  // Add patient flow data
  if (chartData && chartData.patientFlow) {
    csvContent += 'Patient Flow Data\n';
    csvContent += 'Date,Admissions,Discharges,Total\n';
    
    chartData.patientFlow.forEach(flow => {
      csvContent += `${flow.date},${flow.admissions},${flow.discharges},${flow.total}\n`;
    });
    csvContent += '\n';
  }
  
  // Add alert frequency data
  if (chartData && chartData.alertFrequency) {
    csvContent += 'Alert Frequency by Severity\n';
    csvContent += 'Date,Critical,High,Medium,Low\n';
    
    chartData.alertFrequency.forEach(alert => {
      csvContent += `${alert.date},${alert.critical},${alert.high},${alert.medium},${alert.low}\n`;
    });
  }
  
  // Add timestamp
  csvContent += `\nGenerated on: ${new Date().toLocaleString()}\n`;
  
  // Create and download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};