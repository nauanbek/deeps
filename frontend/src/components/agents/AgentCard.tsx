import React from 'react';
import {
  PencilIcon,
  TrashIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  CogIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { formatRelativeTime, truncate } from '../../utils/formatting';
import type { Agent } from '../../types/agent';

interface AgentCardProps {
  agent: Agent;
  onEdit: (agent: Agent) => void;
  onDelete: (agentId: number) => void;
  onExecute?: (agentId: number) => void;
  onAdvancedConfig?: (agent: Agent) => void;
  onManageTools?: (agent: Agent) => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  agent,
  onEdit,
  onDelete,
  onExecute,
  onAdvancedConfig,
  onManageTools,
}) => {
  const maxDescriptionLength = 150;
  const shouldTruncate = agent.description && agent.description.length > maxDescriptionLength;

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      {/* Header with name and status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {agent.name}
          </h3>
          {agent.description && (
            <p className="text-sm text-gray-600 mt-1">
              {shouldTruncate
                ? truncate(agent.description, maxDescriptionLength)
                : agent.description}
            </p>
          )}
        </div>
        <span
          className={`ml-3 flex-shrink-0 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            agent.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}
        >
          {agent.is_active ? (
            <>
              <CheckCircleIcon className="w-3 h-3 mr-1" />
              Active
            </>
          ) : (
            <>
              <XCircleIcon className="w-3 h-3 mr-1" />
              Inactive
            </>
          )}
        </span>
      </div>

      {/* Model and Configuration */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Model:</span>
          <div className="flex items-center space-x-1">
            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
              {agent.model_provider}
            </span>
            <span className="font-medium text-gray-900">{agent.model_name}</span>
          </div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Temperature:</span>
          <span className="font-medium text-gray-900">{agent.temperature}</span>
        </div>
        {agent.max_tokens && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Max Tokens:</span>
            <span className="font-medium text-gray-900">
              {agent.max_tokens.toLocaleString()}
            </span>
          </div>
        )}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Features:</span>
          <div className="flex items-center space-x-1">
            {agent.planning_enabled && (
              <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                Planning
              </span>
            )}
            {agent.filesystem_enabled && (
              <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-xs font-medium">
                Filesystem
              </span>
            )}
            {!agent.planning_enabled && !agent.filesystem_enabled && (
              <span className="text-gray-500 text-xs">None</span>
            )}
          </div>
        </div>
      </div>

      {/* Footer with timestamp and actions */}
      <div className="pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 mb-3">
          Updated {formatRelativeTime(agent.updated_at || agent.created_at)}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="secondary"
            size="sm"
            className="flex-1"
            onClick={() => onEdit(agent)}
            aria-label={`Edit ${agent.name}`}
          >
            <PencilIcon className="w-4 h-4 mr-1" />
            Edit
          </Button>
          {onManageTools && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onManageTools(agent)}
              aria-label={`Manage tools for ${agent.name}`}
              title="Manage External Tools"
            >
              <WrenchScrewdriverIcon className="w-4 h-4" />
            </Button>
          )}
          {onAdvancedConfig && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onAdvancedConfig(agent)}
              aria-label={`Advanced settings for ${agent.name}`}
              title="Advanced Configuration"
            >
              <CogIcon className="w-4 h-4" />
            </Button>
          )}
          {onExecute && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onExecute(agent.id)}
              aria-label={`Execute ${agent.name}`}
            >
              <PlayIcon className="w-4 h-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(agent.id)}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            aria-label={`Delete ${agent.name}`}
          >
            <TrashIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};

// Loading skeleton for AgentCard
export const AgentCardSkeleton: React.FC = () => {
  return (
    <Card className="animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-full"></div>
        </div>
        <div className="h-6 w-16 bg-gray-200 rounded-full ml-3"></div>
      </div>
      <div className="space-y-2 mb-4">
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      </div>
      <div className="pt-4 border-t border-gray-200">
        <div className="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
        <div className="flex space-x-2">
          <div className="h-8 bg-gray-200 rounded flex-1"></div>
          <div className="h-8 w-8 bg-gray-200 rounded"></div>
          <div className="h-8 w-8 bg-gray-200 rounded"></div>
        </div>
      </div>
    </Card>
  );
};
