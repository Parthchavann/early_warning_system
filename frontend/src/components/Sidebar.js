import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  ChartBarIcon,
  UserGroupIcon,
  PresentationChartLineIcon,
  Cog6ToothIcon,
  HeartIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  BellIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

const Sidebar = ({ isOpen, onToggle }) => {
  const { user, logout } = useAuth();
  
  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: ChartBarIcon,
      description: 'Overview and key metrics'
    },
    {
      name: 'Patients',
      href: '/patients',
      icon: UserGroupIcon,
      description: 'Patient list and management'
    },
    {
      name: 'Alerts',
      href: '/alerts',
      icon: BellIcon,
      description: 'Alert management and monitoring'
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: PresentationChartLineIcon,
      description: 'Reports and data analysis'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
      description: 'System configuration'
    }
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className="fixed top-0 left-0 z-50 h-full bg-white shadow-xl w-64 lg:relative lg:shadow-none lg:bg-gray-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0 bg-gradient-to-r from-blue-50 to-blue-100">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white rounded-lg shadow-sm border border-blue-200">
              <HeartIcon className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-blue-900">CarePulse</h1>
              <p className="text-xs text-blue-600 font-medium">Early Warning System</p>
            </div>
          </div>
          
          {/* Close button for mobile */}
          <button
            onClick={onToggle}
            className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation - Scrollable */}
        <nav className="flex-1 p-4 space-y-3 overflow-y-auto">
          {navigationItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-100 text-blue-700 shadow-sm border border-blue-200'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 hover:shadow-sm'
                }`
              }
              onClick={() => {
                // Close mobile menu when navigating
                if (window.innerWidth < 1024) {
                  onToggle();
                }
              }}
            >
              {({ isActive }) => (
                <>
                  <item.icon 
                    className={`mr-3 h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'}`} 
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium">{item.name}</div>
                    <div className="text-xs text-gray-500 group-hover:text-gray-600">
                      {item.description}
                    </div>
                  </div>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User Profile */}
        {user && (
          <div className="flex-shrink-0 p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center space-x-3 mb-3">
              <UserCircleIcon className="w-8 h-8 text-gray-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user.name}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user.role} • {user.email}
                </p>
              </div>
            </div>
            <button
              onClick={logout}
              className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        )}

        {/* System Status */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>System Online</span>
            </div>
            <div>v1.0.0</div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;