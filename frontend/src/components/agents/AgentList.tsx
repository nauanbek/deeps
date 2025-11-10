import React from 'react';
import { AgentCard, AgentCardSkeleton } from './AgentCard';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';
import type { Agent } from '../../types/agent';

interface AgentListProps {
  agents: Agent[];
  isLoading?: boolean;
  isError?: boolean;
  onEdit: (agent: Agent) => void;
  onDelete: (agentId: number) => void;
  onExecute?: (agentId: number) => void;
  onAdvancedConfig?: (agent: Agent) => void;
  onManageTools?: (agent: Agent) => void;
  onRetry?: () => void;
}

export const AgentList: React.FC<AgentListProps> = ({
  agents,
  isLoading = false,
  isError = false,
  onEdit,
  onDelete,
  onExecute,
  onAdvancedConfig,
  onManageTools,
  onRetry,
}) => {
  // Loading state
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <AgentCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <Card className="text-center py-12">
        <div className="flex flex-col items-center">
          <ExclamationCircleIcon className="h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Failed to load agents
          </h3>
          <p className="text-gray-600 mb-4">
            There was an error loading your agents. Please try again.
          </p>
          {onRetry && (
            <Button variant="primary" onClick={onRetry}>
              Retry
            </Button>
          )}
        </div>
      </Card>
    );
  }

  // Empty state
  if (!agents || agents.length === 0) {
    return (
      <Card className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No agents yet</h3>
        <p className="text-gray-600">
          Get started by creating your first AI agent
        </p>
      </Card>
    );
  }

  // Agent grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {agents.map((agent) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          onEdit={onEdit}
          onDelete={onDelete}
          onExecute={onExecute}
          onAdvancedConfig={onAdvancedConfig}
          onManageTools={onManageTools}
        />
      ))}
    </div>
  );
};
