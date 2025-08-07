import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import logging
import mlflow
import mlflow.sklearn
import mlflow.pytorch
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_curve, classification_report

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import DatabaseManager
from src.ml_models.deterioration_models import DeteriorationPredictor
from src.feature_engineering.feature_store import PatientFeatureExtractor
from src.monitoring.metrics import ModelPerformanceTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_synthetic_training_data(n_patients: int = 1000, n_vitals_per_patient: int = 100):
    """Generate synthetic training data for demonstration purposes"""
    np.random.seed(42)
    
    patients_data = []
    vitals_data = []
    outcomes_data = []
    
    for i in range(n_patients):
        patient_id = f"PATIENT_{i:04d}"
        
        age = np.random.randint(18, 90)
        gender = np.random.choice(['M', 'F'])
        
        deterioration_risk = np.random.random()
        
        patients_data.append({
            'patient_id': patient_id,
            'mrn': f"MRN_{i:06d}",
            'admission_date': datetime.utcnow() - timedelta(days=np.random.randint(1, 30)),
            'age': age,
            'gender': gender,
            'weight_kg': np.random.normal(70, 15),
            'height_cm': np.random.normal(170, 10),
            'primary_diagnosis': np.random.choice(['Pneumonia', 'Sepsis', 'CHF', 'COPD', 'MI']),
            'comorbidities': ['HTN', 'DM'] if np.random.random() > 0.5 else [],
            'medications': [],
            'allergies': []
        })
        
        for j in range(n_vitals_per_patient):
            base_time = datetime.utcnow() - timedelta(hours=n_vitals_per_patient - j)
            
            if deterioration_risk > 0.7:
                hr_base = 110 + np.random.normal(0, 20)
                bp_sys_base = 85 + np.random.normal(0, 15)
                rr_base = 25 + np.random.normal(0, 5)
                temp_base = 38.5 + np.random.normal(0, 1)
                spo2_base = 88 + np.random.normal(0, 5)
            elif deterioration_risk > 0.4:
                hr_base = 85 + np.random.normal(0, 15)
                bp_sys_base = 100 + np.random.normal(0, 20)
                rr_base = 18 + np.random.normal(0, 4)
                temp_base = 37.2 + np.random.normal(0, 0.8)
                spo2_base = 94 + np.random.normal(0, 3)
            else:
                hr_base = 70 + np.random.normal(0, 10)
                bp_sys_base = 120 + np.random.normal(0, 15)
                rr_base = 16 + np.random.normal(0, 3)
                temp_base = 36.8 + np.random.normal(0, 0.5)
                spo2_base = 98 + np.random.normal(0, 2)
            
            vitals_data.append({
                'patient_id': patient_id,
                'timestamp': base_time,
                'heart_rate': max(40, min(200, hr_base)),
                'blood_pressure_systolic': max(60, min(220, bp_sys_base)),
                'blood_pressure_diastolic': max(40, min(120, bp_sys_base * 0.7)),
                'respiratory_rate': max(8, min(40, rr_base)),
                'temperature': max(35, min(42, temp_base)),
                'oxygen_saturation': max(80, min(100, spo2_base)),
                'glasgow_coma_scale': 15 if deterioration_risk < 0.5 else np.random.randint(10, 15)
            })
        
        if deterioration_risk > 0.6 and np.random.random() > 0.3:
            outcome_time = datetime.utcnow() - timedelta(hours=np.random.randint(1, 12))
            outcomes_data.append({
                'patient_id': patient_id,
                'timestamp': outcome_time,
                'outcome_type': 'deterioration',
                'severity': 'high' if deterioration_risk > 0.8 else 'medium'
            })
    
    return pd.DataFrame(patients_data), pd.DataFrame(vitals_data), pd.DataFrame(outcomes_data)

