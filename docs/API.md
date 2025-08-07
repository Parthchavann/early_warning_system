# API Reference

This document provides comprehensive documentation for the Patient Deterioration Early Warning System API.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL & Versioning](#base-url--versioning)
3. [Request/Response Format](#requestresponse-format)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Patient Management](#patient-management)
7. [Vital Signs & Clinical Data](#vital-signs--clinical-data)
8. [Prediction & Risk Assessment](#prediction--risk-assessment)
9. [Alert Management](#alert-management)
10. [Analytics & Insights](#analytics--insights)
11. [System Information](#system-information)
12. [SDK & Code Examples](#sdk--code-examples)

## Authentication

### API Key Authentication

All API requests require authentication using an API key in the Authorization header:

```http
Authorization: Bearer your-api-key-here
```

### Example Authentication

```bash
curl -H \"Authorization: Bearer your-api-key\" \
     https://api.patient-ews.com/health
```

```python
import requests

headers = {\"Authorization\": \"Bearer your-api-key\"}
response = requests.get(\"https://api.patient-ews.com/health\", headers=headers)
```

## Base URL & Versioning

**Base URL:** `https://api.patient-ews.com`

**Current Version:** `v1` (implied in all endpoints)

**API Endpoint Format:** `{base_url}/{resource}`

## Request/Response Format

### Content Type
- **Request Content-Type:** `application/json`
- **Response Content-Type:** `application/json`

### Standard Response Format

```json
{
  \"status\": \"success|error\",
  \"data\": {},
  \"message\": \"Human-readable message\",
  \"timestamp\": \"2024-01-01T12:00:00Z\",
  \"request_id\": \"uuid-string\"
}
```

### Date/Time Format
All timestamps use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

## Error Handling

### HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Invalid or missing API key |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Response Format

```json
{
  \"status\": \"error\",
  \"error\": {
    \"code\": \"VALIDATION_ERROR\",
    \"message\": \"Invalid patient data provided\",
    \"details\": {
      \"field\": \"age\",
      \"reason\": \"Age must be between 0 and 150\"
    }
  },
  \"timestamp\": \"2024-01-01T12:00:00Z\",
  \"request_id\": \"req_123456\"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | API key is invalid or expired |
| `PATIENT_NOT_FOUND` | Requested patient does not exist |
| `VALIDATION_ERROR` | Request data validation failed |
| `MODEL_UNAVAILABLE` | ML model is temporarily unavailable |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `INSUFFICIENT_DATA` | Not enough data for prediction |

## Rate Limiting

### Rate Limits

| Endpoint Category | Limit | Window |
|-------------------|-------|---------|
| Patient Management | 1000/hour | Rolling hour |
| Vital Signs | 10000/hour | Rolling hour |  
| Predictions | 500/hour | Rolling hour |
| Analytics | 100/hour | Rolling hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Patient Management

### Create Patient

Create a new patient record in the system.

**Endpoint:** `POST /patients`

**Request Body:**
```json
{
  \"patient_id\": \"PATIENT_001\",
  \"mrn\": \"MRN_123456\",
  \"admission_date\": \"2024-01-01T10:00:00Z\",
  \"age\": 65,
  \"gender\": \"M\",
  \"weight_kg\": 80.5,
  \"height_cm\": 175,
  \"primary_diagnosis\": \"Pneumonia\",
  \"comorbidities\": [\"Hypertension\", \"Diabetes Type 2\"],
  \"medications\": [
    {
      \"name\": \"Lisinopril\",
      \"dosage\": \"10mg\",
      \"frequency\": \"daily\"
    }
  ],
  \"allergies\": [\"Penicillin\"]
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"patient_id\": \"PATIENT_001\",
    \"created_at\": \"2024-01-01T12:00:00Z\"
  },
  \"message\": \"Patient created successfully\"
}
```

**Example:**
```python
import requests

patient_data = {
    \"patient_id\": \"PATIENT_001\",
    \"mrn\": \"MRN_123456\",
    \"admission_date\": \"2024-01-01T10:00:00Z\",
    \"age\": 65,
    \"gender\": \"M\",
    \"primary_diagnosis\": \"Pneumonia\"
}

response = requests.post(
    \"https://api.patient-ews.com/patients\",
    json=patient_data,
    headers={\"Authorization\": \"Bearer your-api-key\"}
)

print(response.json())
```

### Get Patient Details

Retrieve detailed information about a specific patient.

**Endpoint:** `GET /patients/{patient_id}`

**Path Parameters:**
- `patient_id` (string): Unique patient identifier

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"patient_id\": \"PATIENT_001\",
    \"mrn\": \"MRN_123456\",
    \"admission_date\": \"2024-01-01T10:00:00Z\",
    \"age\": 65,
    \"gender\": \"M\",
    \"primary_diagnosis\": \"Pneumonia\",
    \"last_vitals\": \"2024-01-01T14:30:00Z\",
    \"current_risk_score\": 0.45,
    \"active_alerts\": 0
  }
}
```

### Update Patient

Update existing patient information.

**Endpoint:** `PUT /patients/{patient_id}`

**Request Body:** (Partial updates supported)
```json
{
  \"weight_kg\": 82.0,
  \"medications\": [
    {
      \"name\": \"Lisinopril\",
      \"dosage\": \"20mg\",
      \"frequency\": \"daily\"
    }
  ]
}
```

### Delete Patient

Remove a patient from the system (soft delete).

**Endpoint:** `DELETE /patients/{patient_id}`

**Response:**
```json
{
  \"status\": \"success\",
  \"message\": \"Patient marked as inactive\"
}
```

## Vital Signs & Clinical Data

### Add Vital Signs

Submit vital signs data for a patient.

**Endpoint:** `POST /patients/{patient_id}/vitals`

**Request Body:**
```json
{
  \"timestamp\": \"2024-01-01T14:30:00Z\",
  \"heart_rate\": 95,
  \"blood_pressure_systolic\": 140,
  \"blood_pressure_diastolic\": 85,
  \"respiratory_rate\": 18,
  \"temperature\": 37.2,
  \"oxygen_saturation\": 96,
  \"glasgow_coma_scale\": 15
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"id\": 12345,
    \"patient_id\": \"PATIENT_001\",
    \"recorded_at\": \"2024-01-01T14:30:00Z\"
  }
}
```

**Validation Rules:**
- `heart_rate`: 0-300 bpm
- `blood_pressure_systolic`: 0-300 mmHg
- `blood_pressure_diastolic`: 0-200 mmHg
- `respiratory_rate`: 0-100 breaths/min
- `temperature`: 30-45°C
- `oxygen_saturation`: 0-100%
- `glasgow_coma_scale`: 3-15

### Get Vital Signs History

Retrieve historical vital signs for a patient.

**Endpoint:** `GET /patients/{patient_id}/vitals`

**Query Parameters:**
- `start_date` (optional): Start date for data retrieval
- `end_date` (optional): End date for data retrieval  
- `limit` (optional): Maximum number of records (default: 100, max: 1000)
- `offset` (optional): Record offset for pagination

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"patient_id\": \"PATIENT_001\",
    \"total_records\": 48,
    \"vitals\": [
      {
        \"timestamp\": \"2024-01-01T14:30:00Z\",
        \"heart_rate\": 95,
        \"blood_pressure_systolic\": 140,
        \"blood_pressure_diastolic\": 85,
        \"respiratory_rate\": 18,
        \"temperature\": 37.2,
        \"oxygen_saturation\": 96,
        \"glasgow_coma_scale\": 15
      }
    ]
  }
}
```

### Add Clinical Notes

Submit clinical notes or observations.

**Endpoint:** `POST /patients/{patient_id}/notes`

**Request Body:**
```json
{
  \"timestamp\": \"2024-01-01T14:30:00Z\",
  \"author_id\": \"DR_SMITH\",
  \"author_role\": \"attending_physician\",
  \"note_type\": \"progress_note\",
  \"content\": \"Patient shows improvement in respiratory symptoms. Decreased work of breathing observed. Continue current antibiotic regimen.\"
}
```

### Add Laboratory Results

Submit laboratory test results.

**Endpoint:** `POST /patients/{patient_id}/labs`

**Request Body:**
```json
{
  \"timestamp\": \"2024-01-01T08:00:00Z\",
  \"results\": [
    {
      \"test_name\": \"White Blood Cell Count\",
      \"value\": 12.5,
      \"unit\": \"10^3/μL\",
      \"reference_range_min\": 4.0,
      \"reference_range_max\": 11.0,
      \"is_critical\": true
    },
    {
      \"test_name\": \"Lactate\",
      \"value\": 2.8,
      \"unit\": \"mmol/L\",
      \"reference_range_max\": 2.0,
      \"is_critical\": true
    }
  ]
}
```

## Prediction & Risk Assessment

### Get Risk Prediction

Generate a deterioration risk prediction for a patient.

**Endpoint:** `POST /patients/{patient_id}/predict`

**Request Body:**
```json
{
  \"patient_id\": \"PATIENT_001\",
  \"include_historical\": true,
  \"lookback_hours\": 24
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"patient_id\": \"PATIENT_001\",
    \"prediction_timestamp\": \"2024-01-01T15:00:00Z\",
    \"risk_score\": {
      \"overall_risk\": 0.75,
      \"sepsis_risk\": 0.68,
      \"cardiac_risk\": 0.45,
      \"respiratory_risk\": 0.82,
      \"neurological_risk\": 0.32,
      \"confidence\": 0.89,
      \"contributing_factors\": [
        {
          \"factor\": \"respiratory_rate_trend\",
          \"importance\": 0.24,
          \"description\": \"Increasing respiratory rate over past 6 hours\"
        },
        {
          \"factor\": \"temperature_elevation\",
          \"importance\": 0.18,
          \"description\": \"Fever pattern suggesting infection\"
        }
      ]
    },
    \"alerts\": [
      {
        \"alert_id\": \"alert_001\",
        \"severity\": \"high\",
        \"alert_type\": \"respiratory_deterioration\",
        \"message\": \"Patient showing signs of respiratory compromise\",
        \"recommended_actions\": [
          \"Increase monitoring frequency to q15min\",
          \"Consider arterial blood gas analysis\",
          \"Assess need for respiratory support\"
        ]
      }
    ],
    \"explanation\": {
      \"method\": \"SHAP\",
      \"explanation_text\": \"Key risk factors include increasing respiratory rate trend and elevated temperature pattern. Patient's vital signs show concerning deterioration over the past 6 hours.\",
      \"data_quality\": \"good\",
      \"model_version\": \"v1.2.3\"
    }
  }
}
```

### Batch Predictions

Get predictions for multiple patients at once.

**Endpoint:** `POST /predictions/batch`

**Request Body:**
```json
{
  \"patients\": [
    {
      \"patient_id\": \"PATIENT_001\",
      \"lookback_hours\": 24
    },
    {
      \"patient_id\": \"PATIENT_002\", 
      \"lookback_hours\": 12
    }
  ]
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"predictions\": [
      {
        \"patient_id\": \"PATIENT_001\",
        \"risk_score\": {\"overall_risk\": 0.75},
        \"status\": \"success\"
      },
      {
        \"patient_id\": \"PATIENT_002\",
        \"status\": \"error\",
        \"error\": \"Insufficient data\"
      }
    ],
    \"summary\": {
      \"total_requested\": 2,
      \"successful\": 1,
      \"failed\": 1
    }
  }
}
```

### Model Explanation

Get detailed model explanation for a prediction.

**Endpoint:** `GET /patients/{patient_id}/prediction/explain`

**Query Parameters:**
- `method` (optional): Explanation method (`shap`, `lime`, `rule_based`)
- `top_features` (optional): Number of top features to include (default: 10)

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"explanation\": {
      \"method\": \"SHAP\",
      \"base_value\": 0.15,
      \"prediction_contribution\": 0.60,
      \"top_positive_factors\": [
        {
          \"feature\": \"respiratory_rate_trend_6h\",
          \"importance\": 0.24,
          \"description\": \"Respiratory rate trend over 6 hours\",
          \"current_value\": \"increasing\"
        }
      ],
      \"top_negative_factors\": [
        {
          \"feature\": \"heart_rate_variability\",
          \"importance\": -0.08,
          \"description\": \"Heart rate variability\",
          \"current_value\": \"normal\"
        }
      ]
    },
    \"visualization_url\": \"https://api.patient-ews.com/visualizations/explanation/abc123.png\"
  }
}
```

