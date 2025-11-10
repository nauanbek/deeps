import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User, AuthContextType } from '../types/auth';
import * as authApi from '../api/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');

      if (storedToken) {
        setToken(storedToken);
        try {
          // Verify token and get user info
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to restore auth session:', error);
          // Clear invalid token
          localStorage.removeItem('auth_token');
          setToken(null);
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Auto-logout on token expiry (30 minutes)
  useEffect(() => {
    if (token) {
      // Set timeout for 30 minutes
      const timeoutId = setTimeout(() => {
        logout();
      }, 30 * 60 * 1000); // 30 minutes in milliseconds

      return () => clearTimeout(timeoutId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const login = useCallback(async (username: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const authResponse = await authApi.login({ username, password });
      const { access_token } = authResponse;

      // Store token
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);

      // Fetch user data
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (username: string, email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const authResponse = await authApi.register({ username, email, password });
      const { access_token } = authResponse;

      // Store token
      localStorage.setItem('auth_token', access_token);
      setToken(access_token);

      // Fetch user data
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    // Call logout endpoint first (while token is still in localStorage)
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with logout even if API call fails
    }

    // Then clear local state
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
  }, []);

  const refreshUser = useCallback(async (): Promise<void> => {
    if (!token) return;

    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user data:', error);
      throw error;
    }
  }, [token]);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