def train_deterioration_model(
    vitals_df: pd.DataFrame,
    outcomes_df: pd.DataFrame,
    test_size: float = 0.2,
    model_name: str = "deterioration_predictor"
):
    logger.info("Starting model training...")
    
    with mlflow.start_run(run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.log_params({
            'model_type': 'ensemble',
            'test_size': test_size,
            'training_samples': len(vitals_df['patient_id'].unique()),
            'positive_outcomes': len(outcomes_df)
        })
        
        predictor = DeteriorationPredictor()
        
        predictor.train(vitals_df, outcomes_df, test_size=test_size)
        
        X, y = predictor.prepare_training_data(vitals_df, outcomes_df)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        val_predictions = predictor.ensemble_model.predict_proba(X_val)
        val_auc = roc_auc_score(y_val, val_predictions)
        
        precision, recall, _ = precision_recall_curve(y_val, val_predictions)
        pr_auc = np.trapz(recall, precision)
        
        mlflow.log_metrics({
            'val_auc': val_auc,
            'val_pr_auc': pr_auc,
            'train_size': len(X_train),
            'val_size': len(X_val),
            'positive_rate': y_train.mean()
        })
        
        logger.info(f"Validation AUC: {val_auc:.4f}")
        logger.info(f"Validation PR-AUC: {pr_auc:.4f}")
        
        model_path = f"models/{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
        os.makedirs("models", exist_ok=True)
        predictor.save_model(model_path)
        
        mlflow.log_artifact(model_path)
        
        performance_tracker = ModelPerformanceTracker()
        for pred, actual in zip(val_predictions, y_val):
            performance_tracker.record_prediction(pred, actual)
            
        performance_metrics = performance_tracker.calculate_metrics()
        mlflow.log_metrics(performance_metrics)
        
        feature_importance = predictor.ensemble_model.get_feature_importance()
        importance_df = pd.DataFrame([
            {'feature': k, 'importance': v} 
            for k, v in feature_importance.items()
        ]).sort_values('importance', ascending=False)
        
        importance_csv = f"feature_importance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        importance_df.to_csv(importance_csv, index=False)
        mlflow.log_artifact(importance_csv)
        
        logger.info("Top 10 most important features:")
        for _, row in importance_df.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        
        return predictor, val_auc, model_path

def evaluate_model_on_test_set(
    predictor: DeteriorationPredictor,
    test_vitals: pd.DataFrame,
    test_outcomes: pd.DataFrame
):
    logger.info("Evaluating model on test set...")
    
    test_patients = test_vitals['patient_id'].unique()[:50]
    
    predictions = []
    actuals = []
    
    for patient_id in test_patients:
        patient_vitals = test_vitals[test_vitals['patient_id'] == patient_id]
        
        if len(patient_vitals) < 10:
            continue
            
        prediction_result = predictor.predict_risk(patient_vitals, patient_id)
        risk_score = prediction_result['risk_score']
        
        has_outcome = len(test_outcomes[test_outcomes['patient_id'] == patient_id]) > 0
        
        predictions.append(risk_score)
        actuals.append(1 if has_outcome else 0)
    
    if len(predictions) > 10:
        test_auc = roc_auc_score(actuals, predictions)
        logger.info(f"Test AUC: {test_auc:.4f}")
        
        return {
            'test_auc': test_auc,
            'test_samples': len(predictions),
            'test_positive_rate': np.mean(actuals)
        }
    else:
        logger.warning("Not enough test samples for evaluation")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Train Patient Deterioration Model')
    parser.add_argument('--n-patients', type=int, default=1000, 
                       help='Number of synthetic patients to generate')
    parser.add_argument('--test-size', type=float, default=0.2,
                       help='Test set size (0.0 to 1.0)')
    parser.add_argument('--model-name', type=str, default='deterioration_predictor',
                       help='Model name for MLflow tracking')
    parser.add_argument('--mlflow-uri', type=str, default='http://localhost:5000',
                       help='MLflow tracking server URI')
    parser.add_argument('--use-real-data', action='store_true',
                       help='Use real data from database instead of synthetic')
    
    args = parser.parse_args()
    
    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment("patient_deterioration")
    
    if args.use_real_data:
        logger.info("Loading real data from database...")
        db_manager = DatabaseManager()
        
        with db_manager.get_session() as session:
            from src.models.database import VitalSignRecord, PatientRecord
            
            vitals_query = session.query(VitalSignRecord).all()
            patients_query = session.query(PatientRecord).all()
            
            if not vitals_query:
                logger.error("No vital signs data found in database")
                return
            
            vitals_data = [{
                'patient_id': v.patient_id,
                'timestamp': v.timestamp,
                'heart_rate': v.heart_rate,
                'blood_pressure_systolic': v.blood_pressure_systolic,
                'blood_pressure_diastolic': v.blood_pressure_diastolic,
                'respiratory_rate': v.respiratory_rate,
                'temperature': v.temperature,
                'oxygen_saturation': v.oxygen_saturation,
                'glasgow_coma_scale': v.glasgow_coma_scale
            } for v in vitals_query]
            
            vitals_df = pd.DataFrame(vitals_data)
            outcomes_df = pd.DataFrame()
            
    else:
        logger.info(f"Generating synthetic data for {args.n_patients} patients...")
        patients_df, vitals_df, outcomes_df = generate_synthetic_training_data(args.n_patients)
    
    logger.info(f"Training data: {len(vitals_df)} vital signs records")
    logger.info(f"Outcomes data: {len(outcomes_df)} deterioration events")
    
    predictor, val_auc, model_path = train_deterioration_model(
        vitals_df, outcomes_df, args.test_size, args.model_name
    )
    
    if not args.use_real_data:
        test_metrics = evaluate_model_on_test_set(predictor, vitals_df, outcomes_df)
        logger.info(f"Test metrics: {test_metrics}")
    
    logger.info(f"Model training completed successfully!")
    logger.info(f"Model saved to: {model_path}")
    logger.info(f"Validation AUC: {val_auc:.4f}")
    
    return predictor, model_path

if __name__ == "__main__":
    main()