## Alert Management

### Get Active Alerts

Retrieve all active alerts, optionally filtered by patient.

**Endpoint:** `GET /alerts/active`

**Query Parameters:**
- `patient_id` (optional): Filter alerts for specific patient
- `severity` (optional): Filter by severity (`low`, `medium`, `high`, `critical`)
- `limit` (optional): Maximum number of alerts (default: 50)

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"alerts\": [
      {
        \"alert_id\": \"alert_001\",
        \"patient_id\": \"PATIENT_001\",
        \"timestamp\": \"2024-01-01T15:00:00Z\",
        \"severity\": \"high\",
        \"alert_type\": \"deterioration_risk\",
        \"message\": \"High risk of deterioration detected\",
        \"risk_score\": 0.85,
        \"recommended_actions\": [
          \"Increase monitoring frequency\",
          \"Consider ICU evaluation\"
        ],
        \"is_acknowledged\": false,
        \"expires_at\": \"2024-01-01T19:00:00Z\"
      }
    ],
    \"summary\": {
      \"total_alerts\": 1,
      \"by_severity\": {
        \"critical\": 0,
        \"high\": 1,
        \"medium\": 0,
        \"low\": 0
      }
    }
  }
}
```

### Acknowledge Alert

Mark an alert as acknowledged by a clinician.

**Endpoint:** `POST /alerts/{alert_id}/acknowledge`

**Request Body:**
```json
{
  \"acknowledged_by\": \"DR_SMITH\",
  \"acknowledgment_note\": \"Patient assessed, plan updated\"
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"alert_id\": \"alert_001\",
    \"acknowledged_at\": \"2024-01-01T15:30:00Z\",
    \"acknowledged_by\": \"DR_SMITH\"
  }
}
```

### Get Alert History

Retrieve historical alerts for a patient or system-wide.

**Endpoint:** `GET /alerts/history`

**Query Parameters:**
- `patient_id` (optional): Filter by patient
- `start_date` (optional): Start date for alert history
- `end_date` (optional): End date for alert history
- `severity` (optional): Filter by severity
- `acknowledged` (optional): Filter by acknowledgment status

## Analytics & Insights

### Find Similar Patients

Find patients with similar characteristics and clinical patterns.

**Endpoint:** `GET /patients/{patient_id}/similar`

**Query Parameters:**
- `k` (optional): Number of similar patients to return (default: 5, max: 20)
- `similarity_threshold` (optional): Minimum similarity score (0-1, default: 0.7)

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"query_patient_id\": \"PATIENT_001\",
    \"similar_patients\": [
      {
        \"patient_id\": \"PATIENT_047\",
        \"similarity_score\": 0.89,
        \"demographics\": {
          \"age\": 67,
          \"gender\": \"M\",
          \"primary_diagnosis\": \"Pneumonia\"
        },
        \"outcome_summary\": {
          \"length_of_stay\": 5,
          \"icu_admission\": false,
          \"complications\": []
        }
      }
    ],
    \"cohort_insights\": {
      \"cohort_size\": 5,
      \"average_similarity\": 0.83,
      \"common_outcomes\": [
        \"successful_recovery\",
        \"no_icu_required\"
      ]
    }
  }
}
```

