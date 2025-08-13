import React from 'react';
import { HeartIcon, UserIcon, BellIcon } from '@heroicons/react/24/outline';
import { useAlerts } from '../contexts/AlertContext';
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { activeAlerts } = useAlerts();
  const { user, logout } = useAuth();

  return (
    <header className="bg-gradient-to-r from-blue-800 to-blue-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-12 h-12 bg-white bg-opacity-10 rounded-lg backdrop-blur-sm">
              <HeartIcon className="w-8 h-8 text-red-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">CarePulse</h1>
              <p className="text-xs text-blue-200 font-medium">Early Warning System</p>
            </div>
          </div>

          {/* Center - System Status */}
          <div className="hidden md:flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-blue-100">System Online</span>
            </div>
            
            {activeAlerts.length > 0 && (
              <div className="flex items-center space-x-2 bg-red-500 bg-opacity-20 px-3 py-1 rounded-full">
                <BellIcon className="w-4 h-4 text-red-300" />
                <span className="text-sm font-bold text-red-200">
                  {activeAlerts.length} Alert{activeAlerts.length !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>

          {/* User Profile */}
          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium">{user?.name || 'Medical Staff'}</p>
              <p className="text-xs text-blue-200">{user?.role || 'Healthcare Provider'}</p>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-white bg-opacity-10 rounded-full flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-blue-200" />
              </div>
              
              <button
                onClick={logout}
                className="text-sm text-blue-200 hover:text-white transition-colors px-2 py-1 rounded hover:bg-white hover:bg-opacity-10"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Alert Banner */}
      {activeAlerts.length > 0 && (
        <div className="md:hidden bg-red-600 bg-opacity-90 px-4 py-2">
          <div className="flex items-center justify-center space-x-2">
            <BellIcon className="w-4 h-4 text-white" />
            <span className="text-sm font-medium text-white">
              {activeAlerts.length} Active Alert{activeAlerts.length !== 1 ? 's' : ''} - Check Dashboard
            </span>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;