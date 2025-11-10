/**
 * Authentication API Client
 *
 * Provides HTTP methods for user authentication and profile management.
 * Includes registration, login, logout, profile updates, and password changes.
 * Auth tokens are stored in localStorage and automatically included in requests.
 *
 * @module api/auth
 */

import { apiClient } from './client';
import {
  User,
  LoginCredentials,
  RegisterData,
  AuthResponse,
  UpdateProfileData,
  ChangePasswordData,
} from '../types/auth';

/**
 * Register a new user account.
 *
 * Creates a new user account and returns an authentication token.
 * Password must be at least 8 characters with letter and number.
 *
 * @param {RegisterData} data - Registration data
 * @param {string} data.username - Username (3-50 chars, alphanumeric + underscore)
 * @param {string} data.email - Valid email address
 * @param {string} data.password - Password (min 8 chars, letter + number)
 * @returns {Promise<AuthResponse>} Auth response with token and user data
 * @throws {AxiosError} 400 if validation fails, 409 if username/email exists
 *
 * @example
 * const { access_token, user } = await register({
 *   username: 'john_doe',
 *   email: 'john@example.com',
 *   password: 'SecurePass123'
 * });
 * localStorage.setItem('auth_token', access_token);
 */
export const register = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/register', data);
  return response.data;
};

/**
 * Login with username and password.
 *
 * Authenticates user and returns a JWT token valid for 30 minutes.
 * Token is automatically included in subsequent requests via interceptor.
 *
 * @param {LoginCredentials} credentials - Login credentials
 * @param {string} credentials.username - Username
 * @param {string} credentials.password - Password
 * @returns {Promise<AuthResponse>} Auth response with token and user data
 * @throws {AxiosError} 401 if credentials invalid, 400 if validation fails
 *
 * @example
 * const { access_token, user } = await login({
 *   username: 'john_doe',
 *   password: 'SecurePass123'
 * });
 * localStorage.setItem('auth_token', access_token);
 */
export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
  return response.data;
};

/**
 * Get current authenticated user.
 *
 * Fetches the currently authenticated user's profile using the
 * JWT token from localStorage.
 *
 * @returns {Promise<User>} Current user profile
 * @throws {AxiosError} 401 if not authenticated or token expired
 *
 * @example
 * const user = await getCurrentUser();
 * console.log(`Logged in as: ${user.username}`);
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
};

/**
 * Logout current user.
 *
 * Invalidates the current session. Client should remove token
 * from localStorage after calling this.
 *
 * @returns {Promise<void>}
 *
 * @example
 * await logout();
 * localStorage.removeItem('auth_token');
 * window.location.href = '/login';
 */
export const logout = async (): Promise<void> => {
  await apiClient.post('/auth/logout');
};

/**
 * Get user profile.
 *
 * Alias for getCurrentUser(). Fetches the authenticated user's profile.
 *
 * @returns {Promise<User>} User profile
 * @throws {AxiosError} 401 if not authenticated
 */
export const getUserProfile = async (): Promise<User> => {
  const response = await apiClient.get<User>('/users/me');
  return response.data;
};

/**
 * Update user profile.
 *
 * Updates the current user's profile information.
 * Only email can be updated currently.
 *
 * @param {UpdateProfileData} data - Profile update data
 * @param {string} [data.email] - New email address
 * @returns {Promise<User>} Updated user profile
 * @throws {AxiosError} 400 if validation fails, 401 if not authenticated, 409 if email exists
 *
 * @example
 * const updated = await updateProfile({
 *   email: 'newemail@example.com'
 * });
 */
export const updateProfile = async (data: UpdateProfileData): Promise<User> => {
  const response = await apiClient.put<User>('/users/me', data);
  return response.data;
};

/**
 * Change user password.
 *
 * Updates the current user's password. Requires current password
 * for verification. New password must meet strength requirements.
 *
 * @param {ChangePasswordData} data - Password change data
 * @param {string} data.current_password - Current password for verification
 * @param {string} data.new_password - New password (min 8 chars, letter + number)
 * @param {string} data.confirm_password - New password confirmation (must match)
 * @returns {Promise<void>}
 * @throws {AxiosError} 400 if validation fails or passwords don't match, 401 if current password wrong
 *
 * @example
 * await changePassword({
 *   current_password: 'OldPass123',
 *   new_password: 'NewSecurePass456',
 *   confirm_password: 'NewSecurePass456'
 * });
 */
export const changePassword = async (data: ChangePasswordData): Promise<void> => {
  await apiClient.put('/users/me/password', data);
};

/**
 * Delete user account.
 *
 * Permanently deletes the current user's account and all associated data
 * including agents, executions, and configurations. This action cannot be undone.
 *
 * @returns {Promise<void>}
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * if (confirm('Delete account? This cannot be undone!')) {
 *   await deleteAccount();
 *   localStorage.removeItem('auth_token');
 *   window.location.href = '/';
 * }
 */
export const deleteAccount = async (): Promise<void> => {
  await apiClient.delete('/users/me');
};
