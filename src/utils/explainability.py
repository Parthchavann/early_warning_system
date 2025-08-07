import numpy as np
import pandas as pd
import shap
import lime
import lime.tabular
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime
import io
import base64

logger = logging.getLogger(__name__)

class ModelExplainer:
    def __init__(self, model, feature_names: List[str], training_data: Optional[pd.DataFrame] = None):
        self.model = model
        self.feature_names = feature_names
        self.training_data = training_data
        
        self.shap_explainer = None
        self.lime_explainer = None
        
        self._initialize_explainers()
    
    def _initialize_explainers(self):
        """Initialize SHAP and LIME explainers"""
        try:
            if hasattr(self.model, 'predict_proba'):
                self.shap_explainer = shap.Explainer(self.model.predict_proba, self.training_data)
            else:
                self.shap_explainer = shap.Explainer(self.model.predict, self.training_data)
            logger.info("SHAP explainer initialized")
        except Exception as e:
            logger.warning(f"Could not initialize SHAP explainer: {e}")
        
        try:
            if self.training_data is not None:
                self.lime_explainer = lime.tabular.LimeTabularExplainer(
                    self.training_data.values,
                    feature_names=self.feature_names,
                    class_names=['No Deterioration', 'Deterioration'],
                    mode='classification',
                    discretize_continuous=True
                )
                logger.info("LIME explainer initialized")
        except Exception as e:
            logger.warning(f"Could not initialize LIME explainer: {e}")
    
    def explain_prediction(
        self,
        patient_features: pd.DataFrame,
        method: str = "shap",
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate explanation for a single prediction"""
        
        if method.lower() == "shap" and self.shap_explainer:
            return self._shap_explanation(patient_features, patient_id)
        elif method.lower() == "lime" and self.lime_explainer:
            return self._lime_explanation(patient_features, patient_id)
        else:
            return self._fallback_explanation(patient_features, patient_id)
    
    def _shap_explanation(self, patient_features: pd.DataFrame, patient_id: Optional[str]) -> Dict[str, Any]:
        """Generate SHAP-based explanation"""
        try:
            shap_values = self.shap_explainer(patient_features)
            
            if len(shap_values.shape) == 3:
                shap_values = shap_values[:, :, 1]
            
            feature_importance = dict(zip(self.feature_names, shap_values[0].values))
            
            explanation = {
                'method': 'SHAP',
                'patient_id': patient_id,
                'feature_importance': feature_importance,
                'explanation_text': self._generate_explanation_text(feature_importance),
                'top_positive_factors': self._get_top_factors(feature_importance, positive=True),
                'top_negative_factors': self._get_top_factors(feature_importance, positive=False),
                'base_value': float(shap_values.base_values[0]) if hasattr(shap_values, 'base_values') else 0.0,
                'prediction_contribution': float(shap_values[0].values.sum()),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            return self._fallback_explanation(patient_features, patient_id)
    
    def _lime_explanation(self, patient_features: pd.DataFrame, patient_id: Optional[str]) -> Dict[str, Any]:
        """Generate LIME-based explanation"""
        try:
            instance = patient_features.iloc[0].values
            
            exp = self.lime_explainer.explain_instance(
                instance,
                self.model.predict_proba,
                num_features=len(self.feature_names),
                top_labels=2
            )
            
            feature_importance = dict(exp.as_list())
            
            explanation = {
                'method': 'LIME',
                'patient_id': patient_id,
                'feature_importance': feature_importance,
                'explanation_text': self._generate_explanation_text(feature_importance),
                'top_positive_factors': self._get_top_factors(feature_importance, positive=True),
                'top_negative_factors': self._get_top_factors(feature_importance, positive=False),
                'prediction_probability': float(exp.predict_proba[1]),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {e}")
            return self._fallback_explanation(patient_features, patient_id)
    
    def _fallback_explanation(self, patient_features: pd.DataFrame, patient_id: Optional[str]) -> Dict[str, Any]:
        """Generate basic rule-based explanation when SHAP/LIME unavailable"""
        
        feature_values = patient_features.iloc[0].to_dict()
        
        risk_factors = []
        protective_factors = []
        
        if 'ews_score_current' in feature_values:
            ews = feature_values['ews_score_current']
            if ews >= 7:
                risk_factors.append(f"Very high Early Warning Score ({ews})")
            elif ews >= 5:
                risk_factors.append(f"High Early Warning Score ({ews})")
            elif ews <= 2:
                protective_factors.append(f"Low Early Warning Score ({ews})")
        
        if 'heart_rate_mean' in feature_values:
            hr = feature_values['heart_rate_mean']
            if hr > 120:
                risk_factors.append(f"Tachycardia (HR: {hr:.0f})")
            elif hr < 50:
                risk_factors.append(f"Bradycardia (HR: {hr:.0f})")
            elif 60 <= hr <= 100:
                protective_factors.append("Normal heart rate")
        
        if 'respiratory_rate_mean' in feature_values:
            rr = feature_values['respiratory_rate_mean']
            if rr > 24:
                risk_factors.append(f"Tachypnea (RR: {rr:.0f})")
            elif rr < 10:
                risk_factors.append(f"Bradypnea (RR: {rr:.0f})")
        
        if 'temperature_mean' in feature_values:
            temp = feature_values['temperature_mean']
            if temp > 38.5:
                risk_factors.append(f"Fever ({temp:.1f}°C)")
            elif temp < 36:
                risk_factors.append(f"Hypothermia ({temp:.1f}°C)")
        
        if 'spo2_min' in feature_values:
            spo2 = feature_values['spo2_min']
            if spo2 < 90:
                risk_factors.append(f"Hypoxemia (SpO2: {spo2:.0f}%)")
        
        explanation_text = ""
        if risk_factors:
            explanation_text += f"Risk factors: {'; '.join(risk_factors)}. "
        if protective_factors:
            explanation_text += f"Protective factors: {'; '.join(protective_factors)}. "
        
        if not explanation_text:
            explanation_text = "Risk assessment based on overall vital signs pattern."
        
        return {
            'method': 'Rule-based',
            'patient_id': patient_id,
            'feature_importance': {},
            'explanation_text': explanation_text,
            'risk_factors': risk_factors,
            'protective_factors': protective_factors,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _get_top_factors(self, feature_importance: Dict[str, float], positive: bool = True, n: int = 5) -> List[Dict[str, Any]]:
        """Get top contributing factors"""
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1] if positive else -x[1],
            reverse=positive
        )
        
        top_factors = []
        for feature, importance in sorted_features[:n]:
            if (positive and importance > 0) or (not positive and importance < 0):
                top_factors.append({
                    'feature': feature,
                    'importance': importance,
                    'description': self._get_feature_description(feature)
                })
        
        return top_factors
    
    def _get_feature_description(self, feature_name: str) -> str:
        """Get human-readable description of feature"""
        descriptions = {
            'ews_score_current': 'Current Early Warning Score',
            'heart_rate_mean': 'Average Heart Rate',
            'blood_pressure_systolic_mean': 'Average Systolic Blood Pressure',
            'respiratory_rate_mean': 'Average Respiratory Rate',
            'temperature_mean': 'Average Temperature',
            'oxygen_saturation_mean': 'Average Oxygen Saturation',
            'age': 'Patient Age',
            'deterioration_indicators': 'Number of deteriorating vital signs',
            'sepsis_risk_score': 'Sepsis Risk Score',
            'time_since_last_normal': 'Time since last normal vitals'
        }
        
        return descriptions.get(feature_name, feature_name.replace('_', ' ').title())
    
    def _generate_explanation_text(self, feature_importance: Dict[str, float]) -> str:
        """Generate natural language explanation"""
        
        if not feature_importance:
            return "No specific feature importance available."
        
        top_positive = sorted(
            [(k, v) for k, v in feature_importance.items() if v > 0],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        top_negative = sorted(
            [(k, v) for k, v in feature_importance.items() if v < 0],
            key=lambda x: x[1]
        )[:3]
        
        explanation_parts = []
        
        if top_positive:
            positive_features = [self._get_feature_description(feat) for feat, _ in top_positive]
            explanation_parts.append(f"Key risk factors: {', '.join(positive_features)}")
        
        if top_negative:
            negative_features = [self._get_feature_description(feat) for feat, _ in top_negative]
            explanation_parts.append(f"Protective factors: {', '.join(negative_features)}")
        
        if not explanation_parts:
            explanation_parts.append("Risk assessment based on overall clinical pattern")
        
        return ". ".join(explanation_parts) + "."
    
    def create_explanation_visualization(
        self,
        explanation: Dict[str, Any],
        top_n: int = 10
    ) -> go.Figure:
        """Create visualization of explanation"""
        
        feature_importance = explanation.get('feature_importance', {})
        
        if not feature_importance:
            fig = go.Figure()
            fig.add_annotation(
                text="No feature importance data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:top_n]
        
        features, importances = zip(*sorted_features)
        features = [self._get_feature_description(f) for f in features]
        
        colors = ['red' if imp > 0 else 'blue' for imp in importances]
        
        fig = go.Figure(data=[
            go.Bar(
                y=features,
                x=importances,
                orientation='h',
                marker=dict(color=colors),
                text=[f'{imp:.3f}' for imp in importances],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title=f"Feature Importance - {explanation.get('method', 'Unknown')} Explanation",
            xaxis_title="Contribution to Risk Score",
            yaxis_title="Clinical Features",
            height=max(400, len(features) * 30),
            margin=dict(l=200)
        )
        
        return fig

class ClinicalExplanationGenerator:
    def __init__(self):
        self.clinical_rules = self._initialize_clinical_rules()
    
    def _initialize_clinical_rules(self) -> Dict[str, Any]:
        """Initialize clinical interpretation rules"""
        return {
            'ews_thresholds': {
                0: 'Normal - routine monitoring',
                1: 'Low risk - continue routine monitoring',
                2: 'Low risk - continue routine monitoring',
                3: 'Medium risk - increase monitoring frequency',
                4: 'Medium risk - increase monitoring frequency',
                5: 'High risk - urgent clinical review',
                6: 'High risk - urgent clinical review',
                7: 'Very high risk - emergency response'
            },
            'vital_ranges': {
                'heart_rate': {
                    'normal': (60, 100),
                    'tachycardia': (100, float('inf')),
                    'bradycardia': (0, 60)
                },
                'respiratory_rate': {
                    'normal': (12, 20),
                    'tachypnea': (20, float('inf')),
                    'bradypnea': (0, 12)
                },
                'temperature': {
                    'normal': (36.0, 37.5),
                    'fever': (37.5, float('inf')),
                    'hypothermia': (0, 36.0)
                },
                'oxygen_saturation': {
                    'normal': (95, 100),
                    'hypoxemia': (0, 95)
                }
            }
        }
    
    def generate_clinical_interpretation(
        self,
        patient_features: Dict[str, Any],
        risk_score: float,
        explanation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate clinical interpretation of the prediction"""
        
        interpretation = {
            'risk_level': self._categorize_risk(risk_score),
            'clinical_significance': self._assess_clinical_significance(patient_features, risk_score),
            'recommended_actions': self._generate_recommendations(patient_features, risk_score),
            'monitoring_parameters': self._suggest_monitoring_parameters(patient_features),
            'timeline': self._suggest_timeline(risk_score),
            'contraindications': self._check_contraindications(patient_features)
        }
        
        return interpretation
    
    def _categorize_risk(self, risk_score: float) -> Dict[str, Any]:
        """Categorize risk level based on score"""
        if risk_score >= 0.8:
            return {
                'level': 'CRITICAL',
                'description': 'High probability of deterioration within 4 hours',
                'urgency': 'Immediate intervention required'
            }
        elif risk_score >= 0.6:
            return {
                'level': 'HIGH',
                'description': 'Elevated risk of deterioration',
                'urgency': 'Urgent clinical review recommended'
            }
        elif risk_score >= 0.4:
            return {
                'level': 'MODERATE',
                'description': 'Moderate risk of deterioration',
                'urgency': 'Increased monitoring recommended'
            }
        else:
            return {
                'level': 'LOW',
                'description': 'Low risk of deterioration',
                'urgency': 'Continue routine monitoring'
            }
    
    def _assess_clinical_significance(
        self,
        patient_features: Dict[str, Any],
        risk_score: float
    ) -> str:
        """Assess clinical significance of the prediction"""
        
        significance_factors = []
        
        ews = patient_features.get('ews_score_current', 0)
        if ews >= 5:
            significance_factors.append(f"Early Warning Score of {ews} indicates clinical concern")
        
        if 'age' in patient_features:
            age = patient_features['age']
            if age >= 75:
                significance_factors.append("Advanced age increases vulnerability")
            elif age <= 18:
                significance_factors.append("Pediatric patient requires specialized monitoring")
        
        if 'comorbidity_count' in patient_features:
            comorbidities = patient_features['comorbidity_count']
            if comorbidities >= 3:
                significance_factors.append("Multiple comorbidities increase risk complexity")
        
        if risk_score >= 0.7 and not significance_factors:
            significance_factors.append("High risk score warrants immediate attention despite stable vitals")
        
        return "; ".join(significance_factors) if significance_factors else "Standard risk assessment"
    
    def _generate_recommendations(
        self,
        patient_features: Dict[str, Any],
        risk_score: float
    ) -> List[str]:
        """Generate clinical recommendations based on risk assessment"""
        
        recommendations = []
        
        if risk_score >= 0.8:
            recommendations.extend([
                "Consider ICU evaluation",
                "Notify attending physician immediately",
                "Increase vital sign monitoring to q15min",
                "Consider arterial blood gas analysis",
                "Review fluid balance and medication reconciliation"
            ])
        elif risk_score >= 0.6:
            recommendations.extend([
                "Increase monitoring frequency to q30min",
                "Clinical assessment within 1 hour",
                "Consider additional diagnostic tests",
                "Review medication administration times"
            ])
        elif risk_score >= 0.4:
            recommendations.extend([
                "Monitor vital signs q1h",
                "Clinical assessment within 4 hours",
                "Document any changes in patient condition"
            ])
        else:
            recommendations.append("Continue routine monitoring per hospital protocol")
        
        hr = patient_features.get('heart_rate_mean', 70)
        if hr > 120:
            recommendations.append("Investigate cause of tachycardia (pain, fever, hypovolemia)")
        elif hr < 50:
            recommendations.append("Evaluate for cardiac conduction abnormalities")
        
        temp = patient_features.get('temperature_mean', 37)
        if temp > 38.5:
            recommendations.append("Investigate fever source and consider sepsis workup")
        
        spo2 = patient_features.get('spo2_min', 98)
        if spo2 < 90:
            recommendations.append("Assess oxygenation and consider respiratory support")
        
        return recommendations
    
    def _suggest_monitoring_parameters(self, patient_features: Dict[str, Any]) -> List[str]:
        """Suggest parameters to monitor closely"""
        
        parameters = ['Vital signs', 'Level of consciousness', 'Urine output']
        
        if patient_features.get('sepsis_risk_score', 0) > 0.5:
            parameters.extend(['Lactate levels', 'White blood cell count', 'Procalcitonin'])
        
        if patient_features.get('heart_rate_mean', 70) > 100:
            parameters.append('Cardiac rhythm')
        
        if patient_features.get('respiratory_rate_mean', 16) > 20:
            parameters.extend(['Oxygen saturation', 'Respiratory effort'])
        
        return parameters
    
    def _suggest_timeline(self, risk_score: float) -> Dict[str, str]:
        """Suggest timeline for interventions"""
        
        if risk_score >= 0.8:
            return {
                'immediate': 'Clinical assessment and stabilization',
                '15_minutes': 'Vital signs reassessment',
                '1_hour': 'Response to interventions evaluation',
                '4_hours': 'Comprehensive clinical review'
            }
        elif risk_score >= 0.6:
            return {
                'immediate': 'Clinical notification',
                '30_minutes': 'Vital signs reassessment',
                '2_hours': 'Clinical assessment',
                '6_hours': 'Progress evaluation'
            }
        else:
            return {
                '1_hour': 'Next vital signs check',
                '4_hours': 'Routine clinical assessment',
                '12_hours': 'Progress review'
            }
    
    def _check_contraindications(self, patient_features: Dict[str, Any]) -> List[str]:
        """Check for contraindications or special considerations"""
        
        contraindications = []
        
        age = patient_features.get('age', 50)
        if age >= 80:
            contraindications.append("Elderly patient - consider frailty and medication interactions")
        
        if 'high_risk_medications' in patient_features and patient_features['high_risk_medications']:
            contraindications.append("Patient on high-risk medications - review dosing and interactions")
        
        return contraindications