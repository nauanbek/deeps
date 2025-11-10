import React from 'react';
import { renderHook, waitFor, act } from '@testing-library/react';
import { AuthProvider } from '../AuthContext';
import { useAuth } from '../../hooks/useAuth';
import * as authApi from '../../api/auth';

// Mock the auth API
jest.mock('../../api/auth');

const mockAuthApi = authApi as jest.Mocked<typeof authApi>;

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  describe('Initialization', () => {
    it('should initialize with no user when no token in localStorage', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should restore user session from localStorage token', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      localStorage.setItem('auth_token', 'test-token');
      mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('test-token');
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should clear invalid token from localStorage', async () => {
      localStorage.setItem('auth_token', 'invalid-token');
      mockAuthApi.getCurrentUser.mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('Login', () => {
    it('should successfully login user', async () => {
      const mockAuthResponse = {
        access_token: 'new-token',
        token_type: 'bearer',
      };
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      mockAuthApi.login.mockResolvedValue(mockAuthResponse);
      mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login('testuser', 'password123');
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('new-token');
      expect(localStorage.getItem('auth_token')).toBe('new-token');
    });

    it('should handle login failure', async () => {
      mockAuthApi.login.mockRejectedValue(new Error('Invalid credentials'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.login('testuser', 'wrongpassword');
        })
      ).rejects.toThrow();

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Register', () => {
    it('should successfully register user', async () => {
      const mockAuthResponse = {
        access_token: 'new-token',
        token_type: 'bearer',
      };
      const mockUser = {
        id: 1,
        username: 'newuser',
        email: 'new@example.com',
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      mockAuthApi.register.mockResolvedValue(mockAuthResponse);
      mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.register('newuser', 'new@example.com', 'password123');
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('new-token');
      expect(localStorage.getItem('auth_token')).toBe('new-token');
    });

    it('should handle registration failure', async () => {
      mockAuthApi.register.mockRejectedValue(new Error('Username already exists'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await expect(
        act(async () => {
          await result.current.register('existinguser', 'test@example.com', 'password123');
        })
      ).rejects.toThrow();

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout', () => {
    it('should successfully logout user', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      localStorage.setItem('auth_token', 'test-token');
      mockAuthApi.getCurrentUser.mockResolvedValue(mockUser);
      mockAuthApi.logout.mockResolvedValue();

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      act(() => {
        result.current.logout();
      });

      await waitFor(() => {
        expect(result.current.user).toBeNull();
      });

      expect(result.current.token).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('RefreshUser', () => {
    it('should refresh user data', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
      };

      const updatedUser = {
        ...mockUser,
        email: 'updated@example.com',
      };

      localStorage.setItem('auth_token', 'test-token');
      mockAuthApi.getCurrentUser.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      mockAuthApi.getCurrentUser.mockResolvedValueOnce(updatedUser);

      await act(async () => {
        await result.current.refreshUser();
      });

      await waitFor(() => {
        expect(result.current.user?.email).toBe('updated@example.com');
      });
    });
  });
});
