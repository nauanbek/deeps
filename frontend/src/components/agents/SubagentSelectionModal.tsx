/**
 * SubagentSelectionModal - Modal for adding a new subagent to an agent
 */

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useAgents } from '../../hooks/useAgents';
import { useAddSubagent } from '../../hooks/useSubagents';

const subagentSchema = z.object({
  subagent_id: z.number().min(1, 'Subagent is required'),
  delegation_prompt: z.string().optional(),
  priority: z.number().int().min(-100).max(100),
});

type SubagentFormData = z.infer<typeof subagentSchema>;

interface SubagentSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentId: number;
  currentAgentName?: string;
}

export const SubagentSelectionModal: React.FC<SubagentSelectionModalProps> = ({
  isOpen,
  onClose,
  agentId,
  currentAgentName,
}) => {
  const { data: agents, isLoading: isLoadingAgents } = useAgents();
  const addSubagent = useAddSubagent();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
  } = useForm<SubagentFormData>({
    resolver: zodResolver(subagentSchema),
    defaultValues: {
      subagent_id: 0,
      delegation_prompt: '',
      priority: 0,
    },
  });

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      reset({
        subagent_id: 0,
        delegation_prompt: '',
        priority: 0,
      });
    }
  }, [isOpen, reset]);

  const onSubmit = async (data: SubagentFormData) => {
    try {
      await addSubagent.mutateAsync({
        agentId,
        data: {
          subagent_id: data.subagent_id,
          delegation_prompt: data.delegation_prompt || '',
          priority: data.priority,
        },
      });
      reset();
      onClose();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to add subagent';
      setError('root', {
        type: 'manual',
        message: errorMessage,
      });
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  // Filter out the current agent from the list
  const availableAgents = agents?.filter((agent) => agent.id !== agentId) || [];

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={currentAgentName ? `Add Subagent to ${currentAgentName}` : 'Add Subagent'}
      size="lg"
    >
      {isLoadingAgents ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Loading agents...</span>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Root Error Display */}
          {errors.root && (
            <div className="bg-red-50 border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{errors.root.message}</p>
            </div>
          )}

          {/* Subagent Selection */}
          <div>
            <label htmlFor="subagent_id" className="block text-sm font-medium text-gray-700 mb-1">
              Subagent <span className="text-red-500">*</span>
            </label>
            <select
              id="subagent_id"
              {...register('subagent_id', { valueAsNumber: true })}
              className="w-full px-3 py-2 border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              disabled={addSubagent.isPending}
            >
              <option value="">Select an agent...</option>
              {availableAgents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
            {errors.subagent_id && (
              <p className="mt-1 text-sm text-red-600">{errors.subagent_id.message}</p>
            )}
          </div>

          {/* Delegation Prompt */}
          <div>
            <label
              htmlFor="delegation_prompt"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Delegation Prompt (optional)
            </label>
            <textarea
              id="delegation_prompt"
              {...register('delegation_prompt')}
              rows={4}
              className="w-full px-3 py-2 border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Provide custom instructions for delegating tasks to this subagent..."
              disabled={addSubagent.isPending}
            />
            <p className="mt-1 text-xs text-gray-500">
              If not provided, the subagent will use its default system prompt.
            </p>
            {errors.delegation_prompt && (
              <p className="mt-1 text-sm text-red-600">{errors.delegation_prompt.message}</p>
            )}
          </div>

          {/* Priority */}
          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <input
              id="priority"
              type="number"
              {...register('priority', { valueAsNumber: true })}
              min={-100}
              max={100}
              className="w-full px-3 py-2 border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              disabled={addSubagent.isPending}
            />
            <p className="mt-1 text-xs text-gray-500">
              Higher priority subagents are called first. Range: -100 to 100 (default: 0)
            </p>
            {errors.priority && (
              <p className="mt-1 text-sm text-red-600">{errors.priority.message}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={addSubagent.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" isLoading={addSubagent.isPending} disabled={addSubagent.isPending}>
              {addSubagent.isPending ? 'Adding...' : 'Add Subagent'}
            </Button>
          </div>
        </form>
      )}
    </Modal>
  );
};

export default SubagentSelectionModal;
