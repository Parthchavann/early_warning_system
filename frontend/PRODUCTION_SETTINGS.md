# Production Settings - Keep Only Essential Features

## Settings Page - Remove These (Non-essential for production):
❌ **Development/Debug Options:**
- Debug mode toggles
- Test data generators
- Mock data switches
- Development server configs
- Console logging levels
- API debugging tools

❌ **Advanced/Technical Settings:**
- Database connection strings
- Raw SQL query interfaces  
- Server configuration panels
- Memory/performance monitors
- System diagnostics beyond basic health

❌ **Experimental Features:**
- Beta feature flags
- Experimental algorithms
- A/B testing toggles
- Preview/alpha functionality

## Settings Page - Keep These (Essential for production):
✅ **User Preferences:**
- Auto-refresh intervals (30s, 1min, 5min)
- Time zone selection
- Language/locale (if supported)
- Theme preference (light/dark)

✅ **Alert Settings:**
- Alert notification preferences
- Alert severity thresholds (Critical, High, Medium)
- Sound notifications on/off
- Email notification preferences

✅ **Display Options:**
- Items per page (10, 25, 50)
- Default chart time range (1hr, 4hr, 24hr)
- Risk score display format (percentage vs decimal)
- Date/time format preferences

✅ **Export Settings:**
- Default export format (PDF/CSV)
- Export data range options
- Include/exclude patient identifiers in exports

✅ **Security Settings:**
- Session timeout preferences
- Auto-logout settings
- Password change (if applicable)

## Recommended Production Settings Structure:
```
Settings
├── User Preferences
│   ├── Auto-refresh: [30s|1min|5min]
│   ├── Time Zone: [Dropdown]
│   └── Theme: [Light|Dark]
│
├── Alerts & Notifications  
│   ├── Alert Sounds: [On|Off]
│   ├── Critical Risk Threshold: [0.8|0.9]
│   └── High Risk Threshold: [0.6|0.7]
│
├── Display Options
│   ├── Patients per page: [10|25|50]
│   ├── Chart time range: [1hr|4hr|24hr]
│   └── Risk format: [Percentage|Decimal]
│
└── Export Preferences
    ├── Default format: [PDF|CSV]
    └── Include patient names: [Yes|No]
```

## Implementation:
1. Remove all development/debugging controls
2. Keep only user-facing, production-relevant settings
3. Group related settings together
4. Use clear, non-technical language
5. Provide sensible defaults for all options

## Settings Values to Store:
```json
{
  "autoRefresh": 30,
  "timeZone": "local", 
  "theme": "light",
  "alertSounds": true,
  "criticalThreshold": 0.8,
  "highRiskThreshold": 0.6,
  "patientsPerPage": 25,
  "chartTimeRange": "4hr",
  "riskFormat": "percentage",
  "exportFormat": "pdf",
  "includePatientNames": true
}
```