### Generate Patient Summary

Generate an AI-powered clinical summary for a patient.

**Endpoint:** `POST /patients/{patient_id}/summary`

**Request Body:**
```json
{
  \"summary_type\": \"comprehensive\",
  \"include_predictions\": true,
  \"clinical_question\": \"What are the key risk factors for this patient?\"
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"patient_id\": \"PATIENT_001\",
    \"summary\": {
      \"clinical_assessment\": \"67-year-old male with community-acquired pneumonia showing signs of clinical improvement. Vital signs demonstrate decreasing fever and improved oxygenation over past 24 hours.\",
      \"risk_factors\": [
        \"Advanced age (67 years)\",
        \"History of COPD\",
        \"Recent smoking cessation\"
      ],
      \"recommendations\": [
        \"Continue current antibiotic regimen\",
        \"Monitor respiratory status closely\",
        \"Consider step-down from telemetry if stable\"
      ],
      \"monitoring_parameters\": [
        \"Oxygen saturation\",
        \"Respiratory rate\",
        \"Temperature trends\"
      ]
    },
    \"generated_at\": \"2024-01-01T15:45:00Z\",
    \"confidence\": 0.92,
    \"sources_used\": [
      \"vital_signs\",
      \"clinical_notes\",
      \"lab_results\"
    ]
  }
}
```

