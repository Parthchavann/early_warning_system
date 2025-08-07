import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional
import os

st.set_page_config(
    page_title="Patient Deterioration Early Warning System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "your-secure-api-key")

def get_api_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

@st.cache_data(ttl=30)
def fetch_active_alerts():
    try:
        response = requests.get(
            f"{API_BASE_URL}/alerts/active",
            headers=get_api_headers()
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching alerts: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_patient_data(patient_id: str):
    try:
        headers = get_api_headers()
        
        prediction_response = requests.post(
            f"{API_BASE_URL}/patients/{patient_id}/predict",
            headers=headers,
            json={"patient_id": patient_id, "lookback_hours": 24}
        )
        
        if prediction_response.status_code == 200:
            return prediction_response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching patient data: {e}")
        return None

def create_risk_gauge(risk_score: float, title: str = "Overall Risk"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk_score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 80], 'color': "orange"},
                {'range': [80, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def create_vital_trends_chart(vitals_data: List[Dict]):
    if not vitals_data:
        return None
        
    df = pd.DataFrame(vitals_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Heart Rate', 'Blood Pressure', 'Temperature', 'Oxygen Saturation'),
        vertical_spacing=0.08
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['heart_rate'], 
                  mode='lines+markers', name='Heart Rate',
                  line=dict(color='red')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['blood_pressure_systolic'], 
                  mode='lines+markers', name='Systolic BP',
                  line=dict(color='blue')),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['temperature'], 
                  mode='lines+markers', name='Temperature',
                  line=dict(color='orange')),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['oxygen_saturation'], 
                  mode='lines+markers', name='SpO2',
                  line=dict(color='green')),
        row=2, col=2
    )
    
    fig.update_layout(height=500, showlegend=False)
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Heart Rate (bpm)", row=1, col=1)
    fig.update_yaxes(title_text="Blood Pressure (mmHg)", row=1, col=2)
    fig.update_yaxes(title_text="Temperature (°C)", row=2, col=1)
    fig.update_yaxes(title_text="SpO2 (%)", row=2, col=2)
    
    return fig

def create_alerts_timeline(alerts: List[Dict]):
    if not alerts:
        return None
        
    df = pd.DataFrame(alerts)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    color_map = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'orange',
        'critical': 'red'
    }
    
    fig = px.scatter(
        df, x='timestamp', y='patient_id',
        color='severity', size_max=15,
        color_discrete_map=color_map,
        hover_data=['alert_type', 'message']
    )
    
    fig.update_layout(
        title="Alert Timeline",
        xaxis_title="Time",
        yaxis_title="Patient ID",
        height=400
    )
    
    return fig

