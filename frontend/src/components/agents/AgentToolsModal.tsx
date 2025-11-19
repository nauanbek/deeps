/**
 * AgentToolsModal - Modal for managing external tools attached to an agent
 *
 * Allows users to:
 * - View currently attached tools
 * - Add new tools from configured external tools
 * - Remove tools from agent
 * - See tool status and configuration
 */

import React, { useState, useEffect } from 'react';
import {
  CheckIcon,
  PlusIcon,
  TrashIcon,
  ServerIcon,
  CodeBracketSquareIcon,
  MagnifyingGlassCircleIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { Modal, ModalFooter } from '../common/Modal';
import { Button } from '../common/Button';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { useExternalTools } from '../../hooks/useExternalTools';
import { useUpdateAgent } from '../../hooks/useAgents';
import { useToast } from '../../hooks/useToast';
import type { Agent } from '../../types/agent';
import type { ExternalToolConfig, ExternalToolType } from '../../types/externalTool';

interface AgentToolsModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent: Agent;
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

export const AgentToolsModal: React.FC<AgentToolsModalProps> = ({ isOpen, onClose, agent }) => {
  const [selectedToolIds, setSelectedToolIds] = useState<number[]>([]);
  const [hasChanges, setHasChanges] = useState(false);

  const { success: showSuccess, error: showError } = useToast();
  const { data: toolsResponse, isLoading } = useExternalTools({ is_active: true });
  const updateAgent = useUpdateAgent();

  const availableTools = toolsResponse?.tools || [];

  // Initialize selected tools from agent
  useEffect(() => {
    if (isOpen && agent) {
      setSelectedToolIds(agent.langchain_tool_ids || []);
      setHasChanges(false);
    }
  }, [isOpen, agent]);

  const handleToggleTool = (toolId: number) => {
    setSelectedToolIds((prev) => {
      if (prev.includes(toolId)) {
        return prev.filter((id) => id !== toolId);
      } else {
        return [...prev, toolId];
      }
    });
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateAgent.mutateAsync({
        id: agent.id,
        data: {
          langchain_tool_ids: selectedToolIds,
        },
      });
      showSuccess('Agent tools updated successfully');
      setHasChanges(false);
      onClose();
    } catch (error: unknown) {
      let errorMessage = 'Failed to update agent tools';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      showError(errorMessage);
    }
  };

  const handleCancel = () => {
    if (hasChanges) {
      if (window.confirm('You have unsaved changes. Are you sure you want to close?')) {
        onClose();
      }
    } else {
      onClose();
    }
  };

  const isToolSelected = (toolId: number) => selectedToolIds.includes(toolId);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title={`Manage Tools - ${agent.name}`}
      size="lg"
      showCloseButton={!updateAgent.isPending}
    >
      <div className="space-y-4">
        {/* Description */}
        <p className="text-sm text-gray-600">
          Select external tools to make available to this agent during execution. The agent will be
          able to use these tools to interact with databases, repositories, and APIs.
        </p>

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center items-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && availableTools.length === 0 && (
          <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
            <ServerIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tools configured</h3>
            <p className="mt-1 text-sm text-gray-500">
              Configure external tools in the External Tools page first.
            </p>
            <div className="mt-4">
              <Button
                variant="secondary"
                onClick={() => {
                  window.location.href = '/external-tools';
                }}
              >
                Go to External Tools
              </Button>
            </div>
          </div>
        )}

        {/* Tool List */}
        {!isLoading && availableTools.length > 0 && (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {availableTools.map((tool) => {
              const Icon = getToolIcon(tool.tool_type);
              const colorClass = getToolColor(tool.tool_type);
              const selected = isToolSelected(tool.id);

              return (
                <div
                  key={tool.id}
                  onClick={() => handleToggleTool(tool.id)}
                  className={`relative p-4 border rounded-lg cursor-pointer transition-all ${
                    selected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      {/* Icon */}
                      <div className={`p-2 rounded ${colorClass}`}>
                        <Icon className="w-5 h-5" />
                      </div>

                      {/* Tool Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-gray-900">{tool.tool_name}</h4>
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}
                          >
                            {tool.tool_type}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {tool.test_status === 'success' && (
                            <span className="text-green-600">✓ Connected</span>
                          )}
                          {tool.test_status === 'failed' && (
                            <span className="text-red-600">✗ Connection failed</span>
                          )}
                          {(!tool.test_status || tool.test_status === 'not_tested') && (
                            <span className="text-gray-500">Not tested</span>
                          )}
                          {' • Provider: '}
                          <span className="capitalize">{tool.provider}</span>
                        </p>
                      </div>
                    </div>

                    {/* Selection Checkbox */}
                    <div
                      className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center ${
                        selected
                          ? 'bg-primary-600 border-primary-600'
                          : 'border-gray-300 bg-white'
                      }`}
                    >
                      {selected && <CheckIcon className="w-4 h-4 text-white" />}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Selection Summary */}
        {!isLoading && availableTools.length > 0 && (
          <div className="pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              {selectedToolIds.length} tool{selectedToolIds.length !== 1 ? 's' : ''} selected
            </p>
            {hasChanges && (
              <p className="text-xs text-orange-600 mt-1">
                You have unsaved changes. Click "Save Changes" to apply.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <ModalFooter>
        <Button
          type="button"
          variant="secondary"
          onClick={handleCancel}
          disabled={updateAgent.isPending}
        >
          Cancel
        </Button>
        <Button
          type="button"
          onClick={handleSave}
          disabled={updateAgent.isPending || !hasChanges}
        >
          {updateAgent.isPending ? 'Saving...' : 'Save Changes'}
        </Button>
      </ModalFooter>
    </Modal>
  );
};

export default AgentToolsModal;
