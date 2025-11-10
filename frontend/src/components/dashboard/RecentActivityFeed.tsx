import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import type { Execution } from '../../types/execution';

export interface RecentActivityFeedProps {
  executions: Execution[];
}

export const RecentActivityFeed: React.FC<RecentActivityFeedProps> = ({ executions }) => {
  const getStatusDotColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'running':
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusBadgeColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg p-6 shadow">
      <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
      <div className="space-y-4">
        {executions.map((execution) => (
          <div key={execution.id} className="flex items-start space-x-3">
            <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${getStatusDotColor(execution.status)}`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-gray-900">
                {execution.agent_name || `Agent ${execution.agent_id}`}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {execution.input_text}
              </p>
              <p className="text-xs text-gray-400">
                {formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })}
              </p>
            </div>
            <div
              className={`px-2 py-1 rounded text-xs font-medium flex-shrink-0 ${getStatusBadgeColor(
                execution.status
              )}`}
            >
              {execution.status}
            </div>
          </div>
        ))}
      </div>

      {executions.length === 0 && (
        <p className="text-center text-gray-500 py-8">No recent activity</p>
      )}
    </div>
  );
};

export default RecentActivityFeed;
