#!/usr/bin/env node
/**
 * Debug script to test the Analytics API response and identify the issue
 */

async function debugAnalytics() {
    const fetch = require('node-fetch');
    
    console.log('🔍 DEBUGGING ANALYTICS API RESPONSE');
    console.log('=' * 50);
    
    try {
        console.log('📡 Fetching from http://localhost:8000/analytics...');
        const response = await fetch('http://localhost:8000/analytics');
        
        if (!response.ok) {
            console.error(`❌ API Error: ${response.status} ${response.statusText}`);
            return;
        }
        
        const analyticsData = await response.json();
        
        console.log('\n📊 RAW API RESPONSE:');
        console.log('avgRiskScore:', analyticsData.avgRiskScore, '(type:', typeof analyticsData.avgRiskScore, ')');
        console.log('alertResponseTime:', analyticsData.alertResponseTime, '(type:', typeof analyticsData.alertResponseTime, ')');
        console.log('totalPatients:', analyticsData.totalPatients, '(type:', typeof analyticsData.totalPatients, ')');
        
        console.log('\n🧪 TESTING JAVASCRIPT LOGIC:');
        
        // Test the exact logic used in React component
        const processedData = {
            totalPatients: analyticsData.totalPatients,
            avgRiskScore: analyticsData.avgRiskScore, // Already in percentage format
            alertResponseTime: analyticsData.alertResponseTime,
            predictionAccuracy: analyticsData.predictionAccuracy,
            systemUptime: analyticsData.systemUptime,
        };
        
        console.log('processedData.avgRiskScore:', processedData.avgRiskScore);
        console.log('processedData.alertResponseTime:', processedData.alertResponseTime);
        
        // Test the KPI card logic
        console.log('\n🎯 KPI CARD VALUES:');
        console.log('Avg Risk Score card value:', processedData?.avgRiskScore ?? 0);
        console.log('Response Time card value:', processedData?.alertResponseTime ?? 0);
        
        // Test old logic vs new logic
        console.log('\n⚖️ COMPARING LOGIC:');
        console.log('OLD (|| 0):', processedData?.avgRiskScore || 0);
        console.log('NEW (?? 0):', processedData?.avgRiskScore ?? 0);
        
        // Test if values are truthy/falsy
        console.log('\n✅ TRUTHINESS TEST:');
        console.log('avgRiskScore is truthy:', !!processedData.avgRiskScore);
        console.log('alertResponseTime is truthy:', !!processedData.alertResponseTime);
        
        console.log('\n📈 FINAL VALUES THAT SHOULD DISPLAY:');
        console.log(`Average Risk Score: ${processedData.avgRiskScore}%`);
        console.log(`Alert Response Time: ${processedData.alertResponseTime}min`);
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

debugAnalytics();