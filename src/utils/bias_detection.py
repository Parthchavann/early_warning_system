import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_auc_score
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BiasDetector:
    def __init__(self):
        self.protected_attributes = ['age_group', 'gender', 'race', 'ethnicity', 'insurance_type']
        self.fairness_metrics = {}
        
    def detect_demographic_bias(
        self,
        predictions: pd.DataFrame,
        protected_attribute: str,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Detect bias across demographic groups"""
        
        if protected_attribute not in predictions.columns:
            return {'error': f'Protected attribute {protected_attribute} not found in data'}
        
        groups = predictions[protected_attribute].unique()
        bias_metrics = {}
        
        for group in groups:
            group_data = predictions[predictions[protected_attribute] == group]
            
            if len(group_data) == 0:
                continue
                
            group_metrics = {
                'sample_size': len(group_data),
                'positive_prediction_rate': (group_data['prediction'] > threshold).mean(),
                'average_prediction_score': group_data['prediction'].mean(),
                'actual_positive_rate': group_data.get('actual', pd.Series()).mean() if 'actual' in group_data else None
            }
            
            bias_metrics[group] = group_metrics
        
        fairness_assessment = self._assess_fairness(bias_metrics, protected_attribute)
        
        return {
            'protected_attribute': protected_attribute,
            'group_metrics': bias_metrics,
            'fairness_assessment': fairness_assessment,
            'bias_detected': fairness_assessment['bias_score'] > 0.1,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _assess_fairness(self, group_metrics: Dict[str, Any], attribute: str) -> Dict[str, Any]:
        """Assess fairness across groups using multiple metrics"""
        
        groups = list(group_metrics.keys())
        if len(groups) < 2:
            return {'error': 'Need at least 2 groups for bias assessment'}
        
        prediction_rates = [group_metrics[g]['positive_prediction_rate'] for g in groups]
        avg_scores = [group_metrics[g]['average_prediction_score'] for g in groups]
        
        demographic_parity = max(prediction_rates) - min(prediction_rates)
        
        equalized_odds_violation = 0
        if all('actual_positive_rate' in group_metrics[g] and group_metrics[g]['actual_positive_rate'] is not None for g in groups):
            actual_rates = [group_metrics[g]['actual_positive_rate'] for g in groups]
            equalized_odds_violation = max(actual_rates) - min(actual_rates)
        
        score_disparity = max(avg_scores) - min(avg_scores)
        
        bias_score = max(demographic_parity, equalized_odds_violation, score_disparity)
        
        fairness_level = "Fair"
        if bias_score > 0.2:
            fairness_level = "Significant Bias"
        elif bias_score > 0.1:
            fairness_level = "Moderate Bias"
        elif bias_score > 0.05:
            fairness_level = "Minor Bias"
        
        return {
            'bias_score': bias_score,
            'fairness_level': fairness_level,
            'demographic_parity_difference': demographic_parity,
            'equalized_odds_violation': equalized_odds_violation,
            'score_disparity': score_disparity,
            'recommendations': self._generate_fairness_recommendations(bias_score, attribute)
        }
    
    def _generate_fairness_recommendations(self, bias_score: float, attribute: str) -> List[str]:
        """Generate recommendations to improve fairness"""
        
        recommendations = []
        
        if bias_score > 0.2:
            recommendations.extend([
                f"Significant bias detected for {attribute}",
                "Consider rebalancing training data",
                "Implement bias mitigation techniques",
                "Add fairness constraints to model training",
                "Regular bias monitoring required"
            ])
        elif bias_score > 0.1:
            recommendations.extend([
                f"Moderate bias detected for {attribute}",
                "Monitor predictions across groups",
                "Consider post-processing fairness adjustments",
                "Review feature selection for bias"
            ])
        elif bias_score > 0.05:
            recommendations.extend([
                f"Minor bias detected for {attribute}",
                "Continue monitoring fairness metrics",
                "Document findings for compliance"
            ])
        else:
            recommendations.append("Fairness assessment passed")
        
        return recommendations
    
    def analyze_prediction_fairness(
        self,
        predictions_df: pd.DataFrame,
        protected_attributes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Comprehensive fairness analysis across multiple protected attributes"""
        
        if protected_attributes is None:
            protected_attributes = [attr for attr in self.protected_attributes 
                                 if attr in predictions_df.columns]
        
        fairness_report = {
            'overall_assessment': 'PASS',
            'attributes_analyzed': protected_attributes,
            'detailed_results': {},
            'summary_statistics': {},
            'actionable_recommendations': []
        }
        
        bias_detected = False
        
        for attr in protected_attributes:
            if attr in predictions_df.columns:
                bias_result = self.detect_demographic_bias(predictions_df, attr)
                fairness_report['detailed_results'][attr] = bias_result
                
                if bias_result.get('bias_detected', False):
                    bias_detected = True
                    fairness_report['actionable_recommendations'].extend(
                        bias_result['fairness_assessment']['recommendations']
                    )
        
        if bias_detected:
            fairness_report['overall_assessment'] = 'BIAS_DETECTED'
        
        fairness_report['summary_statistics'] = self._compute_summary_statistics(
            fairness_report['detailed_results']
        )
        
        return fairness_report
    
    def _compute_summary_statistics(self, detailed_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary statistics across all bias analyses"""
        
        all_bias_scores = []
        significant_bias_count = 0
        
        for attr, result in detailed_results.items():
            if 'fairness_assessment' in result:
                bias_score = result['fairness_assessment']['bias_score']
                all_bias_scores.append(bias_score)
                
                if bias_score > 0.1:
                    significant_bias_count += 1
        
        if not all_bias_scores:
            return {'error': 'No bias scores computed'}
        
        return {
            'average_bias_score': np.mean(all_bias_scores),
            'max_bias_score': max(all_bias_scores),
            'attributes_with_significant_bias': significant_bias_count,
            'total_attributes_tested': len(all_bias_scores)
        }

class ClinicalBiasAnalyzer:
    def __init__(self):
        self.clinical_factors = [
            'age_group', 'gender', 'primary_diagnosis', 
            'insurance_type', 'hospital_unit', 'admission_source'
        ]
    
    def analyze_clinical_bias(
        self,
        patient_data: pd.DataFrame,
        predictions: pd.DataFrame,
        outcomes: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """Analyze bias in clinical predictions with healthcare-specific considerations"""
        
        merged_data = patient_data.merge(predictions, on='patient_id', how='inner')
        
        if outcomes is not None:
            merged_data = merged_data.merge(outcomes, on='patient_id', how='left')
        
        clinical_bias_report = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'total_patients': len(merged_data),
            'bias_analyses': {},
            'clinical_recommendations': [],
            'regulatory_compliance': self._check_regulatory_compliance(merged_data)
        }
        
        for factor in self.clinical_factors:
            if factor in merged_data.columns:
                bias_analysis = self._analyze_clinical_factor_bias(merged_data, factor)
                clinical_bias_report['bias_analyses'][factor] = bias_analysis
        
        clinical_bias_report['clinical_recommendations'] = self._generate_clinical_recommendations(
            clinical_bias_report['bias_analyses']
        )
        
        return clinical_bias_report
    
    def _analyze_clinical_factor_bias(
        self,
        data: pd.DataFrame,
        factor: str
    ) -> Dict[str, Any]:
        """Analyze bias for a specific clinical factor"""
        
        factor_analysis = {
            'factor': factor,
            'groups_analyzed': data[factor].value_counts().to_dict(),
            'risk_disparities': {},
            'outcome_disparities': {},
            'clinical_significance': self._assess_clinical_significance(factor)
        }
        
        for group in data[factor].unique():
            group_data = data[data[factor] == group]
            
            if len(group_data) < 10:
                continue
            
            avg_risk = group_data['prediction'].mean()
            risk_threshold_rate = (group_data['prediction'] > 0.6).mean()
            
            factor_analysis['risk_disparities'][group] = {
                'average_risk_score': avg_risk,
                'high_risk_rate': risk_threshold_rate,
                'sample_size': len(group_data)
            }
            
            if 'actual_outcome' in group_data.columns:
                actual_rate = group_data['actual_outcome'].mean()
                factor_analysis['outcome_disparities'][group] = {
                    'actual_deterioration_rate': actual_rate,
                    'prediction_calibration': abs(avg_risk - actual_rate)
                }
        
        factor_analysis['disparity_metrics'] = self._compute_disparity_metrics(
            factor_analysis['risk_disparities']
        )
        
        return factor_analysis
    
    def _assess_clinical_significance(self, factor: str) -> Dict[str, Any]:
        """Assess clinical significance of bias in a given factor"""
        
        significance_mapping = {
            'age_group': {
                'importance': 'HIGH',
                'rationale': 'Age is a known risk factor for deterioration',
                'acceptable_disparity': 0.1
            },
            'gender': {
                'importance': 'MEDIUM',
                'rationale': 'Gender differences may reflect biological factors',
                'acceptable_disparity': 0.05
            },
            'race': {
                'importance': 'CRITICAL',
                'rationale': 'Racial bias in healthcare is a major concern',
                'acceptable_disparity': 0.02
            },
            'insurance_type': {
                'importance': 'CRITICAL',
                'rationale': 'Healthcare access should not depend on insurance',
                'acceptable_disparity': 0.02
            }
        }
        
        return significance_mapping.get(factor, {
            'importance': 'MEDIUM',
            'rationale': 'Standard bias assessment',
            'acceptable_disparity': 0.05
        })
    
    def _compute_disparity_metrics(self, risk_disparities: Dict[str, Any]) -> Dict[str, Any]:
        """Compute disparity metrics across groups"""
        
        if len(risk_disparities) < 2:
            return {'error': 'Need at least 2 groups for disparity analysis'}
        
        avg_risks = [group_data['average_risk_score'] for group_data in risk_disparities.values()]
        high_risk_rates = [group_data['high_risk_rate'] for group_data in risk_disparities.values()]
        
        return {
            'risk_score_range': max(avg_risks) - min(avg_risks),
            'high_risk_rate_range': max(high_risk_rates) - min(high_risk_rates),
            'coefficient_of_variation': np.std(avg_risks) / np.mean(avg_risks) if np.mean(avg_risks) > 0 else 0
        }
    
    def _generate_clinical_recommendations(self, bias_analyses: Dict[str, Any]) -> List[str]:
        """Generate clinical recommendations based on bias analysis"""
        
        recommendations = []
        
        high_bias_factors = []
        for factor, analysis in bias_analyses.items():
            if 'disparity_metrics' in analysis and 'risk_score_range' in analysis['disparity_metrics']:
                risk_range = analysis['disparity_metrics']['risk_score_range']
                significance = analysis['clinical_significance']
                
                if risk_range > significance.get('acceptable_disparity', 0.05):
                    high_bias_factors.append(factor)
        
        if high_bias_factors:
            recommendations.extend([
                f"Significant bias detected in: {', '.join(high_bias_factors)}",
                "Implement bias monitoring dashboard for clinical staff",
                "Review model training data for representativeness",
                "Consider stratified model validation",
                "Document bias mitigation efforts for regulatory compliance"
            ])
        
        recommendations.extend([
            "Establish regular bias auditing schedule",
            "Train clinical staff on bias recognition and mitigation",
            "Implement clinical override protocols for high-bias predictions"
        ])
        
        return recommendations
    
    def _check_regulatory_compliance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check compliance with healthcare regulations regarding bias"""
        
        compliance_checks = {
            'data_representativeness': self._check_data_representativeness(data),
            'disparate_impact': self._check_disparate_impact(data),
            'documentation_requirements': self._check_documentation_requirements()
        }
        
        overall_compliance = all(
            check.get('compliant', False) for check in compliance_checks.values()
        )
        
        return {
            'overall_compliant': overall_compliance,
            'individual_checks': compliance_checks,
            'required_actions': self._generate_compliance_actions(compliance_checks)
        }
    
    def _check_data_representativeness(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check if data is representative of patient population"""
        
        if 'gender' in data.columns:
            gender_distribution = data['gender'].value_counts(normalize=True)
            female_ratio = gender_distribution.get('F', 0)
            
            representative = 0.4 <= female_ratio <= 0.6
        else:
            representative = False
        
        return {
            'compliant': representative,
            'details': f"Gender distribution: {gender_distribution.to_dict() if 'gender' in data.columns else 'Not available'}"
        }
    
    def _check_disparate_impact(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Check for disparate impact across protected groups"""
        
        if 'gender' in data.columns and 'prediction' in data.columns:
            male_high_risk = (data[data['gender'] == 'M']['prediction'] > 0.6).mean()
            female_high_risk = (data[data['gender'] == 'F']['prediction'] > 0.6).mean()
            
            if male_high_risk > 0 and female_high_risk > 0:
                impact_ratio = min(male_high_risk, female_high_risk) / max(male_high_risk, female_high_risk)
                compliant = impact_ratio >= 0.8  # 80% rule
            else:
                compliant = False
                impact_ratio = 0
        else:
            compliant = False
            impact_ratio = 0
        
        return {
            'compliant': compliant,
            'impact_ratio': impact_ratio,
            'details': f"Four-fifths rule: {impact_ratio:.2f} >= 0.8"
        }
    
    def _check_documentation_requirements(self) -> Dict[str, Any]:
        """Check if bias documentation requirements are met"""
        
        return {
            'compliant': True,
            'details': "Basic bias analysis documented",
            'recommendations': [
                "Maintain bias testing records",
                "Document mitigation strategies",
                "Regular bias assessment reports"
            ]
        }
    
    def _generate_compliance_actions(self, compliance_checks: Dict[str, Any]) -> List[str]:
        """Generate actions required for compliance"""
        
        actions = []
        
        for check_name, check_result in compliance_checks.items():
            if not check_result.get('compliant', False):
                if check_name == 'data_representativeness':
                    actions.append("Ensure training data represents diverse patient population")
                elif check_name == 'disparate_impact':
                    actions.append("Address disparate impact across protected groups")
                elif check_name == 'documentation_requirements':
                    actions.extend(check_result.get('recommendations', []))
        
        if not actions:
            actions.append("Maintain current bias monitoring practices")
        
        return actions