import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Cog6ToothIcon,
  BellIcon,
  ServerIcon,
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

const Settings = () => {
  const [settings, setSettings] = useState({
    notifications: {
      criticalAlerts: true,
      systemUpdates: false,
      reportReminders: true,
      emailNotifications: true
    },
    system: {
      autoRefresh: true,
      refreshInterval: 30,
      darkMode: false,
      compactView: false
    },
    api: {
      baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 10000,
      showDebugLogs: false
    }
  });

  const [showApiKey, setShowApiKey] = useState(false);

  const handleNotificationChange = (key) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: !prev.notifications[key]
      }
    }));
  };

  const handleSystemChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      system: {
        ...prev.system,
        [key]: value
      }
    }));
  };

  const handleApiChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      api: {
        ...prev.api,
        [key]: value
      }
    }));
  };

  const saveSettings = () => {
    // In a real app, this would save to backend or localStorage
    console.log('Saving settings:', settings);
    alert('Settings saved successfully!');
  };

  const resetSettings = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      setSettings({
        notifications: {
          criticalAlerts: true,
          systemUpdates: false,
          reportReminders: true,
          emailNotifications: true
        },
        system: {
          autoRefresh: true,
          refreshInterval: 30,
          darkMode: false,
          compactView: false
        },
        api: {
          baseUrl: 'http://localhost:8000',
          timeout: 10000,
          showDebugLogs: false
        }
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure your dashboard preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-blue-100 rounded-lg">
              <BellIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Notifications</h3>
              <p className="text-sm text-gray-600">Manage alert preferences</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Critical Alerts</p>
                <p className="text-sm text-gray-500">High-priority patient alerts</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.notifications.criticalAlerts}
                  onChange={() => handleNotificationChange('criticalAlerts')}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">System Updates</p>
                <p className="text-sm text-gray-500">System maintenance notifications</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.notifications.systemUpdates}
                  onChange={() => handleNotificationChange('systemUpdates')}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Report Reminders</p>
                <p className="text-sm text-gray-500">Weekly analytics reports</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.notifications.reportReminders}
                  onChange={() => handleNotificationChange('reportReminders')}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-500">Receive alerts via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.notifications.emailNotifications}
                  onChange={() => handleNotificationChange('emailNotifications')}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </motion.div>

        {/* System Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-green-100 rounded-lg">
              <Cog6ToothIcon className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">Display & Performance</h3>
              <p className="text-sm text-gray-600">Interface and behavior settings</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Auto Refresh</p>
                <p className="text-sm text-gray-500">Automatically refresh data</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.system.autoRefresh}
                  onChange={() => handleSystemChange('autoRefresh', !settings.system.autoRefresh)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                min="5"
                max="300"
                value={settings.system.refreshInterval}
                onChange={(e) => handleSystemChange('refreshInterval', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Dark Mode</p>
                <p className="text-sm text-gray-500">Enable dark theme (Coming soon)</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer opacity-50">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  disabled
                  checked={settings.system.darkMode}
                  onChange={() => handleSystemChange('darkMode', !settings.system.darkMode)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Compact View</p>
                <p className="text-sm text-gray-500">Reduce spacing and padding</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.system.compactView}
                  onChange={() => handleSystemChange('compactView', !settings.system.compactView)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </motion.div>

        {/* API Configuration */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 lg:col-span-2"
        >
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2 bg-purple-100 rounded-lg">
              <ServerIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">API Configuration</h3>
              <p className="text-sm text-gray-600">Backend connection settings</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                API Base URL
              </label>
              <input
                type="url"
                value={settings.api.baseUrl}
                onChange={(e) => handleApiChange('baseUrl', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="http://localhost:8000"
              />
              <p className="text-xs text-gray-500 mt-1">Backend server endpoint</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Request Timeout (ms)
              </label>
              <input
                type="number"
                min="1000"
                max="60000"
                value={settings.api.timeout}
                onChange={(e) => handleApiChange('timeout', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">Maximum request wait time</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                API Key
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={process.env.REACT_APP_API_KEY || 'secure-api-key-change-in-production'}
                  readOnly
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showApiKey ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">Set via environment variable</p>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Debug Logging</p>
                <p className="text-sm text-gray-500">Show API request/response logs</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.api.showDebugLogs}
                  onChange={() => handleApiChange('showDebugLogs', !settings.api.showDebugLogs)}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
        <button
          onClick={resetSettings}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
        >
          Reset to Defaults
        </button>
        <button
          onClick={saveSettings}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Save Settings
        </button>
      </div>

      {/* System Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gray-50 border border-gray-200 rounded-md p-4"
      >
        <div className="flex items-center space-x-3">
          <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
          <div>
            <h4 className="text-sm font-medium text-gray-900">System Information</h4>
            <p className="text-sm text-gray-600">
              Patient EWS Dashboard v1.0.0 • React {React.version} • 
              Node.js environment variables configured
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Settings;