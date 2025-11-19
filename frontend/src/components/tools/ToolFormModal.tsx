/**
 * ToolFormModal - Modal form for creating and editing tools
 */

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';
import { useCreateTool, useUpdateTool } from '../../hooks/useTools';
import { useToast } from '../../hooks/useToast';
import type { Tool } from '../../types/tool';

const toolSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().optional(),
  tool_type: z.enum(['builtin', 'custom', 'langgraph']),
  configuration: z.record(z.string(), z.any()).optional(),
  schema_definition: z.record(z.string(), z.any()).optional(),
});

type ToolFormData = z.infer<typeof toolSchema>;

interface ToolFormModalProps {
  isOpen: boolean;
  tool?: Tool;
  onClose: () => void;
}

export const ToolFormModal: React.FC<ToolFormModalProps> = ({ isOpen, tool, onClose }) => {
  const isEdit = !!tool;
  const { success: showSuccess, error: showError } = useToast();
  const createTool = useCreateTool();
  const updateTool = useUpdateTool();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ToolFormData>({
    resolver: zodResolver(toolSchema),
    defaultValues: tool
      ? {
          name: tool.name,
          description: tool.description || '',
          tool_type: tool.tool_type,
          configuration: tool.configuration || {},
          schema_definition: tool.schema_definition || {},
        }
      : {
          tool_type: 'custom',
          description: '',
          configuration: {},
          schema_definition: {},
        },
  });

  const onSubmit = async (data: ToolFormData) => {
    try {
      if (isEdit && tool) {
        await updateTool.mutateAsync({ id: tool.id, data });
        showSuccess('Tool updated successfully');
      } else {
        await createTool.mutateAsync(data);
        showSuccess('Tool created successfully');
      }
      reset();
      onClose();
    } catch (error: unknown) {
      let errorMessage = `Failed to ${isEdit ? 'update' : 'create'} tool`;
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      showError(errorMessage);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={isEdit ? 'Edit Tool' : 'Create Tool'} size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Name <span className="text-red-500">*</span>
          </label>
          <Input
            {...register('name')}
            id="name"
            type="text"
            placeholder="calculator, web_search, etc."
            disabled={isSubmitting}
            error={errors.name?.message}
          />
        </div>

        {/* Type */}
        <div>
          <label htmlFor="tool_type" className="block text-sm font-medium text-gray-700 mb-1">
            Type <span className="text-red-500">*</span>
          </label>
          <Select
            {...register('tool_type')}
            id="tool_type"
            options={[
              { value: 'builtin', label: 'Built-in' },
              { value: 'custom', label: 'Custom' },
              { value: 'langgraph', label: 'LangGraph' },
            ]}
            disabled={isSubmitting}
            error={errors.tool_type?.message}
          />
        </div>

        {/* Description */}
        <Textarea
          {...register('description')}
          id="description"
          label="Description"
          rows={3}
          placeholder="Describe what this tool does..."
          disabled={isSubmitting}
          error={errors.description?.message}
        />

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <Button type="button" variant="secondary" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting} disabled={isSubmitting}>
            {isEdit ? 'Update' : 'Create'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default ToolFormModal;
