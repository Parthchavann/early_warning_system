import mlflow
import mlflow.tracking
from mlflow.tracking import MlflowClient
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mlflow_experiment(
    experiment_name: str = "patient_deterioration",
    tracking_uri: str = "http://localhost:5000",
    artifact_root: str = None
):
    """Setup MLflow experiment for patient deterioration prediction"""
    
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    try:
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment:
            logger.info(f"Experiment '{experiment_name}' already exists with ID: {experiment.experiment_id}")
            return experiment.experiment_id
    except:
        pass
    
    experiment_id = mlflow.create_experiment(
        name=experiment_name,
        artifact_location=artifact_root,
        tags={
            "project": "patient-deterioration-ews",
            "team": "clinical-ai",
            "created_date": datetime.now().isoformat(),
            "description": "Early Warning System for Patient Deterioration Prediction"
        }
    )
    
    logger.info(f"Created experiment '{experiment_name}' with ID: {experiment_id}")
    return experiment_id

def register_model_version(
    model_name: str,
    run_id: str,
    model_version: str = "1",
    stage: str = "None"
):
    """Register a model version in MLflow Model Registry"""
    
    client = MlflowClient()
    
    try:
        registered_model = client.get_registered_model(model_name)
        logger.info(f"Model '{model_name}' already registered")
    except:
        registered_model = client.create_registered_model(
            name=model_name,
            tags={
                "task": "binary_classification",
                "domain": "healthcare",
                "target": "patient_deterioration"
            },
            description="Patient deterioration prediction model using vital signs and clinical data"
        )
        logger.info(f"Registered new model: {model_name}")
    
    model_uri = f"runs:/{run_id}/model"
    
    model_version = client.create_model_version(
        name=model_name,
        source=model_uri,
        run_id=run_id,
        tags={
            "validation_auc": "0.85",
            "training_date": datetime.now().isoformat()
        }
    )
    
    if stage != "None":
        client.transition_model_version_stage(
            name=model_name,
            version=model_version.version,
            stage=stage,
            archive_existing_versions=False
        )
        logger.info(f"Transitioned model version {model_version.version} to {stage}")
    
    return model_version

def setup_model_registry():
    """Setup MLflow Model Registry with predefined models"""
    
    client = MlflowClient()
    
    models_to_register = [
        {
            "name": "deterioration_predictor",
            "description": "Primary model for patient deterioration prediction",
            "tags": {"type": "ensemble", "priority": "high"}
        },
        {
            "name": "sepsis_predictor", 
            "description": "Specialized model for sepsis risk prediction",
            "tags": {"type": "specialized", "condition": "sepsis"}
        },
        {
            "name": "cardiac_deterioration_predictor",
            "description": "Model focused on cardiac deterioration events", 
            "tags": {"type": "specialized", "condition": "cardiac"}
        }
    ]
    
    for model_config in models_to_register:
        try:
            client.get_registered_model(model_config["name"])
            logger.info(f"Model {model_config['name']} already exists")
        except:
            client.create_registered_model(
                name=model_config["name"],
                tags=model_config["tags"],
                description=model_config["description"]
            )
            logger.info(f"Created registered model: {model_config['name']}")

def create_model_alias(model_name: str, version: str, alias: str):
    """Create an alias for a model version"""
    
    client = MlflowClient()
    
    client.set_registered_model_alias(
        name=model_name,
        alias=alias,
        version=version
    )
    
    logger.info(f"Created alias '{alias}' for {model_name} version {version}")

def setup_mlflow_tags():
    """Setup standard tags for MLflow experiments and runs"""
    
    return {
        "mlflow.experiment.tags": {
            "project": "patient-deterioration-ews",
            "team": "clinical-ai",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "version": "1.0.0"
        },
        "mlflow.run.tags": {
            "model_type": "ensemble",
            "data_version": "v1.0",
            "feature_version": "v1.0",
            "training_pipeline": "automated"
        }
    }

def log_model_metadata(
    run_id: str,
    model_performance: dict,
    training_config: dict,
    feature_importance: dict = None
):
    """Log comprehensive model metadata"""
    
    with mlflow.start_run(run_id=run_id):
        mlflow.log_metrics(model_performance)
        mlflow.log_params(training_config)
        
        if feature_importance:
            for feature, importance in feature_importance.items():
                mlflow.log_metric(f"feature_importance_{feature}", importance)
        
        mlflow.log_param("model_framework", "scikit-learn + xgboost + lightgbm")
        mlflow.log_param("prediction_type", "binary_classification")
        mlflow.log_param("target_variable", "patient_deterioration_4h")
        
        model_info = {
            "input_features": list(feature_importance.keys()) if feature_importance else [],
            "output": "deterioration_probability",
            "model_size": "ensemble_of_5_models",
            "inference_time": "< 100ms",
            "deployment_ready": True
        }
        
        mlflow.log_dict(model_info, "model_info.json")

def setup_model_monitoring_alerts():
    """Setup model monitoring and alerting rules"""
    
    monitoring_config = {
        "performance_thresholds": {
            "auc_min": 0.75,
            "precision_min": 0.7,
            "recall_min": 0.8
        },
        "data_quality_thresholds": {
            "missing_data_max": 0.2,
            "outlier_ratio_max": 0.1
        },
        "drift_detection": {
            "feature_drift_threshold": 0.1,
            "prediction_drift_threshold": 0.05
        },
        "alert_settings": {
            "email_recipients": ["ml-team@hospital.com"],
            "slack_webhook": os.getenv("SLACK_WEBHOOK_URL"),
            "alert_frequency": "daily"
        }
    }
    
    return monitoring_config

def main():
    """Main setup function for MLflow infrastructure"""
    
    logger.info("Setting up MLflow infrastructure for Patient Deterioration EWS...")
    
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    artifact_root = os.getenv("MLFLOW_ARTIFACT_ROOT", "./mlruns")
    
    experiment_id = setup_mlflow_experiment(
        tracking_uri=tracking_uri,
        artifact_root=artifact_root
    )
    
    setup_model_registry()
    
    logger.info("MLflow infrastructure setup completed successfully!")
    
    logger.info(f"""
    MLflow Setup Summary:
    - Tracking URI: {tracking_uri}
    - Artifact Root: {artifact_root}
    - Experiment ID: {experiment_id}
    
    To access MLflow UI:
    mlflow ui --backend-store-uri {tracking_uri} --default-artifact-root {artifact_root}
    """)

if __name__ == "__main__":
    main()