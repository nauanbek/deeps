import { useContext } from 'react';
import AuthContext from '../contexts/AuthContext';
import { AuthContextType } from '../types/auth';

/**
 * Custom hook for accessing authentication context
 * @throws Error if used outside AuthProvider
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};
