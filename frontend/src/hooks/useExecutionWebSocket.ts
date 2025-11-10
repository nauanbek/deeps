import { useEffect, useState, useRef, useCallback } from 'react';
import type { ExecutionTrace } from '../types/execution';

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

interface UseExecutionWebSocketResult {
  traces: ExecutionTrace[];
  isConnected: boolean;
  error: string | null;
  reconnect: () => void;
}

/**
 * Custom hook for WebSocket connection to stream execution traces in real-time
 */
export const useExecutionWebSocket = (
  executionId: number | null
): UseExecutionWebSocketResult => {
  const [traces, setTraces] = useState<ExecutionTrace[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldConnectRef = useRef(true);

  const connect = useCallback(() => {
    if (!executionId || !shouldConnectRef.current) return;

    try {
      const wsUrl = `${WS_BASE_URL}/api/v1/executions/${executionId}/stream`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle different message types
          if (data.type === 'trace' && data.data) {
            setTraces((prev) => [...prev, data.data]);
          } else if (data.type === 'error') {
            setError(data.data?.message || 'WebSocket error');
          } else if (data.type === 'complete') {
            setIsConnected(false);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        setIsConnected(false);

        // Attempt reconnection after 3 seconds
        if (shouldConnectRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to establish WebSocket connection');
    }
  }, [executionId]);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setTraces([]);
    setError(null);
    connect();
  }, [connect]);

  useEffect(() => {
    shouldConnectRef.current = true;
    connect();

    return () => {
      shouldConnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    traces,
    isConnected,
    error,
    reconnect,
  };
};
