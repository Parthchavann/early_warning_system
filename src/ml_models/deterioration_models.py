import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer, AutoConfig
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_curve, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, List, Optional, Tuple, Any
import joblib
import mlflow
import mlflow.pytorch
import mlflow.sklearn
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TimeSeriesDataset(Dataset):
    def __init__(self, sequences: np.ndarray, labels: np.ndarray, sequence_length: int = 24):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.FloatTensor(labels)
        self.sequence_length = sequence_length
        
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

class LSTMDeteriorationModel(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        num_classes: int = 1
    ):
        super(LSTMDeteriorationModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=True
        )
        
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,
            num_heads=8,
            dropout=dropout
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, num_classes),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        batch_size = x.size(0)
        
        lstm_out, (hidden, cell) = self.lstm(x)
        
        lstm_out = lstm_out.transpose(0, 1)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        attn_out = attn_out.transpose(0, 1)
        
        final_hidden = attn_out[:, -1, :]
        
        output = self.classifier(final_hidden)
        return output

class MultiModalDeteriorationModel(nn.Module):
    def __init__(
        self,
        vitals_input_size: int,
        text_model_name: str = "emilyalsentzer/Bio_ClinicalBERT",
        hidden_size: int = 128,
        num_classes: int = 1
    ):
        super(MultiModalDeteriorationModel, self).__init__()
        
        self.vitals_encoder = LSTMDeteriorationModel(
            input_size=vitals_input_size,
            hidden_size=hidden_size,
            num_classes=hidden_size
        )
        
        self.text_encoder = AutoModel.from_pretrained(text_model_name)
        text_hidden_size = self.text_encoder.config.hidden_size
        
        self.fusion_layer = nn.Sequential(
            nn.Linear(hidden_size + text_hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes),
            nn.Sigmoid()
        )
        
    def forward(self, vitals_data, text_input_ids, text_attention_mask):
        vitals_features = self.vitals_encoder(vitals_data)
        
        text_outputs = self.text_encoder(
            input_ids=text_input_ids,
            attention_mask=text_attention_mask
        )
        text_features = text_outputs.pooler_output
        
        fused_features = torch.cat([vitals_features, text_features], dim=1)
        output = self.fusion_layer(fused_features)
        
        return output

class EnsemblePredictor:
    def __init__(self):
        self.models = {}
        self.weights = {}
        self.feature_importance = {}
        
    def add_model(self, name: str, model, weight: float = 1.0):
        self.models[name] = model
        self.weights[name] = weight
        
    def train_ensemble(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ):
        self.models['logistic'] = LogisticRegression(random_state=42, max_iter=1000)
        self.models['rf'] = RandomForestClassifier(n_estimators=100, random_state=42)
        self.models['gbm'] = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.models['xgb'] = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
        self.models['lgb'] = lgb.LGBMClassifier(random_state=42, verbose=-1)
        
        scores = {}
        
        for name, model in self.models.items():
            logger.info(f"Training {name} model...")
            
            model.fit(X_train, y_train)
            
            val_pred = model.predict_proba(X_val)[:, 1]
            val_score = roc_auc_score(y_val, val_pred)
            scores[name] = val_score
            
            logger.info(f"{name} validation AUC: {val_score:.4f}")
            
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[name] = dict(
                    zip(X_train.columns, model.feature_importances_)
                )
                
        total_score = sum(scores.values())
        self.weights = {name: score/total_score for name, score in scores.items()}
        
        logger.info(f"Model weights: {self.weights}")
        
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        predictions = []
        
        for name, model in self.models.items():
            if hasattr(model, 'predict_proba'):
                pred = model.predict_proba(X)[:, 1]
            else:
                pred = model.predict(X)
            predictions.append(pred * self.weights[name])
            
        ensemble_pred = np.sum(predictions, axis=0)
        return ensemble_pred
    
    def get_feature_importance(self) -> Dict[str, float]:
        combined_importance = {}
        
        for model_name, importance_dict in self.feature_importance.items():
            weight = self.weights[model_name]
            for feature, importance in importance_dict.items():
                if feature not in combined_importance:
                    combined_importance[feature] = 0
                combined_importance[feature] += importance * weight
                
        return dict(sorted(combined_importance.items(), key=lambda x: x[1], reverse=True))

