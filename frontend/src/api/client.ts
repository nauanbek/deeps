/**
 * API Client Configuration
 *
 * Configures the Axios HTTP client with:
 * - Base URL and default headers
 * - Request interceptor for JWT authentication
 * - Response interceptor for error handling and auto-redirect on 401
 * - User-friendly error message generation
 * - Development logging
 *
 * @module api/client
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Configured Axios instance for all API requests.
 *
 * Includes automatic JWT token injection, error handling,
 * and authentication flow management.
 *
 * Configuration:
 * - Base URL: /api/v1
 * - Timeout: 30 seconds
 * - Content-Type: application/json
 * - Authorization: Bearer token from localStorage (auto-injected)
 *
 * @example
 * import { apiClient } from './client';
 * const response = await apiClient.get('/agents');
 */
export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

/**
 * Request interceptor that automatically injects JWT token.
 *
 * Retrieves the auth token from localStorage and adds it to
 * the Authorization header as a Bearer token for all requests.
 * If no token exists, the request proceeds without authentication.
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Generate user-friendly error messages from Axios errors.
 *
 * Handles various error scenarios:
 * - Network errors (no response)
 * - Timeout errors (ECONNABORTED)
 * - HTTP errors with custom messages from backend
 * - Status code-specific default messages
 *
 * @param {unknown} error - Axios error object
 * @returns {string} User-friendly error message
 *
 * @private
 */
const getErrorMessage = (error: unknown): string => {
  // Type guard for axios error structure
  if (!error || typeof error !== 'object') {
    return 'An unexpected error occurred';
  }

  const axiosError = error as {
    code?: string;
    message?: string;
    response?: {
      status?: number;
      data?: { detail?: string; message?: string };
    };
  };
  // Network errors
  if (!axiosError.response) {
    if (axiosError.code === 'ECONNABORTED') {
      return 'Request timed out. Please check your connection and try again.';
    }
    if (axiosError.message === 'Network Error') {
      return 'Network error. Please check your internet connection.';
    }
    return 'Unable to connect to server. Please try again later.';
  }

  // Server errors with custom messages
  const status = axiosError.response.status;
  const data = axiosError.response.data;

  // Extract error message from various response formats
  const message =
    data?.detail ||
    data?.message ||
    data?.error ||
    (typeof data === 'string' ? data : null);

  if (message) {
    return message;
  }

  // Default messages by status code
  const statusMessages: Record<number, string> = {
    400: 'Invalid request. Please check your input and try again.',
    401: 'Authentication required. Please log in.',
    403: 'You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    409: 'This action conflicts with existing data.',
    422: 'Validation error. Please check your input.',
    429: 'Too many requests. Please try again later.',
    500: 'Server error. Please try again later.',
    502: 'Bad gateway. The server is temporarily unavailable.',
    503: 'Service unavailable. Please try again later.',
    504: 'Gateway timeout. The server took too long to respond.',
  };

  return statusMessages[status] || 'An unexpected error occurred.';
};

/**
 * Response interceptor for global error handling and authentication.
 *
 * Functionality:
 * - Adds user-friendly error messages to all errors (error.friendlyMessage)
 * - Logs errors in development mode for debugging
 * - Auto-redirects to /login on 401 Unauthorized (expired/invalid token)
 * - Logs 403 Forbidden warnings
 * - Parses retry-after headers for 429 Rate Limiting
 *
 * Error Properties Added:
 * - error.friendlyMessage: User-friendly error message string
 * - error.retryAfter: Seconds to wait before retrying (for 429 errors)
 *
 * @example
 * try {
 *   await apiClient.get('/agents');
 * } catch (error) {
 *   console.error(error.friendlyMessage); // User-friendly message
 *   if (error.retryAfter) {
 *     console.log(`Retry after ${error.retryAfter} seconds`);
 *   }
 * }
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Add user-friendly error message
    const friendlyMessage = getErrorMessage(error);
    error.friendlyMessage = friendlyMessage;

    // Log error in development for debugging
    if (process.env.NODE_ENV === 'development') {
      console.error('API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        message: friendlyMessage,
        details: error.response?.data,
      });
    }

    // Handle 401 Unauthorized - clear auth and redirect to login
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      // Only redirect if not already on login/register pages
      if (currentPath !== '/login' && currentPath !== '/register') {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
    }

    // Handle 403 Forbidden - log access denial
    if (error.response?.status === 403) {
      console.warn('Access forbidden:', error.config?.url);
    }

    // Handle 429 Rate Limiting - parse retry-after header
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      if (retryAfter) {
        error.retryAfter = parseInt(retryAfter, 10);
      }
    }

    return Promise.reject(error);
  }
);