### Clinical Q&A

Ask specific clinical questions about a patient using RAG.

**Endpoint:** `POST /patients/{patient_id}/qa`

**Request Body:**
```json
{
  \"question\": \"What is the trend in this patient's respiratory status over the past 12 hours?\"
}
```

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"question\": \"What is the trend in this patient's respiratory status over the past 12 hours?\",
    \"answer\": \"The patient's respiratory status has shown improvement over the past 12 hours. Respiratory rate decreased from 24 to 18 breaths per minute, oxygen saturation improved from 92% to 96%, and the patient reports less shortness of breath. Clinical notes indicate decreased use of accessory muscles.\",
    \"confidence\": 0.87,
    \"sources\": [
      {
        \"type\": \"vital_signs\",
        \"timestamp\": \"2024-01-01T14:30:00Z\"
      },
      {
        \"type\": \"clinical_note\",
        \"timestamp\": \"2024-01-01T13:00:00Z\"
      }
    ]
  }
}
```

### Population Analytics

Get insights about patient populations and trends.

**Endpoint:** `GET /analytics/population`

**Query Parameters:**
- `unit` (optional): Hospital unit filter
- `diagnosis` (optional): Primary diagnosis filter
- `date_range` (optional): Date range for analysis
- `metrics` (optional): Specific metrics to include

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"time_period\": \"2024-01-01 to 2024-01-07\",
    \"total_patients\": 150,
    \"risk_distribution\": {
      \"low_risk\": 85,
      \"medium_risk\": 45,
      \"high_risk\": 15,
      \"critical_risk\": 5
    },
    \"alert_statistics\": {
      \"total_alerts\": 127,
      \"alert_rate\": 0.85,
      \"false_positive_rate\": 0.12,
      \"response_time_median\": \"8.5 minutes\"
    },
    \"outcome_metrics\": {
      \"early_interventions\": 23,
      \"prevented_deteriorations\": 8,
      \"icu_transfers\": 3
    }
  }
}
```

