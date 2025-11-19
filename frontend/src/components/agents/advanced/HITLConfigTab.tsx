/**
 * HITL (Human-in-the-Loop) Configuration Tab
 * Configure tool approval workflows
 */

import React, { useState } from 'react';
import { Button } from '../../common/Button';
import { TrashIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import {
  useInterruptConfigs,
  useCreateInterruptConfig,
  useUpdateInterruptConfig,
  useDeleteInterruptConfig,
} from '../../../hooks/useAdvancedConfig';

interface HITLConfigTabProps {
  agentId: number;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

const DECISION_OPTIONS = [
  { value: 'approve', label: 'Approve' },
  { value: 'edit', label: 'Edit' },
  { value: 'reject', label: 'Reject' },
];

export const HITLConfigTab: React.FC<HITLConfigTabProps> = ({
  agentId,
  onSuccess,
  onError,
}) => {
  const { data: configs, isLoading } = useInterruptConfigs(agentId);
  const createMutation = useCreateInterruptConfig();
  const updateMutation = useUpdateInterruptConfig();
  const deleteMutation = useDeleteInterruptConfig();

  const [newToolName, setNewToolName] = useState('');
  const [selectedDecisions, setSelectedDecisions] = useState<string[]>(['approve', 'reject']);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newToolName || selectedDecisions.length === 0) return;

    try {
      await createMutation.mutateAsync({
        agentId,
        data: {
          tool_name: newToolName,
          allowed_decisions: selectedDecisions as Array<'approve' | 'edit' | 'reject'>,
          config: {},
        },
      });
      setNewToolName('');
      setSelectedDecisions(['approve', 'reject']);
      onSuccess?.();
    } catch (err: unknown) {
      let errorMessage = 'Failed to create interrupt config';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      onError?.(errorMessage);
    }
  };

  const handleDelete = async (toolName: string) => {
    if (window.confirm(`Remove HITL approval for "${toolName}"?`)) {
      try {
        await deleteMutation.mutateAsync({ agentId, toolName });
        onSuccess?.();
      } catch (err: unknown) {
        let errorMessage = 'Failed to delete interrupt config';
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosError = err as { response?: { data?: { detail?: string } } };
          errorMessage = axiosError.response?.data?.detail || errorMessage;
        }
        onError?.(errorMessage);
      }
    }
  };

  const toggleDecision = (decision: string) => {
    setSelectedDecisions(prev =>
      prev.includes(decision)
        ? prev.filter(d => d !== decision)
        : [...prev, decision]
    );
  };

  if (isLoading) {
    return <div className="py-12 text-center text-gray-600">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Human-in-the-Loop (HITL)</h3>
        <p className="mt-1 text-sm text-gray-600">
          Configure which tools require human approval before execution.
        </p>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">How it works:</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Agent pauses when calling configured tools</li>
          <li>You can approve, edit args, or reject the action</li>
          <li>Execution resumes based on your decision</li>
        </ul>
      </div>

      {/* Add new config form */}
      <form onSubmit={handleCreate} className="space-y-4 bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900">Add Tool Approval Rule</h4>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tool Name</label>
          <input
            type="text"
            value={newToolName}
            onChange={(e) => setNewToolName(e.target.value)}
            placeholder="e.g., delete_file, send_email"
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Allowed Decisions</label>
          <div className="flex space-x-4">
            {DECISION_OPTIONS.map(option => (
              <label key={option.value} className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedDecisions.includes(option.value)}
                  onChange={() => toggleDecision(option.value)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-4 w-4"
                />
                <span className="ml-2 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={createMutation.isPending || !newToolName || selectedDecisions.length === 0}
        >
          {createMutation.isPending ? 'Adding...' : 'Add Rule'}
        </Button>
      </form>

      {/* Existing configs */}
      <div>
        <h4 className="font-medium text-gray-900 mb-3">
          Configured Tools ({configs?.total || 0})
        </h4>
        {configs && configs.configs.length > 0 ? (
          <div className="space-y-2">
            {configs.configs.map((config) => (
              <div
                key={config.id}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-md p-3"
              >
                <div className="flex items-center space-x-3">
                  <ShieldCheckIcon className="w-5 h-5 text-primary-500" />
                  <div>
                    <div className="text-sm font-medium text-gray-900">{config.tool_name}</div>
                    <div className="text-xs text-gray-500">
                      Decisions: {config.allowed_decisions.join(', ')}
                    </div>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(config.tool_name)}
                  disabled={deleteMutation.isPending}
                >
                  <TrashIcon className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-600 bg-gray-50 p-4 rounded-md">
            No approval rules configured. Add tools that require human approval.
          </div>
        )}
      </div>

      {/* Common tools suggestion */}
      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Common tools to protect:</h4>
        <div className="flex flex-wrap gap-2">
          {['delete_file', 'write_file', 'send_email', 'execute_code'].map(tool => (
            <button
              key={tool}
              type="button"
              onClick={() => setNewToolName(tool)}
              className="text-xs px-2 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-700"
            >
              {tool}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HITLConfigTab;
