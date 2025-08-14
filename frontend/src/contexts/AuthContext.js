import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing session on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (token) {
        // Verify token with backend
        const response = await authAPI.verifyToken();
        if (response.data && response.data.user) {
          setUser(response.data.user);
        } else {
          localStorage.removeItem('auth_token');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('auth_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authAPI.login(credentials);
      
      // Handle direct response from simple server
      const responseData = response.data;
      if (responseData && responseData.token && responseData.user) {
        const { token, user } = responseData;
        
        // Store token
        localStorage.setItem('auth_token', token);
        
        // Set user
        setUser(user);
        
        console.log('Login successful:', user.name);
        return { success: true, user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const signup = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authAPI.signup(userData);
      
      if (response.data && response.data.token && response.data.user) {
        const { token, user } = response.data;
        
        // Store token
        localStorage.setItem('auth_token', token);
        
        // Set user
        setUser(user);
        
        console.log('Signup successful:', user.name);
        return { success: true, user };
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Signup failed:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Signup failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint to invalidate token on server
      await authAPI.logout().catch(() => {
        // Continue with local logout even if server call fails
      });
    } finally {
      // Always clear local session
      localStorage.removeItem('auth_token');
      setUser(null);
      setError(null);
      console.log('Logged out successfully');
    }
  };

  const updateProfile = async (profileData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authAPI.updateProfile(profileData);
      
      if (response.data && response.data.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (error) {
      console.error('Profile update failed:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Profile update failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const changePassword = async (passwordData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authAPI.changePassword(passwordData);
      
      if (response.data && response.data.success) {
        return { success: true };
      } else {
        throw new Error('Failed to change password');
      }
    } catch (error) {
      console.error('Password change failed:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Password change failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    // State
    user,
    loading,
    error,
    isAuthenticated: !!user,
    
    // Actions
    login,
    signup,
    logout,
    updateProfile,
    changePassword,
    checkAuthStatus,
    clearError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;