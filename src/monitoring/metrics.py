import time
from typing import Dict, List, Any
from collections import defaultdict, deque
import threading
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
        self.lock = threading.Lock()
        
        self.prometheus_counters = {
            'predictions_made': Counter('ews_predictions_total', 'Total number of predictions made'),
            'alerts_generated': Counter('ews_alerts_total', 'Total number of alerts generated'),
            'alerts_acknowledged': Counter('ews_alerts_acknowledged_total', 'Total number of alerts acknowledged'),
            'patients_created': Counter('ews_patients_created_total', 'Total number of patients created'),
            'vitals_ingested': Counter('ews_vitals_ingested_total', 'Total number of vital signs ingested'),
            'api_requests': Counter('ews_api_requests_total', 'Total number of API requests', ['method', 'endpoint'])
        }
        
        self.prometheus_histograms = {
            'prediction_duration_seconds': Histogram('ews_prediction_duration_seconds', 'Time taken for predictions'),
            'risk_scores': Histogram('ews_risk_scores', 'Distribution of risk scores', buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0])
        }
        
        self.prometheus_gauges = {
            'active_alerts': Gauge('ews_active_alerts', 'Number of active alerts'),
            'patients_monitored': Gauge('ews_patients_monitored', 'Number of patients being monitored'),
            'model_accuracy': Gauge('ews_model_accuracy', 'Current model accuracy')
        }
        
    def increment_counter(self, metric_name: str, value: int = 1, labels: Dict[str, str] = None):
        with self.lock:
            self.counters[metric_name] += value
            
            if metric_name in self.prometheus_counters:
                if labels:
                    self.prometheus_counters[metric_name].labels(**labels).inc(value)
                else:
                    self.prometheus_counters[metric_name].inc(value)
                    
    def record_histogram(self, metric_name: str, value: float):
        with self.lock:
            self.histograms[metric_name].append(value)
            
            if len(self.histograms[metric_name]) > 10000:
                self.histograms[metric_name] = self.histograms[metric_name][-5000:]
                
            if metric_name in self.prometheus_histograms:
                self.prometheus_histograms[metric_name].observe(value)
                
    def set_gauge(self, metric_name: str, value: float):
        with self.lock:
            self.gauges[metric_name] = value
            
            if metric_name in self.prometheus_gauges:
                self.prometheus_gauges[metric_name].set(value)
                
    def get_counter(self, metric_name: str) -> int:
        with self.lock:
            return self.counters.get(metric_name, 0)
            
    def get_histogram_stats(self, metric_name: str) -> Dict[str, float]:
        with self.lock:
            values = self.histograms.get(metric_name, [])
            
            if not values:
                return {'count': 0, 'mean': 0, 'min': 0, 'max': 0, 'p50': 0, 'p95': 0, 'p99': 0}
                
            import numpy as np
            
            return {
                'count': len(values),
                'mean': np.mean(values),
                'min': np.min(values),
                'max': np.max(values),
                'p50': np.percentile(values, 50),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99)
            }
            
    def get_gauge(self, metric_name: str) -> float:
        with self.lock:
            return self.gauges.get(metric_name, 0.0)
            
    def generate_prometheus_metrics(self) -> str:
        return generate_latest()
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        with self.lock:
            summary = {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {}
            }
            
            for metric_name in self.histograms:
                summary['histograms'][metric_name] = self.get_histogram_stats(metric_name)
                
            return summary

class ModelPerformanceTracker:
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.predictions = deque(maxlen=window_size)
        self.ground_truth = deque(maxlen=window_size)
        self.lock = threading.Lock()
        
    def record_prediction(self, prediction: float, actual: float = None):
        with self.lock:
            self.predictions.append({
                'timestamp': time.time(),
                'prediction': prediction,
                'actual': actual
            })
            
    def calculate_metrics(self) -> Dict[str, float]:
        with self.lock:
            if not self.predictions:
                return {}
                
            import numpy as np
            from sklearn.metrics import roc_auc_score, mean_squared_error
            
            valid_pairs = [(p['prediction'], p['actual']) 
                          for p in self.predictions 
                          if p['actual'] is not None]
            
            if len(valid_pairs) < 10:
                return {'sample_size': len(valid_pairs)}
                
            predictions, actuals = zip(*valid_pairs)
            
            metrics = {
                'sample_size': len(valid_pairs),
                'mean_prediction': np.mean(predictions),
                'std_prediction': np.std(predictions),
                'rmse': np.sqrt(mean_squared_error(actuals, predictions))
            }
            
            try:
                if len(set(actuals)) > 1:
                    metrics['auc'] = roc_auc_score(actuals, predictions)
            except:
                pass
                
            return metrics

