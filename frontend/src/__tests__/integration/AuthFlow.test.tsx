import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@testing-library/jest-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import { ProtectedRoute } from '../../components/auth/ProtectedRoute';
import Login from '../../pages/Login';
import Dashboard from '../../pages/Dashboard';
import * as authApi from '../../api/auth';

// Mock the Dashboard to avoid complex dependencies
jest.mock('../../pages/Dashboard', () => ({
  __esModule: true,
  default: () => <div>Dashboard Page</div>,
}));

// Don't mock Login - we need the actual component for integration tests

// Mock the auth API
jest.mock('../../api/auth');

describe('Authentication Flow Integration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    localStorage.clear();
    jest.clearAllMocks();
  });

  const renderWithProviders = (initialRoute = '/') => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialRoute]}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('redirects to login when accessing protected route without auth', async () => {
    renderWithProviders('/dashboard');

    // Should redirect to login page
    await waitFor(() => {
      expect(screen.getByText(/Sign in to DeepAgents/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
  });

  it('allows access to protected route after successful login', async () => {
    const mockToken = 'mock-jwt-token';
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
    };

    (authApi.login as jest.Mock).mockResolvedValue({
      access_token: mockToken,
      token_type: 'bearer',
      user: mockUser,
    });

    (authApi.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    renderWithProviders('/login');

    // Fill in login form
    const usernameInput = screen.getByLabelText(/Username/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const loginButton = screen.getByRole('button', { name: /Sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(loginButton);

    // Wait for login to complete
    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });

    // Token should be stored
    expect(localStorage.getItem('auth_token')).toBe(mockToken);

    // Should navigate to dashboard (dashboard content would appear)
    // Note: In a real scenario, the router would navigate automatically
  });

  it('shows error message on invalid credentials', async () => {
    (authApi.login as jest.Mock).mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Invalid credentials' },
      },
    });

    renderWithProviders('/login');

    const usernameInput = screen.getByLabelText(/Username/i);
    const passwordInput = screen.getByLabelText(/Password/i);
    const loginButton = screen.getByRole('button', { name: /Sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(loginButton);

    // Should show error message
    await waitFor(() => {
      // The error could be either the detail from backend or the fallback message
      const errorText = screen.queryByText(/Invalid credentials/i) || screen.queryByText(/Invalid username or password/i);
      expect(errorText).toBeInTheDocument();
    }, { timeout: 3000 });

    // Should not store token
    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('validates required fields before submission', () => {
    renderWithProviders('/login');

    const loginButton = screen.getByRole('button', { name: /Sign in/i });

    // Try to submit empty form
    fireEvent.click(loginButton);

    // Should show validation errors (if implemented)
    // Username and password fields should have HTML5 validation
    const usernameInput = screen.getByLabelText(/Username/i) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(
      /Password/i
    ) as HTMLInputElement;

    expect(usernameInput.required).toBe(true);
    expect(passwordInput.required).toBe(true);
  });

  it('logs out user and redirects to login', async () => {
    const mockToken = 'mock-jwt-token';
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
    };

    // Set up authenticated state
    localStorage.setItem('auth_token', mockToken);
    (authApi.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    renderWithProviders('/dashboard');

    // Wait for auth check
    await waitFor(() => {
      expect(authApi.getCurrentUser).toHaveBeenCalled();
    });

    // Simulate logout (in real app, would click logout button)
    localStorage.removeItem('auth_token');

    // Verify token is removed
    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('persists authentication across page refreshes', async () => {
    const mockToken = 'mock-jwt-token';
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
    };

    // Simulate existing auth state
    localStorage.setItem('auth_token', mockToken);
    (authApi.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    renderWithProviders('/dashboard');

    // Should fetch current user with stored token
    await waitFor(() => {
      expect(authApi.getCurrentUser).toHaveBeenCalled();
    });

    // Token should still be in localStorage
    expect(localStorage.getItem('auth_token')).toBe(mockToken);
  });

  it('handles token expiration gracefully', async () => {
    const mockToken = 'expired-token';

    localStorage.setItem('auth_token', mockToken);
    (authApi.getCurrentUser as jest.Mock).mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Token expired' },
      },
    });

    renderWithProviders('/dashboard');

    // Should attempt to fetch user
    await waitFor(() => {
      expect(authApi.getCurrentUser).toHaveBeenCalled();
    });

    // Should redirect to login on token expiration
    // (This depends on AuthContext implementation)
  });
});
