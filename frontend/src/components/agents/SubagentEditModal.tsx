/**
 * SubagentEditModal - Modal for editing an existing subagent configuration
 */

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useUpdateSubagent } from '../../hooks/useSubagents';
import type { Subagent } from '../../types/subagent';

const subagentEditSchema = z.object({
  delegation_prompt: z.string().optional(),
  priority: z.number().int().min(-100).max(100),
});

type SubagentEditFormData = z.infer<typeof subagentEditSchema>;

interface SubagentEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  agentId: number;
  subagent: Subagent;
}

export const SubagentEditModal: React.FC<SubagentEditModalProps> = ({
  isOpen,
  onClose,
  agentId,
  subagent,
}) => {
  const updateSubagent = useUpdateSubagent();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
  } = useForm<SubagentEditFormData>({
    resolver: zodResolver(subagentEditSchema),
    defaultValues: {
      delegation_prompt: subagent.delegation_prompt || '',
      priority: subagent.priority,
    },
  });

  // Update form when subagent prop changes
  useEffect(() => {
    if (isOpen) {
      reset({
        delegation_prompt: subagent.delegation_prompt || '',
        priority: subagent.priority,
      });
    }
  }, [isOpen, subagent, reset]);

  const onSubmit = async (data: SubagentEditFormData) => {
    try {
      await updateSubagent.mutateAsync({
        agentId,
        subagentId: subagent.subagent_id,
        data: {
          delegation_prompt: data.delegation_prompt || '',
          priority: data.priority,
        },
      });
      onClose();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update subagent';
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

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Edit Subagent: ${subagent.subagent.name}`}
      size="lg"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Root Error Display */}
        {errors.root && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">{errors.root.message}</p>
          </div>
        )}

        {/* Subagent Name (Read-only) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Subagent</label>
          <div className="w-full px-3 py-2 bg-gray-50 border-gray-200 rounded-lg text-gray-700">
            {subagent.subagent.name}
          </div>
          <p className="mt-1 text-xs text-gray-500">
            Subagent cannot be changed. Delete and add a new one to change the subagent.
          </p>
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
            disabled={updateSubagent.isPending}
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
            disabled={updateSubagent.isPending}
          />
          <p className="mt-1 text-xs text-gray-500">
            Higher priority subagents are called first. Range: -100 to 100
          </p>
          {errors.priority && <p className="mt-1 text-sm text-red-600">{errors.priority.message}</p>}
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={updateSubagent.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={updateSubagent.isPending}
            disabled={updateSubagent.isPending}
          >
            {updateSubagent.isPending ? 'Updating...' : 'Update'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default SubagentEditModal;
