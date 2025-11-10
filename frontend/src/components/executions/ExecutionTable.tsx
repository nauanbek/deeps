import React from 'react';
import type { Execution } from '../../types/execution';
import { formatRelativeTime, formatDuration, truncate } from '../../utils/formatting';
import { STATUS_COLORS } from '../../utils/constants';
import { Loading } from '../common/Loading';

interface ExecutionTableProps {
  executions: Execution[];
  onViewDetails?: (id: number) => void;
  onCancel?: (id: number) => void;
  isLoading?: boolean;
}

export const ExecutionTable: React.FC<ExecutionTableProps> = ({
  executions,
  onViewDetails,
  onCancel,
  isLoading = false,
}) => {
  if (isLoading) {
    return <Loading text="Loading executions..." />;
  }

  if (executions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900">No executions found</h3>
        <p className="text-gray-600 mt-2">
          Executions will appear here when agents are run
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      {/* Desktop Table View */}
      <div className="hidden md:block">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Agent
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Input
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Started
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {executions.map((execution) => (
              <tr key={execution.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {execution.agent_name || `Agent ${execution.agent_id}`}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        STATUS_COLORS[execution.status]
                      }`}
                    >
                      {execution.status}
                    </span>
                    {execution.status === 'running' && (
                      <div className="flex space-x-1" aria-hidden="true">
                        <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" />
                        <div
                          className="w-1 h-1 bg-blue-600 rounded-full animate-pulse"
                          style={{ animationDelay: '0.2s' }}
                        />
                        <div
                          className="w-1 h-1 bg-blue-600 rounded-full animate-pulse"
                          style={{ animationDelay: '0.4s' }}
                        />
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 max-w-xs">
                    {truncate(execution.input_text, 50)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatDuration(execution.duration_seconds)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {formatRelativeTime(execution.started_at)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                  <button
                    onClick={() => onViewDetails?.(execution.id)}
                    className="text-primary-600 hover:text-primary-900 font-medium"
                    aria-label={`View details for ${execution.agent_name || `Agent ${execution.agent_id}`} execution`}
                  >
                    View
                  </button>
                  {execution.status === 'running' && (
                    <button
                      onClick={() => onCancel?.(execution.id)}
                      className="text-red-600 hover:text-red-900 font-medium"
                      aria-label={`Cancel execution for ${execution.agent_name || `Agent ${execution.agent_id}`}`}
                    >
                      Cancel
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {executions.map((execution) => (
          <div
            key={execution.id}
            className="bg-white rounded-lg shadow p-4 space-y-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-gray-900">
                  {execution.agent_name || `Agent ${execution.agent_id}`}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  {formatRelativeTime(execution.started_at)}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    STATUS_COLORS[execution.status]
                  }`}
                >
                  {execution.status}
                </span>
                {execution.status === 'running' && (
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" />
                    <div
                      className="w-1 h-1 bg-blue-600 rounded-full animate-pulse"
                      style={{ animationDelay: '0.2s' }}
                    />
                    <div
                      className="w-1 h-1 bg-blue-600 rounded-full animate-pulse"
                      style={{ animationDelay: '0.4s' }}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="text-sm text-gray-700">
              <span className="font-medium">Input:</span>{' '}
              {truncate(execution.input_text, 100)}
            </div>

            <div className="text-sm text-gray-600">
              <span className="font-medium">Duration:</span>{' '}
              {formatDuration(execution.duration_seconds)}
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => onViewDetails?.(execution.id)}
                className="flex-1 px-3 py-2 bg-primary-600 text-white text-sm font-medium rounded hover:bg-primary-700"
                aria-label="View"
              >
                View Details
              </button>
              {execution.status === 'running' && (
                <button
                  onClick={() => onCancel?.(execution.id)}
                  className="px-3 py-2 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700"
                  aria-label="Cancel"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
