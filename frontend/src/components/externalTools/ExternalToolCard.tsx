/**
 * ExternalToolCard - Card component for displaying a configured external tool
 */

import React, { useState } from 'react';
import {
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ServerIcon,
  CodeBracketSquareIcon,
  MagnifyingGlassCircleIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { useTestConnection } from '../../hooks/useExternalTools';
import { useToast } from '../../hooks/useToast';
import { Button } from '../common/Button';
import type { ExternalToolConfig, ExternalToolType } from '../../types/externalTool';

interface ExternalToolCardProps {
  tool: ExternalToolConfig;
  onEdit: (tool: ExternalToolConfig) => void;
  onDelete: (tool: ExternalToolConfig) => void;
}

// Tool type icons
const getToolIcon = (toolType: ExternalToolType) => {
  switch (toolType) {
    case 'postgresql':
      return ServerIcon;
    case 'gitlab':
      return CodeBracketSquareIcon;
    case 'elasticsearch':
      return MagnifyingGlassCircleIcon;
    case 'http':
      return GlobeAltIcon;
    default:
      return ServerIcon;
  }
};

// Tool type colors
const getToolColor = (toolType: ExternalToolType) => {
  switch (toolType) {
    case 'postgresql':
      return 'bg-blue-100 text-blue-800';
    case 'gitlab':
      return 'bg-orange-100 text-orange-800';
    case 'elasticsearch':
      return 'bg-yellow-100 text-yellow-800';
    case 'http':
      return 'bg-purple-100 text-purple-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Test status badge
const TestStatusBadge: React.FC<{ status: string | null }> = ({ status }) => {
  if (!status || status === 'not_tested') {
    return (
      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
        <ClockIcon className="w-3 h-3 mr-1" />
        Not Tested
      </span>
    );
  }

  if (status === 'success') {
    return (
      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
        <CheckCircleIcon className="w-3 h-3 mr-1" />
        Connected
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
      <XCircleIcon className="w-3 h-3 mr-1" />
      Failed
    </span>
  );
};

export const ExternalToolCard: React.FC<ExternalToolCardProps> = ({ tool, onEdit, onDelete }) => {
  const [isTesting, setIsTesting] = useState(false);
  const testConnection = useTestConnection();
  const { success: showSuccess, error: showError } = useToast();

  const Icon = getToolIcon(tool.tool_type);
  const colorClass = getToolColor(tool.tool_type);

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      const result = await testConnection.mutateAsync({ id: tool.id });

      if (result.success) {
        showSuccess('Connection test successful!');
      } else {
        showError(`Connection test failed: ${result.message}`);
      }
    } catch (error: unknown) {
      let errorMessage = 'Connection test failed';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      showError(errorMessage);
    } finally {
      setIsTesting(false);
    }
  };

  // Format last tested date
  const lastTestedText = tool.last_tested_at
    ? new Date(tool.last_tested_at).toLocaleString()
    : 'Never';

  return (
    <div className="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-all shadow-sm hover:shadow-md">
      {/* Header */}
      <div className="p-5 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${colorClass}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{tool.tool_name}</h3>
              <p className="text-sm text-gray-500 capitalize">{tool.tool_type}</p>
            </div>
          </div>

          {/* Active status */}
          {tool.is_active ? (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
              Active
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
              Inactive
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="p-5 space-y-3">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Connection Status:</span>
          <TestStatusBadge status={tool.test_status} />
        </div>

        {/* Last Tested */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Last Tested:</span>
          <span className="text-gray-900">{lastTestedText}</span>
        </div>

        {/* Provider */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Provider:</span>
          <span className="text-gray-900 capitalize">{tool.provider}</span>
        </div>

        {/* Error Message (if failed) */}
        {tool.test_status === 'failed' && tool.test_error_message && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-xs text-red-800 font-medium mb-1">Last Error:</p>
            <p className="text-xs text-red-700">{tool.test_error_message}</p>
          </div>
        )}

        {/* Created Date */}
        <div className="pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-500">
            Created {new Date(tool.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-5 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between rounded-b-lg">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleTestConnection}
          disabled={isTesting || !tool.is_active}
          className="flex-1 mr-2"
        >
          {isTesting ? 'Testing...' : 'Test Connection'}
        </Button>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onEdit(tool)}
            className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded transition-colors"
            title="Edit tool"
          >
            <PencilIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => onDelete(tool)}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
            title="Delete tool"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExternalToolCard;