class AlertingSystem:
    def __init__(self):
        self.alert_rules = []
        self.alert_history = deque(maxlen=1000)
        
    def add_alert_rule(self, name: str, condition_func, message: str, severity: str = "warning"):
        self.alert_rules.append({
            'name': name,
            'condition': condition_func,
            'message': message,
            'severity': severity
        })
        
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts = []
        
        for rule in self.alert_rules:
            try:
                if rule['condition'](metrics):
                    alert = {
                        'name': rule['name'],
                        'message': rule['message'],
                        'severity': rule['severity'],
                        'timestamp': time.time(),
                        'metrics_snapshot': metrics
                    }
                    alerts.append(alert)
                    self.alert_history.append(alert)
                    logger.warning(f"Alert triggered: {rule['name']} - {rule['message']}")
            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {e}")
                
        return alerts

class HealthChecker:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.last_check_time = time.time()
        self.alerting_system = AlertingSystem()
        self._setup_default_alerts()
        
    def _setup_default_alerts(self):
        self.alerting_system.add_alert_rule(
            "high_prediction_latency",
            lambda m: m.get('histograms', {}).get('prediction_duration_seconds', {}).get('p95', 0) > 5.0,
            "Prediction latency P95 > 5 seconds",
            "warning"
        )
        
        self.alerting_system.add_alert_rule(
            "low_prediction_accuracy",
            lambda m: m.get('model_performance', {}).get('auc', 1.0) < 0.7,
            "Model AUC dropped below 0.7",
            "critical"
        )
        
        self.alerting_system.add_alert_rule(
            "too_many_high_risk_predictions",
            lambda m: m.get('histograms', {}).get('risk_scores', {}).get('p95', 0) > 0.9,
            "95th percentile of risk scores > 0.9",
            "warning"
        )
        
    def check_system_health(self) -> Dict[str, Any]:
        current_time = time.time()
        metrics_summary = self.metrics_collector.get_metrics_summary()
        
        health_status = {
            'status': 'healthy',
            'timestamp': current_time,
            'uptime_seconds': current_time - self.last_check_time,
            'metrics': metrics_summary,
            'alerts': []
        }
        
        alerts = self.alerting_system.check_alerts(metrics_summary)
        health_status['alerts'] = alerts
        
        if alerts:
            critical_alerts = [a for a in alerts if a['severity'] == 'critical']
            if critical_alerts:
                health_status['status'] = 'unhealthy'
            else:
                health_status['status'] = 'degraded'
                
        return health_status

class DataQualityMonitor:
    def __init__(self):
        self.data_quality_metrics = defaultdict(dict)
        
    def check_vital_signs_quality(self, vitals_data: Dict[str, Any]) -> Dict[str, Any]:
        quality_score = 1.0
        issues = []
        
        expected_vitals = ['heart_rate', 'blood_pressure_systolic', 'respiratory_rate', 'temperature', 'oxygen_saturation']
        
        missing_vitals = [v for v in expected_vitals if vitals_data.get(v) is None]
        if missing_vitals:
            quality_score -= 0.1 * len(missing_vitals)
            issues.append(f"Missing vital signs: {', '.join(missing_vitals)}")
            
        hr = vitals_data.get('heart_rate')
        if hr is not None and (hr < 30 or hr > 200):
            quality_score -= 0.2
            issues.append(f"Heart rate out of physiological range: {hr}")
            
        bp_sys = vitals_data.get('blood_pressure_systolic')
        if bp_sys is not None and (bp_sys < 50 or bp_sys > 250):
            quality_score -= 0.2
            issues.append(f"Blood pressure out of range: {bp_sys}")
            
        temp = vitals_data.get('temperature')
        if temp is not None and (temp < 30 or temp > 45):
            quality_score -= 0.2
            issues.append(f"Temperature out of range: {temp}")
            
        return {
            'quality_score': max(0, quality_score),
            'issues': issues,
            'completeness': 1 - (len(missing_vitals) / len(expected_vitals))
        }
        
    def aggregate_quality_metrics(self, patient_id: str, quality_data: Dict[str, Any]):
        if patient_id not in self.data_quality_metrics:
            self.data_quality_metrics[patient_id] = {
                'quality_scores': [],
                'issue_counts': defaultdict(int),
                'total_records': 0
            }
            
        patient_metrics = self.data_quality_metrics[patient_id]
        patient_metrics['quality_scores'].append(quality_data['quality_score'])
        patient_metrics['total_records'] += 1
        
        for issue in quality_data['issues']:
            patient_metrics['issue_counts'][issue] += 1
            
        if len(patient_metrics['quality_scores']) > 100:
            patient_metrics['quality_scores'] = patient_metrics['quality_scores'][-50:]
            
    def get_patient_quality_summary(self, patient_id: str) -> Dict[str, Any]:
        if patient_id not in self.data_quality_metrics:
            return {'error': 'No quality data available'}
            
        patient_metrics = self.data_quality_metrics[patient_id]
        quality_scores = patient_metrics['quality_scores']
        
        if not quality_scores:
            return {'error': 'No quality scores available'}
            
        import numpy as np
        
        return {
            'average_quality_score': np.mean(quality_scores),
            'latest_quality_score': quality_scores[-1],
            'total_records': patient_metrics['total_records'],
            'common_issues': dict(list(patient_metrics['issue_counts'].items())[:5])
        }