class DeteriorationPredictor:
    def __init__(self):
        self.ensemble_model = EnsemblePredictor()
        self.lstm_model = None
        self.multimodal_model = None
        self.tokenizer = None
        self.feature_columns = None
        self.scaler = None
        self.is_trained = False
        
    def prepare_training_data(
        self,
        vitals_df: pd.DataFrame,
        outcomes_df: pd.DataFrame,
        notes_df: Optional[pd.DataFrame] = None,
        prediction_hours: int = 4
    ) -> Tuple[pd.DataFrame, pd.Series]:
        
        merged_data = []
        
        for patient_id in vitals_df['patient_id'].unique():
            patient_vitals = vitals_df[vitals_df['patient_id'] == patient_id].sort_values('timestamp')
            patient_outcomes = outcomes_df[outcomes_df['patient_id'] == patient_id]
            
            if patient_outcomes.empty:
                continue
                
            outcome_time = patient_outcomes['timestamp'].min()
            cutoff_time = outcome_time - timedelta(hours=prediction_hours)
            
            relevant_vitals = patient_vitals[patient_vitals['timestamp'] <= cutoff_time]
            
            if len(relevant_vitals) < 5:
                continue
                
            features = self._extract_features_for_patient(relevant_vitals, patient_id)
            features['patient_id'] = patient_id
            features['label'] = 1 if not patient_outcomes.empty else 0
            
            merged_data.append(features)
            
        training_df = pd.DataFrame(merged_data)
        
        feature_cols = [col for col in training_df.columns if col not in ['patient_id', 'label']]
        X = training_df[feature_cols].fillna(0)
        y = training_df['label']
        
        self.feature_columns = feature_cols
        
        return X, y
    
    def _extract_features_for_patient(self, vitals_df: pd.DataFrame, patient_id: str) -> Dict[str, float]:
        features = {}
        
        if vitals_df.empty:
            return features
            
        recent_vitals = vitals_df.tail(24)
        
        for col in ['heart_rate', 'blood_pressure_systolic', 'respiratory_rate', 'temperature', 'oxygen_saturation']:
            if col in recent_vitals.columns:
                values = recent_vitals[col].dropna()
                if not values.empty:
                    features[f'{col}_mean'] = values.mean()
                    features[f'{col}_std'] = values.std()
                    features[f'{col}_min'] = values.min()
                    features[f'{col}_max'] = values.max()
                    features[f'{col}_trend'] = self._calculate_trend(values)
                    
        features['ews_score_current'] = self._calculate_ews_score(recent_vitals.iloc[-1])
        features['ews_score_max'] = recent_vitals.apply(self._calculate_ews_score, axis=1).max()
        features['ews_score_mean'] = recent_vitals.apply(self._calculate_ews_score, axis=1).mean()
        
        deterioration_indicators = 0
        for col in ['heart_rate', 'respiratory_rate']:
            if col in recent_vitals.columns:
                trend = self._calculate_trend(recent_vitals[col].dropna())
                if abs(trend) > 1.0:
                    deterioration_indicators += 1
                    
        features['deterioration_indicators'] = deterioration_indicators
        
        return features
    
    def _calculate_trend(self, values: pd.Series) -> float:
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        return np.polyfit(x, values, 1)[0]
    
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
                
        return score
    
    def train(
        self,
        vitals_df: pd.DataFrame,
        outcomes_df: pd.DataFrame,
        notes_df: Optional[pd.DataFrame] = None,
        test_size: float = 0.2
    ):
        logger.info("Preparing training data...")
        X, y = self.prepare_training_data(vitals_df, outcomes_df, notes_df)
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        logger.info(f"Training on {len(X_train)} samples, validating on {len(X_val)} samples")
        logger.info(f"Positive samples: {y_train.sum()}/{len(y_train)} train, {y_val.sum()}/{len(y_val)} val")
        
        with mlflow.start_run(run_name="deterioration_prediction"):
            mlflow.log_params({
                'train_size': len(X_train),
                'val_size': len(X_val),
                'positive_ratio': y_train.mean(),
                'num_features': len(self.feature_columns)
            })
            
            self.ensemble_model.train_ensemble(X_train, y_train, X_val, y_val)
            
            val_pred = self.ensemble_model.predict_proba(X_val)
            val_auc = roc_auc_score(y_val, val_pred)
            
            mlflow.log_metric('val_auc', val_auc)
            
            precision, recall, _ = precision_recall_curve(y_val, val_pred)
            pr_auc = np.trapz(recall, precision)
            mlflow.log_metric('val_pr_auc', pr_auc)
            
            logger.info(f"Validation AUC: {val_auc:.4f}, PR-AUC: {pr_auc:.4f}")
            
            self.is_trained = True
            
    def predict_risk(
        self,
        vitals_df: pd.DataFrame,
        patient_id: str,
        notes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
            
        patient_vitals = vitals_df[vitals_df['patient_id'] == patient_id]
        
        if patient_vitals.empty:
            return {
                'risk_score': 0.1,
                'confidence': 0.0,
                'explanation': 'No vital signs data available'
            }
            
        features = self._extract_features_for_patient(patient_vitals, patient_id)
        feature_df = pd.DataFrame([features])[self.feature_columns].fillna(0)
        
        risk_score = self.ensemble_model.predict_proba(feature_df)[0]
        
        feature_importance = self.ensemble_model.get_feature_importance()
        
        explanation = self._generate_explanation(features, feature_importance)
        
        confidence = min(1.0, max(0.1, len(patient_vitals) / 24.0))
        
        return {
            'risk_score': float(risk_score),
            'confidence': float(confidence),
            'explanation': explanation,
            'contributing_factors': list(feature_importance.keys())[:5]
        }
    
    def _generate_explanation(
        self,
        features: Dict[str, float],
        feature_importance: Dict[str, float]
    ) -> str:
        
        explanations = []
        
        if features.get('ews_score_current', 0) >= 5:
            explanations.append("High Early Warning Score indicates clinical deterioration")
            
        if features.get('deterioration_indicators', 0) >= 2:
            explanations.append("Multiple vital signs showing concerning trends")
            
        if features.get('heart_rate_mean', 60) > 100:
            explanations.append("Elevated heart rate")
            
        if features.get('respiratory_rate_mean', 16) > 20:
            explanations.append("Increased respiratory rate")
            
        if not explanations:
            explanations.append("Risk assessment based on overall vital signs pattern")
            
        return "; ".join(explanations)
    
    def save_model(self, path: str):
        model_data = {
            'ensemble_model': self.ensemble_model,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, path)
        logger.info(f"Model saved to {path}")
        
    def load_model(self, path: str):
        model_data = joblib.load(path)
        self.ensemble_model = model_data['ensemble_model']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = model_data['is_trained']
        logger.info(f"Model loaded from {path}")