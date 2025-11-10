import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import type { AgentHealth } from '../../types/monitoring';

export interface AgentHealthCardProps {
  health: AgentHealth;
}

export const AgentHealthCard: React.FC<AgentHealthCardProps> = ({ health }) => {
  const getBadgeStyles = (successRate: number): string => {
    if (successRate >= 80) {
      return 'bg-green-100 text-green-800';
    } else if (successRate >= 50) {
      return 'bg-yellow-100 text-yellow-800';
    } else {
      return 'bg-red-100 text-red-800';
    }
  };

  return (
    <div className="bg-white rounded-lg p-4 shadow hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-semibold text-gray-900">{health.agent_name}</h4>
          <p className="text-sm text-gray-500">ID: {health.agent_id}</p>
        </div>
        <div
          className={`px-2 py-1 rounded text-xs font-medium ${getBadgeStyles(
            health.success_rate
          )}`}
        >
          {health.success_rate.toFixed(1)}% success
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-gray-600">Executions</p>
          <p className="font-semibold text-gray-900">{health.total_executions}</p>
        </div>
        <div>
          <p className="text-gray-600">Avg Time</p>
          <p className="font-semibold text-gray-900">
            {health.avg_execution_time.toFixed(1)}s
          </p>
        </div>
        <div>
          <p className="text-gray-600">Success</p>
          <p className="font-semibold text-green-600">{health.success_count}</p>
        </div>
        <div>
          <p className="text-gray-600">Errors</p>
          <p className="font-semibold text-red-600">{health.error_count}</p>
        </div>
      </div>

      {health.last_execution_at && (
        <p className="mt-3 text-xs text-gray-500">
          Last run:{' '}
          {formatDistanceToNow(new Date(health.last_execution_at), {
            addSuffix: true,
          })}
        </p>
      )}
    </div>
  );
};

export default AgentHealthCard;
