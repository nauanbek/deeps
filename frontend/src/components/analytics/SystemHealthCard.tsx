import React from 'react';
import { SystemPerformance } from '../../types/analytics';

interface SystemHealthCardProps {
  data: SystemPerformance;
  isLoading?: boolean;
  error?: Error | null;
}

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          System Health
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-gray-500">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          System Health
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-red-500">Error loading system data: {error.message}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">
        System Health
      </h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-xs text-gray-600 mb-1">Uptime</p>
          <p className="text-xl font-bold text-gray-900">
            {formatUptime(data.uptime_seconds)}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-xs text-gray-600 mb-1">Active Agents</p>
          <p className="text-xl font-bold text-gray-900">
            {data.active_agents} / {data.total_agents}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-xs text-gray-600 mb-1">Total Executions</p>
          <p className="text-xl font-bold text-gray-900">
            {data.total_executions.toLocaleString()}
          </p>
        </div>
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-xs text-gray-600 mb-1">Last 24h</p>
          <p className="text-xl font-bold text-gray-900">
            {data.executions_last_24h.toLocaleString()}
          </p>
        </div>
      </div>

      <div className="bg-gray-50 p-4 rounded mb-4">
        <p className="text-xs text-gray-600 mb-2">Success Rate (24h)</p>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                data.success_rate_last_24h >= 0.9
                  ? 'bg-green-500'
                  : data.success_rate_last_24h >= 0.7
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${data.success_rate_last_24h * 100}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-gray-900">
            {(data.success_rate_last_24h * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="text-center">
          <p className="text-xs text-gray-600">Avg Response</p>
          <p className="text-sm font-semibold text-gray-900">
            {data.avg_response_time_ms}ms
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">DB Size</p>
          <p className="text-sm font-semibold text-gray-900">
            {data.database_size_mb}MB
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-600">Cache Hit</p>
          <p className="text-sm font-semibold text-gray-900">
            {(data.cache_hit_rate * 100).toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthCard;
