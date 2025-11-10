/**
 * React hook for managing toast notifications.
 *
 * Provides a simple API for displaying temporary toast messages
 * with different severity levels (success, error, info, warning).
 * Toasts automatically dismiss after 5 seconds.
 *
 * @module useToast
 */

import { useState, useCallback } from 'react';
import type { ToastType } from '../components/common/Toast';

/**
 * Internal toast data structure.
 */
interface ToastData {
  id: string;
  message: string;
  type: ToastType;
}

/**
 * Hook to manage toast notification state and display.
 *
 * @returns {Object} Toast utilities
 * @returns {ToastData[]} toasts - Current list of active toasts
 * @returns {Function} addToast - Function to add a new toast (message, type)
 * @returns {Function} removeToast - Function to manually dismiss a toast (id)
 * @returns {Function} success - Convenience function for success toasts
 * @returns {Function} error - Convenience function for error toasts
 * @returns {Function} info - Convenience function for info toasts
 * @returns {Function} warning - Convenience function for warning toasts
 *
 * @example
 * const { success, error, toasts } = useToast();
 *
 * // Show success toast
 * success('Agent created successfully!');
 *
 * // Show error toast
 * error('Failed to connect to server');
 *
 * // Render toasts
 * {toasts.map(toast => <Toast key={toast.id} {...toast} />)}
 */
export const useToast = () => {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  /**
   * Add a new toast notification.
   *
   * Toast will automatically dismiss after 5 seconds.
   *
   * @param {string} message - Toast message to display
   * @param {ToastType} [type='info'] - Toast severity level
   * @returns {string} Toast ID (for manual dismissal)
   */
  const addToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substring(7);
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 5000);

    return id;
  }, []);

  /**
   * Manually remove a toast by ID.
   *
   * @param {string} id - Toast ID to remove
   */
  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  /** Show a success toast (green checkmark) */
  const success = useCallback((message: string) => addToast(message, 'success'), [addToast]);

  /** Show an error toast (red X) */
  const error = useCallback((message: string) => addToast(message, 'error'), [addToast]);

  /** Show an info toast (blue i) */
  const info = useCallback((message: string) => addToast(message, 'info'), [addToast]);

  /** Show a warning toast (yellow triangle) */
  const warning = useCallback((message: string) => addToast(message, 'warning'), [addToast]);

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning,
  };
};