## System Information

### Health Check

Check the overall health and status of the API service.

**Endpoint:** `GET /health`

**Response:**
```json
{
  \"status\": \"healthy\",
  \"timestamp\": \"2024-01-01T16:00:00Z\",
  \"version\": \"1.2.3\",
  \"services\": {
    \"database\": \"healthy\",
    \"mlflow\": \"healthy\",
    \"kafka\": \"healthy\",
    \"redis\": \"healthy\"
  },
  \"system_metrics\": {
    \"uptime_seconds\": 86400,
    \"memory_usage_mb\": 512,
    \"active_predictions\": 15,
    \"queue_length\": 0
  }
}
```

### System Metrics

Get detailed system metrics and performance information.

**Endpoint:** `GET /metrics`

**Response:**
```json
{
  \"status\": \"success\",
  \"data\": {
    \"api_metrics\": {
      \"requests_per_minute\": 45,
      \"average_response_time_ms\": 150,
      \"error_rate\": 0.02
    },
    \"ml_metrics\": {
      \"predictions_per_hour\": 250,
      \"model_accuracy\": 0.87,
      \"average_prediction_time_ms\": 85
    },
    \"resource_usage\": {
      \"cpu_usage_percent\": 35,
      \"memory_usage_percent\": 45,
      \"disk_usage_percent\": 20
    }
  }
}
```

