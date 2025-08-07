import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from feast import FeatureStore, Feature, Entity, FeatureView, Field
from feast.types import Float32, Int64, String, UnixTimestamp
from feast.data_source import FileSource
import logging
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)

class PatientFeatureExtractor:
    def __init__(self):
        self.feature_definitions = self._define_feature_catalog()
        
    def _define_feature_catalog(self) -> Dict[str, Any]:
        return {
            "vital_signs": {
                "heart_rate_mean_1h": {"type": "continuous", "description": "Mean heart rate in last hour"},
                "heart_rate_std_1h": {"type": "continuous", "description": "Heart rate standard deviation in last hour"},
                "heart_rate_trend_6h": {"type": "continuous", "description": "Heart rate trend over 6 hours"},
                "bp_mean_1h": {"type": "continuous", "description": "Mean blood pressure in last hour"},
                "respiratory_rate_mean_1h": {"type": "continuous", "description": "Mean respiratory rate in last hour"},
                "temperature_max_1h": {"type": "continuous", "description": "Max temperature in last hour"},
                "spo2_min_1h": {"type": "continuous", "description": "Min oxygen saturation in last hour"},
                "gcs_current": {"type": "discrete", "description": "Current Glasgow Coma Scale"}
            },
            "derived_scores": {
                "ews_score_current": {"type": "discrete", "description": "Current Early Warning Score"},
                "ews_score_max_4h": {"type": "discrete", "description": "Max EWS in last 4 hours"},
                "sepsis_risk_score": {"type": "continuous", "description": "SEPSIS-3 derived risk score"},
                "shock_index": {"type": "continuous", "description": "Heart rate / SBP ratio"}
            },
            "temporal_patterns": {
                "vital_deterioration_6h": {"type": "binary", "description": "Any vital deteriorating in 6h"},
                "consecutive_abnormal_vitals": {"type": "discrete", "description": "Count of consecutive abnormal readings"},
                "time_since_last_normal": {"type": "continuous", "description": "Hours since last normal vitals"}
            },
            "lab_values": {
                "lactate_current": {"type": "continuous", "description": "Current lactate level"},
                "wbc_trend_24h": {"type": "continuous", "description": "White blood cell trend"},
                "creatinine_change_24h": {"type": "continuous", "description": "Creatinine change in 24h"},
                "hemoglobin_current": {"type": "continuous", "description": "Current hemoglobin"}
            },
            "patient_context": {
                "age_group": {"type": "categorical", "description": "Age group classification"},
                "los_days": {"type": "continuous", "description": "Length of stay in days"},
                "comorbidity_count": {"type": "discrete", "description": "Number of comorbidities"},
                "high_risk_medications": {"type": "binary", "description": "Taking high-risk medications"}
            }
        }
    
    def extract_vital_features(self, vitals_df: pd.DataFrame, patient_id: str) -> Dict[str, float]:
        patient_vitals = vitals_df[vitals_df['patient_id'] == patient_id].copy()
        
        if patient_vitals.empty:
            return {}
            
        patient_vitals = patient_vitals.sort_values('timestamp')
        features = {}
        
        now = datetime.utcnow()
        
        last_1h = patient_vitals[patient_vitals['timestamp'] >= now - timedelta(hours=1)]
        last_6h = patient_vitals[patient_vitals['timestamp'] >= now - timedelta(hours=6)]
        
        if not last_1h.empty:
            features['heart_rate_mean_1h'] = last_1h['heart_rate'].mean()
            features['heart_rate_std_1h'] = last_1h['heart_rate'].std()
            features['bp_mean_1h'] = (last_1h['blood_pressure_systolic'].mean() + 
                                    last_1h['blood_pressure_diastolic'].mean()) / 2
            features['respiratory_rate_mean_1h'] = last_1h['respiratory_rate'].mean()
            features['temperature_max_1h'] = last_1h['temperature'].max()
            features['spo2_min_1h'] = last_1h['oxygen_saturation'].min()
            features['gcs_current'] = last_1h['glasgow_coma_scale'].iloc[-1] if not last_1h.empty else 15
            
        if len(last_6h) >= 2:
            features['heart_rate_trend_6h'] = self._calculate_trend(
                last_6h, 'heart_rate', 'timestamp'
            )
            
        features.update(self._calculate_derived_scores(patient_vitals))
        features.update(self._calculate_temporal_patterns(patient_vitals))
        
        return {k: v for k, v in features.items() if not pd.isna(v)}
    
    def _calculate_trend(self, df: pd.DataFrame, value_col: str, time_col: str) -> float:
        if len(df) < 2:
            return 0.0
            
        x = (df[time_col] - df[time_col].min()).dt.total_seconds() / 3600
        y = df[value_col].fillna(method='ffill')
        
        if len(y.dropna()) < 2:
            return 0.0
            
        return np.polyfit(x, y, 1)[0]
    
    def _calculate_derived_scores(self, vitals_df: pd.DataFrame) -> Dict[str, float]:
        features = {}
        
        if vitals_df.empty:
            return features
            
        latest = vitals_df.iloc[-1]
        
        ews_score = self._calculate_ews_score(latest)
        features['ews_score_current'] = ews_score
        
        last_4h = vitals_df[vitals_df['timestamp'] >= datetime.utcnow() - timedelta(hours=4)]
        if not last_4h.empty:
            ews_scores = [self._calculate_ews_score(row) for _, row in last_4h.iterrows()]
            features['ews_score_max_4h'] = max(ews_scores)
            
        if pd.notna(latest['heart_rate']) and pd.notna(latest['blood_pressure_systolic']):
            features['shock_index'] = latest['heart_rate'] / latest['blood_pressure_systolic']
            
        features['sepsis_risk_score'] = self._calculate_sepsis_risk(latest)
        
        return features
    
    def _calculate_ews_score(self, vitals_row) -> int:
        score = 0
        
        hr = vitals_row.get('heart_rate')
        if pd.notna(hr):
            if hr < 40 or hr > 130:
                score += 3
            elif hr < 50 or hr > 110:
                score += 2
            elif hr < 60 or hr > 100:
                score += 1
                
        rr = vitals_row.get('respiratory_rate')
        if pd.notna(rr):
            if rr < 8 or rr > 30:
                score += 3
            elif rr < 10 or rr > 25:
                score += 2
            elif rr < 12 or rr > 20:
                score += 1
                
        temp = vitals_row.get('temperature')
        if pd.notna(temp):
            if temp < 35.5 or temp > 38.5:
                score += 3
            elif temp < 36.0 or temp > 38.0:
                score += 2
            elif temp < 36.5 or temp > 37.5:
                score += 1
                
        spo2 = vitals_row.get('oxygen_saturation')
        if pd.notna(spo2):
            if spo2 < 85:
                score += 3
            elif spo2 < 90:
                score += 2
            elif spo2 < 94:
                score += 1
                
        bp_sys = vitals_row.get('blood_pressure_systolic')
        if pd.notna(bp_sys):
            if bp_sys < 90 or bp_sys > 180:
                score += 3
            elif bp_sys < 100 or bp_sys > 160:
                score += 2
            elif bp_sys < 110 or bp_sys > 140:
                score += 1
                
        gcs = vitals_row.get('glasgow_coma_scale')
        if pd.notna(gcs):
            if gcs < 9:
                score += 3
            elif gcs < 12:
                score += 2
            elif gcs < 15:
                score += 1
                
        return score
    
    def _calculate_sepsis_risk(self, vitals_row) -> float:
        qsofa_score = 0
        
        rr = vitals_row.get('respiratory_rate')
        if pd.notna(rr) and rr >= 22:
            qsofa_score += 1
            
        bp_sys = vitals_row.get('blood_pressure_systolic')
        if pd.notna(bp_sys) and bp_sys <= 100:
            qsofa_score += 1
            
        gcs = vitals_row.get('glasgow_coma_scale')
        if pd.notna(gcs) and gcs < 15:
            qsofa_score += 1
            
        if qsofa_score >= 2:
            return 0.8
        elif qsofa_score == 1:
            return 0.4
        else:
            return 0.1
    
    def _calculate_temporal_patterns(self, vitals_df: pd.DataFrame) -> Dict[str, float]:
        features = {}
        
        if vitals_df.empty:
            return features
            
        last_6h = vitals_df[vitals_df['timestamp'] >= datetime.utcnow() - timedelta(hours=6)]
        
        deterioration_count = 0
        for col in ['heart_rate', 'respiratory_rate', 'temperature']:
            if col in last_6h.columns:
                trend = self._calculate_trend(last_6h, col, 'timestamp')
                if abs(trend) > 0.5:
                    deterioration_count += 1
                    
        features['vital_deterioration_6h'] = 1 if deterioration_count >= 2 else 0
        
        consecutive_abnormal = 0
        for _, row in vitals_df.tail(10).iterrows():
            ews = self._calculate_ews_score(row)
            if ews >= 3:
                consecutive_abnormal += 1
            else:
                break
                
        features['consecutive_abnormal_vitals'] = consecutive_abnormal
        
        normal_vitals = vitals_df.apply(lambda x: self._calculate_ews_score(x) < 3, axis=1)
        if normal_vitals.any():
            last_normal_idx = normal_vitals.iloc[::-1].idxmax()
            time_diff = (datetime.utcnow() - vitals_df.loc[last_normal_idx, 'timestamp']).total_seconds() / 3600
            features['time_since_last_normal'] = time_diff
        else:
            features['time_since_last_normal'] = 24.0
            
        return features
    
    def extract_lab_features(self, lab_df: pd.DataFrame, patient_id: str) -> Dict[str, float]:
        patient_labs = lab_df[lab_df['patient_id'] == patient_id].copy()
        features = {}
        
        if patient_labs.empty:
            return features
            
        now = datetime.utcnow()
        recent_labs = patient_labs[patient_labs['timestamp'] >= now - timedelta(hours=24)]
        
        for test_name in ['lactate', 'wbc', 'creatinine', 'hemoglobin']:
            test_data = recent_labs[recent_labs['test_name'].str.lower().str.contains(test_name, na=False)]
            
            if not test_data.empty:
                latest_value = test_data.sort_values('timestamp').iloc[-1]['value']
                
                if test_name == 'lactate':
                    features['lactate_current'] = latest_value
                elif test_name == 'hemoglobin':
                    features['hemoglobin_current'] = latest_value
                    
                if len(test_data) >= 2:
                    trend = self._calculate_trend(test_data, 'value', 'timestamp')
                    
                    if test_name == 'wbc':
                        features['wbc_trend_24h'] = trend
                    elif test_name == 'creatinine':
                        old_value = test_data.sort_values('timestamp').iloc[0]['value']
                        features['creatinine_change_24h'] = latest_value - old_value
                        
        return features
    
    def extract_patient_context_features(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        features = {}
        
        age = patient_data.get('age', 50)
        if age < 18:
            features['age_group'] = 'pediatric'
        elif age < 65:
            features['age_group'] = 'adult'
        else:
            features['age_group'] = 'elderly'
            
        admission_date = patient_data.get('admission_date')
        if admission_date:
            los = (datetime.utcnow() - admission_date).days
            features['los_days'] = los
        else:
            features['los_days'] = 0
            
        comorbidities = patient_data.get('comorbidities', [])
        features['comorbidity_count'] = len(comorbidities)
        
        medications = patient_data.get('medications', [])
        high_risk_meds = ['warfarin', 'heparin', 'insulin', 'digoxin', 'lithium']
        has_high_risk = any(
            any(med.lower() in drug.get('name', '').lower() for med in high_risk_meds)
            for drug in medications
        )
        features['high_risk_medications'] = 1 if has_high_risk else 0
        
        return features

class FeaturePreprocessor:
    def __init__(self):
        self.scalers = {}
        self.imputers = {}
        self.feature_importance = {}
        
    def fit_preprocessors(self, feature_df: pd.DataFrame):
        numeric_features = feature_df.select_dtypes(include=[np.number]).columns
        
        for feature in numeric_features:
            if feature_df[feature].isna().sum() > 0:
                self.imputers[feature] = SimpleImputer(strategy='median')
                self.imputers[feature].fit(feature_df[[feature]])
                
            self.scalers[feature] = RobustScaler()
            cleaned_values = feature_df[feature].fillna(feature_df[feature].median())
            self.scalers[feature].fit(cleaned_values.values.reshape(-1, 1))
            
        logger.info(f"Fitted preprocessors for {len(numeric_features)} features")
        
    def transform_features(self, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        transformed = feature_dict.copy()
        
        for feature, value in feature_dict.items():
            if pd.isna(value) and feature in self.imputers:
                value = self.imputers[feature].transform([[value]])[0, 0]
                transformed[feature] = value
                
            if feature in self.scalers and not pd.isna(value):
                scaled_value = self.scalers[feature].transform([[value]])[0, 0]
                transformed[f"{feature}_scaled"] = scaled_value
                
        return transformed