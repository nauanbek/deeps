/**
 * ToolConnectionStatus - Real-time connection status indicator with auto-refresh
 *
 * Features:
 * - Auto-refreshes connection status every 60 seconds
 * - Visual indicators (connected/failed/testing)
 * - Manual refresh button
 * - Last tested timestamp
 * - Animated pulsing for active connections
 */

import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useTestConnection, useExternalTool } from '../../hooks/useExternalTools';
import { useToast } from '../../hooks/useToast';
import type { ExternalToolConfig, TestStatus } from '../../types/externalTool';

interface ToolConnectionStatusProps {
  toolId: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  showRefreshButton?: boolean;
  compact?: boolean;
}

export const ToolConnectionStatus: React.FC<ToolConnectionStatusProps> = ({
  toolId,
  autoRefresh = true,
  refreshInterval = 60000, // 60 seconds default
  showRefreshButton = true,
  compact = false,
}) => {
  const [isManualTesting, setIsManualTesting] = useState(false);
  const { error: showError } = useToast();

  // Fetch tool data with auto-refresh
  const { data: tool, refetch } = useExternalTool(toolId);
  const testConnection = useTestConnection();

  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !tool?.is_active) return;

    const interval = setInterval(() => {
      refetch();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, refetch, tool?.is_active]);

  const handleManualTest = async () => {
    if (!tool) return;

    setIsManualTesting(true);
    try {
      await testConnection.mutateAsync({ id: tool.id });
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Connection test failed';
      showError(errorMessage);
    } finally {
      setIsManualTesting(false);
    }
  };

  if (!tool) {
    return (
      <div className="flex items-center space-x-2 text-gray-400">
        <div className="w-2 h-2 bg-gray-300 rounded-full" />
        <span className="text-xs">Loading...</span>
      </div>
    );
  }

  const getStatusDisplay = (status: TestStatus | null) => {
    if (isManualTesting) {
      return {
        icon: ArrowPathIcon,
        color: 'text-blue-600',
        bgColor: 'bg-blue-100',
        dotColor: 'bg-blue-500',
        label: 'Testing...',
        animate: true,
      };
    }

    switch (status) {
      case 'success':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          dotColor: 'bg-green-500',
          label: 'Connected',
          animate: false,
        };
      case 'failed':
        return {
          icon: XCircleIcon,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          dotColor: 'bg-red-500',
          label: 'Failed',
          animate: false,
        };
      default:
        return {
          icon: ClockIcon,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          dotColor: 'bg-gray-400',
          label: 'Not Tested',
          animate: false,
        };
    }
  };

  const statusDisplay = getStatusDisplay(tool.test_status);
  const Icon = statusDisplay.icon;

  // Format last tested time
  const getLastTestedText = () => {
    if (!tool.last_tested_at) return 'Never tested';

    const lastTested = new Date(tool.last_tested_at);
    const now = new Date();
    const diffMs = now.getTime() - lastTested.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  if (compact) {
    return (
      <div className="flex items-center space-x-2">
        {/* Status Dot with Animation */}
        <div className="relative flex items-center">
          <div
            className={`w-2 h-2 rounded-full ${statusDisplay.dotColor} ${
              statusDisplay.animate ? 'animate-pulse' : ''
            }`}
          />
          {statusDisplay.animate && (
            <div
              className={`absolute w-2 h-2 rounded-full ${statusDisplay.dotColor} animate-ping opacity-75`}
            />
          )}
        </div>

        {/* Status Text */}
        <span className={`text-xs font-medium ${statusDisplay.color}`}>
          {statusDisplay.label}
        </span>

        {/* Manual Refresh Button */}
        {showRefreshButton && !isManualTesting && tool.is_active && (
          <button
            onClick={handleManualTest}
            className="ml-1 p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Test connection"
          >
            <ArrowPathIcon className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Status Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Icon
            className={`w-4 h-4 ${statusDisplay.color} ${
              statusDisplay.animate ? 'animate-spin' : ''
            }`}
          />
          <span className={`text-sm font-medium ${statusDisplay.color}`}>
            {statusDisplay.label}
          </span>
        </div>

        {showRefreshButton && !isManualTesting && tool.is_active && (
          <button
            onClick={handleManualTest}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded hover:bg-gray-100"
            title="Refresh connection status"
          >
            <ArrowPathIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Last Tested Time */}
      <div className="text-xs text-gray-500">
        Last tested: {getLastTestedText()}
      </div>

      {/* Error Message */}
      {tool.test_status === 'failed' && tool.test_error_message && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          {tool.test_error_message}
        </div>
      )}

      {/* Auto-refresh Indicator */}
      {autoRefresh && tool.is_active && (
        <div className="text-xs text-gray-400 flex items-center space-x-1">
          <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" />
          <span>Auto-refreshing every {refreshInterval / 1000}s</span>
        </div>
      )}
    </div>
  );
};

/**
 * Simple connection status badge for inline use
 */
export const ToolConnectionBadge: React.FC<{ status: TestStatus | null }> = ({ status }) => {
  const getStatusStyle = () => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-3 h-3" />;
      case 'failed':
        return <XCircleIcon className="w-3 h-3" />;
      default:
        return <ClockIcon className="w-3 h-3" />;
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case 'success':
        return 'Connected';
      case 'failed':
        return 'Failed';
      default:
        return 'Not Tested';
    }
  };

  return (
    <span
      className={`inline-flex items-center space-x-1 px-2 py-1 rounded border text-xs font-medium ${getStatusStyle()}`}
    >
      {getStatusIcon()}
      <span>{getStatusLabel()}</span>
    </span>
  );
};

export default ToolConnectionStatus;