### Prometheus Metrics

Get metrics in Prometheus format for monitoring integration.

**Endpoint:** `GET /metrics/prometheus`

**Response:** (text/plain format)
```
# HELP ews_predictions_total Total number of predictions made
# TYPE ews_predictions_total counter
ews_predictions_total 1250

# HELP ews_prediction_duration_seconds Time taken for predictions
# TYPE ews_prediction_duration_seconds histogram
ews_prediction_duration_seconds_bucket{le=\"0.1\"} 100
ews_prediction_duration_seconds_bucket{le=\"0.5\"} 950
ews_prediction_duration_seconds_bucket{le=\"1.0\"} 1200
ews_prediction_duration_seconds_bucket{le=\"+Inf\"} 1250
```

## SDK & Code Examples

### Python SDK

Install the Python SDK:
```bash
pip install patient-ews-sdk
```

Basic usage:
```python
from patient_ews import EWSClient

# Initialize client
client = EWSClient(
    base_url=\"https://api.patient-ews.com\",
    api_key=\"your-api-key\"
)

# Create a patient
patient = client.patients.create({
    \"patient_id\": \"PATIENT_001\",
    \"age\": 65,
    \"gender\": \"M\",
    \"primary_diagnosis\": \"Pneumonia\"
})

# Add vital signs
vitals = client.patients.add_vitals(\"PATIENT_001\", {
    \"timestamp\": \"2024-01-01T14:30:00Z\",
    \"heart_rate\": 95,
    \"blood_pressure_systolic\": 140,
    \"temperature\": 37.2
})

# Get prediction
prediction = client.predictions.get(\"PATIENT_001\")
print(f\"Risk Score: {prediction.risk_score.overall_risk}\")

# Handle errors
try:
    prediction = client.predictions.get(\"INVALID_PATIENT\")
except client.PatientNotFoundError as e:
    print(f\"Patient not found: {e.message}\")
```

### JavaScript SDK

Install the JavaScript SDK:
```bash
npm install patient-ews-sdk
```

Basic usage:
```javascript
const { EWSClient } = require('patient-ews-sdk');

// Initialize client
const client = new EWSClient({
  baseUrl: 'https://api.patient-ews.com',
  apiKey: 'your-api-key'
});

// Create a patient
const patient = await client.patients.create({
  patient_id: 'PATIENT_001',
  age: 65,
  gender: 'M',
  primary_diagnosis: 'Pneumonia'
});

// Add vital signs
const vitals = await client.patients.addVitals('PATIENT_001', {
  timestamp: '2024-01-01T14:30:00Z',
  heart_rate: 95,
  blood_pressure_systolic: 140,
  temperature: 37.2
});

// Get prediction
const prediction = await client.predictions.get('PATIENT_001');
console.log(`Risk Score: ${prediction.risk_score.overall_risk}`);
```

### cURL Examples

**Create Patient:**
```bash
curl -X POST \"https://api.patient-ews.com/patients\" \
  -H \"Authorization: Bearer your-api-key\" \
  -H \"Content-Type: application/json\" \
  -d '{
    \"patient_id\": \"PATIENT_001\",
    \"age\": 65,
    \"gender\": \"M\",
    \"primary_diagnosis\": \"Pneumonia\"
  }'
```

**Get Prediction:**
```bash
curl -X POST \"https://api.patient-ews.com/patients/PATIENT_001/predict\" \
  -H \"Authorization: Bearer your-api-key\" \
  -H \"Content-Type: application/json\" \
  -d '{
    \"patient_id\": \"PATIENT_001\",
    \"lookback_hours\": 24
  }'
```

**Get Active Alerts:**
```bash
curl -X GET \"https://api.patient-ews.com/alerts/active\" \
  -H \"Authorization: Bearer your-api-key\"
```

This comprehensive API reference provides all the information needed to integrate with the Patient Deterioration Early Warning System. For additional support, please refer to our support documentation or contact the development team.