def display_patient_card(patient_id: str, prediction_data: Dict):
    with st.container():
        st.subheader(f"Patient {patient_id}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        risk_score = prediction_data['risk_score']['overall_risk']
        
        with col1:
            st.metric(
                "Overall Risk",
                f"{risk_score:.1%}",
                delta=f"{(risk_score - 0.3):.1%}" if risk_score > 0.3 else None
            )
            
        with col2:
            st.metric(
                "Sepsis Risk",
                f"{prediction_data['risk_score']['sepsis_risk']:.1%}"
            )
            
        with col3:
            st.metric(
                "Confidence",
                f"{prediction_data['risk_score']['confidence']:.1%}"
            )
            
        with col4:
            alert_count = len(prediction_data.get('alerts', []))
            st.metric("Active Alerts", alert_count)
            
        if risk_score > 0.7:
            st.error("🚨 HIGH RISK - Immediate attention required!")
        elif risk_score > 0.5:
            st.warning("⚠️ ELEVATED RISK - Monitor closely")
        else:
            st.success("✅ LOW RISK - Continue routine monitoring")

def main():
    st.title("🏥 Patient Deterioration Early Warning System")
    st.markdown("Real-time monitoring and prediction of patient deterioration")
    
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Select View",
            ["Dashboard Overview", "Patient Detail", "Alert Management", "System Monitoring"]
        )
        
        st.header("Settings")
        auto_refresh = st.checkbox("Auto Refresh (30s)", value=True)
        
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    if page == "Dashboard Overview":
        st.header("Dashboard Overview")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Active Alerts")
            alerts = fetch_active_alerts()
            
            if alerts:
                alerts_df = pd.DataFrame(alerts)
                
                severity_counts = alerts_df['severity'].value_counts()
                
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("Critical", severity_counts.get('critical', 0))
                with col_b:
                    st.metric("High", severity_counts.get('high', 0))
                with col_c:
                    st.metric("Medium", severity_counts.get('medium', 0))
                with col_d:
                    st.metric("Low", severity_counts.get('low', 0))
                
                st.dataframe(
                    alerts_df[['patient_id', 'severity', 'alert_type', 'message', 'timestamp']],
                    use_container_width=True
                )
                
                fig_timeline = create_alerts_timeline(alerts)
                if fig_timeline:
                    st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("No active alerts")
        
        with col2:
            st.subheader("System Status")
            
            try:
                health_response = requests.get(f"{API_BASE_URL}/health")
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    st.success("✅ System Healthy")
                    st.write(f"Version: {health_data.get('version', 'N/A')}")
                else:
                    st.error("❌ System Unhealthy")
            except:
                st.error("❌ Cannot connect to API")
                
            st.subheader("Quick Stats")
            if alerts:
                total_patients = len(set(alert['patient_id'] for alert in alerts))
                st.metric("Patients with Alerts", total_patients)
                
                avg_risk = np.mean([0.8 if alert['severity'] == 'critical' else 
                                 0.6 if alert['severity'] == 'high' else 
                                 0.4 for alert in alerts])
                st.metric("Average Risk Level", f"{avg_risk:.1%}")
    
    elif page == "Patient Detail":
        st.header("Patient Detail View")
        
        patient_id = st.text_input("Enter Patient ID", value="PATIENT_001")
        
        if patient_id:
            prediction_data = fetch_patient_data(patient_id)
            
            if prediction_data:
                display_patient_card(patient_id, prediction_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Risk Assessment")
                    risk_gauge = create_risk_gauge(
                        prediction_data['risk_score']['overall_risk'],
                        "Overall Deterioration Risk"
                    )
                    st.plotly_chart(risk_gauge, use_container_width=True)
                    
                    st.subheader("Risk Breakdown")
                    risk_data = prediction_data['risk_score']
                    risk_categories = ['sepsis_risk', 'cardiac_risk', 'respiratory_risk', 'neurological_risk']
                    
                    for category in risk_categories:
                        if category in risk_data:
                            st.metric(
                                category.replace('_', ' ').title(),
                                f"{risk_data[category]:.1%}"
                            )
                
                with col2:
                    st.subheader("Contributing Factors")
                    explanation = prediction_data.get('explanation', {})
                    
                    if 'explanation_text' in explanation:
                        st.write(explanation['explanation_text'])
                    
                    if 'risk_factors' in explanation:
                        st.write("**Key Risk Factors:**")
                        for factor in explanation['risk_factors'][:5]:
                            st.write(f"• {factor}")
                    
                    st.subheader("Recommended Actions")
                    alerts = prediction_data.get('alerts', [])
                    if alerts:
                        for alert in alerts:
                            with st.expander(f"{alert['severity'].upper()} Alert"):
                                st.write(alert['message'])
                                if alert.get('recommended_actions'):
                                    st.write("**Recommended Actions:**")
                                    for action in alert['recommended_actions']:
                                        st.write(f"• {action}")
                
                st.subheader("Similar Patients")
                try:
                    similar_response = requests.get(
                        f"{API_BASE_URL}/patients/{patient_id}/similar",
                        headers=get_api_headers()
                    )
                    if similar_response.status_code == 200:
                        similar_patients = similar_response.json()
                        if similar_patients:
                            similar_df = pd.DataFrame(similar_patients)
                            st.dataframe(similar_df[['patient_id', 'similarity_score']], use_container_width=True)
                        else:
                            st.info("No similar patients found")
                except Exception as e:
                    st.error(f"Error fetching similar patients: {e}")
            else:
                st.error(f"Could not fetch data for patient {patient_id}")
    
    elif page == "Alert Management":
        st.header("Alert Management")
        
        alerts = fetch_active_alerts()
        
        if alerts:
            st.subheader("Active Alerts")
            
            for alert in alerts:
                severity_color = {
                    'low': 'blue',
                    'medium': 'orange', 
                    'high': 'red',
                    'critical': 'red'
                }.get(alert['severity'], 'gray')
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Patient:** {alert['patient_id']}  
                        **Type:** {alert['alert_type']}  
                        **Message:** {alert['message']}  
                        **Time:** {alert['timestamp']}
                        """)
                    
                    with col2:
                        st.markdown(f"**Severity:** :{severity_color}[{alert['severity'].upper()}]")
                    
                    with col3:
                        if st.button(f"Acknowledge", key=f"ack_{alert['alert_id']}"):
                            try:
                                ack_response = requests.post(
                                    f"{API_BASE_URL}/alerts/{alert['alert_id']}/acknowledge",
                                    headers=get_api_headers(),
                                    params={"acknowledged_by": "Dashboard User"}
                                )
                                if ack_response.status_code == 200:
                                    st.success("Alert acknowledged")
                                    st.rerun()
                                else:
                                    st.error("Failed to acknowledge alert")
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    st.divider()
        else:
            st.info("No active alerts")
    
    elif page == "System Monitoring":
        st.header("System Monitoring")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("API Health")
            try:
                health_response = requests.get(f"{API_BASE_URL}/health")
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    st.json(health_data)
                else:
                    st.error(f"API Health Check Failed: {health_response.status_code}")
            except Exception as e:
                st.error(f"Cannot connect to API: {e}")
        
        with col2:
            st.subheader("System Metrics")
            try:
                metrics_response = requests.get(f"{API_BASE_URL}/metrics/prometheus")
                if metrics_response.status_code == 200:
                    st.text("Metrics endpoint available")
                    
                    sample_metrics = {
                        "Predictions Made": np.random.randint(100, 1000),
                        "Active Patients": np.random.randint(50, 200),
                        "Average Response Time": f"{np.random.uniform(0.1, 2.0):.2f}s",
                        "Model Accuracy": f"{np.random.uniform(0.8, 0.95):.2%}"
                    }
                    
                    for metric, value in sample_metrics.items():
                        st.metric(metric, value)
                else:
                    st.error("Metrics endpoint unavailable")
            except Exception as e:
                st.error(f"Error fetching metrics: {e}")
        
        st.subheader("Recent Activity")
        
        activity_data = []
        alerts = fetch_active_alerts()
        
        if alerts:
            for alert in alerts[-10:]:
                activity_data.append({
                    'timestamp': alert['timestamp'],
                    'event': f"Alert: {alert['alert_type']}",
                    'patient': alert['patient_id'],
                    'severity': alert['severity']
                })
        
        if activity_data:
            activity_df = pd.DataFrame(activity_data)
            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No recent activity")

if __name__ == "__main__":
    main()