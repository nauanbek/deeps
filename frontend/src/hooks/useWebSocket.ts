/**
 * React hook for WebSocket connection management using Socket.IO.
 *
 * Provides a general-purpose WebSocket connection with automatic reconnection,
 * event subscription, and message sending capabilities. Uses Socket.IO client
 * for robust WebSocket communication with fallback transports.
 *
 * @module useWebSocket
 */

import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

/**
 * Options for configuring WebSocket hook behavior.
 */
interface UseWebSocketOptions {
  /** Callback invoked when a message is received */
  onMessage?: (data: unknown) => void;
  /** Callback invoked on WebSocket errors */
  onError?: (error: Error) => void;
  /** Whether to automatically connect on mount. Default: true */
  autoConnect?: boolean;
}

/**
 * Hook to manage WebSocket connection lifecycle.
 *
 * Creates and manages a Socket.IO WebSocket connection with automatic
 * reconnection, event handling, and cleanup. Useful for real-time
 * communication with the backend.
 *
 * @param {UseWebSocketOptions} [options={}] - Configuration options
 * @returns {Object} WebSocket utilities
 * @returns {boolean} isConnected - Whether WebSocket is currently connected
 * @returns {Function} sendMessage - Function to send messages (event, data)
 * @returns {Function} subscribe - Function to subscribe to custom events
 * @returns {Function} unsubscribe - Function to unsubscribe from events
 *
 * @example
 * const { isConnected, sendMessage, subscribe } = useWebSocket({
 *   onMessage: (data) => console.log('Received:', data),
 *   onError: (error) => console.error('WebSocket error:', error)
 * });
 *
 * // Send a message
 * sendMessage('agent_status', { agent_id: 123 });
 *
 * // Subscribe to custom events
 * subscribe('agent_update', (data) => console.log('Agent updated:', data));
 */
export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { onMessage, onError, autoConnect = true } = options;
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!autoConnect) return;

    const socket = io(WS_URL, {
      transports: ['websocket'],
    });

    socket.on('connect', () => {
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('message', (data) => {
      onMessage?.(data);
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
    };
  }, [autoConnect, onMessage, onError]);

  /**
   * Send a message to the server via WebSocket.
   *
   * @param {string} event - Event name to emit
   * @param {unknown} data - Data payload to send
   */
  const sendMessage = (event: string, data: unknown) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  };

  /**
   * Subscribe to a custom WebSocket event.
   *
   * @param {string} event - Event name to listen for
   * @param {Function} callback - Callback invoked when event received
   */
  const subscribe = (event: string, callback: (data: unknown) => void) => {
    socketRef.current?.on(event, callback);
  };

  /**
   * Unsubscribe from a WebSocket event.
   *
   * @param {string} event - Event name to stop listening to
   */
  const unsubscribe = (event: string) => {
    socketRef.current?.off(event);
  };

  return {
    isConnected,
    sendMessage,
    subscribe,
    unsubscribe,
  };
};
