import React, { useEffect, useState, Suspense, lazy } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { Modal, ModalFooter } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';
import { ComponentLoadingFallback } from '../common/LoadingFallback';
import SubagentManager from './SubagentManager';
import type { Agent, AgentCreate, AgentUpdate } from '../../types/agent';

// Lazy load Monaco Editor (heavy dependency)
const Editor = lazy(() => import('@monaco-editor/react').then(module => ({ default: module.default })));

// Validation schema
const agentSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().optional().nullable(),
  model_provider: z.enum(['anthropic', 'openai']),
  model_name: z.string().min(1, 'Model is required'),
  temperature: z.number().min(0, 'Must be at least 0').max(2, 'Must be at most 2'),
  max_tokens: z.number().min(1, 'Must be at least 1').max(100000, 'Must be at most 100,000').nullable(),
  system_prompt: z.string().min(1, 'System prompt is required'),
  planning_enabled: z.boolean(),
  filesystem_enabled: z.boolean(),
});

type AgentFormData = z.infer<typeof agentSchema>;

interface AgentFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AgentFormData) => Promise<void>;
  agent?: Agent | null;
  isSubmitting?: boolean;
}

const MODEL_OPTIONS = {
  anthropic: [
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
  ],
  openai: [
    { value: 'gpt-4-turbo-preview', label: 'GPT-4 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
};

export const AgentFormModal: React.FC<AgentFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  agent,
  isSubmitting = false,
}) => {
  const isEditMode = !!agent;
  const [isSubagentsExpanded, setIsSubagentsExpanded] = useState(false);

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: {
      name: '',
      description: '',
      model_provider: 'anthropic',
      model_name: 'claude-3-5-sonnet-20241022',
      temperature: 0.7,
      max_tokens: 4096,
      system_prompt: 'You are a helpful AI assistant.',
      planning_enabled: false,
      filesystem_enabled: false,
    },
  });

  // Watch model provider to update model options
  const selectedProvider = watch('model_provider');

  // Reset form when agent changes or modal opens
  useEffect(() => {
    if (isOpen) {
      if (agent) {
        reset({
          name: agent.name,
          description: agent.description || '',
          model_provider: agent.model_provider as 'anthropic' | 'openai',
          model_name: agent.model_name,
          temperature: agent.temperature,
          max_tokens: agent.max_tokens,
          system_prompt: agent.system_prompt,
          planning_enabled: agent.planning_enabled,
          filesystem_enabled: agent.filesystem_enabled,
        });
      } else {
        reset({
          name: '',
          description: '',
          model_provider: 'anthropic',
          model_name: 'claude-3-5-sonnet-20241022',
          temperature: 0.7,
          max_tokens: 4096,
          system_prompt: 'You are a helpful AI assistant.',
          planning_enabled: false,
          filesystem_enabled: false,
        });
      }
    }
  }, [isOpen, agent, reset]);

  // Update model_name when provider changes
  useEffect(() => {
    if (selectedProvider && !isEditMode) {
      const firstModel = MODEL_OPTIONS[selectedProvider][0]?.value;
      if (firstModel) {
        setValue('model_name', firstModel);
      }
    }
  }, [selectedProvider, setValue, isEditMode]);

  const handleFormSubmit = async (data: AgentFormData) => {
    try {
      await onSubmit(data);
      onClose();
    } catch (error) {
      // Error handling is done in parent component
      console.error('Form submission error:', error);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Agent' : 'Create Agent'}
      size="xl"
      showCloseButton={!isSubmitting}
    >
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Name <span className="text-red-500">*</span>
          </label>
          <Input
            {...register('name')}
            id="name"
            type="text"
            placeholder="My Agent"
            disabled={isSubmitting}
            error={errors.name?.message}
          />
        </div>

        {/* Description */}
        <Textarea
          {...register('description')}
          id="description"
          label="Description"
          rows={3}
          placeholder="Describe what this agent does..."
          disabled={isSubmitting}
          error={errors.description?.message}
        />

        {/* Model Provider and Name */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="model_provider" className="block text-sm font-medium text-gray-700 mb-1">
              Model Provider <span className="text-red-500">*</span>
            </label>
            <Select
              {...register('model_provider')}
              id="model_provider"
              options={[
                { value: 'anthropic', label: 'Anthropic' },
                { value: 'openai', label: 'OpenAI' },
              ]}
              disabled={isSubmitting}
              error={errors.model_provider?.message}
            />
          </div>

          <div>
            <label htmlFor="model_name" className="block text-sm font-medium text-gray-700 mb-1">
              Model <span className="text-red-500">*</span>
            </label>
            <Select
              {...register('model_name')}
              id="model_name"
              options={MODEL_OPTIONS[selectedProvider] || []}
              disabled={isSubmitting}
              error={errors.model_name?.message}
            />
          </div>
        </div>

        {/* Temperature and Max Tokens */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="temperature" className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {watch('temperature')}
            </label>
            <input
              {...register('temperature', { valueAsNumber: true })}
              type="range"
              id="temperature"
              min="0"
              max="2"
              step="0.1"
              className="w-full"
              disabled={isSubmitting}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Precise (0)</span>
              <span>Balanced (1)</span>
              <span>Creative (2)</span>
            </div>
            {errors.temperature && (
              <p className="mt-1 text-sm text-red-600">{errors.temperature.message}</p>
            )}
          </div>

          <Input
            {...register('max_tokens', {
              valueAsNumber: true,
              setValueAs: (v) => v === '' ? null : Number(v)
            })}
            id="max_tokens"
            label="Max Tokens"
            type="number"
            min={1}
            max={100000}
            placeholder="4096"
            disabled={isSubmitting}
            error={errors.max_tokens?.message}
          />
        </div>

        {/* System Prompt */}
        <div>
          <label htmlFor="system_prompt" className="block text-sm font-medium text-gray-700 mb-1">
            System Prompt <span className="text-red-500">*</span>
          </label>
          <Controller
            name="system_prompt"
            control={control}
            render={({ field }) => (
              <div className="border-gray-300 rounded-md overflow-hidden">
                <Suspense fallback={<ComponentLoadingFallback />}>
                  <Editor
                    height="300px"
                    defaultLanguage="markdown"
                    theme="vs-light"
                    value={field.value}
                    onChange={(value) => field.onChange(value || '')}
                    options={{
                      minimap: { enabled: false },
                      lineNumbers: 'on',
                      wordWrap: 'on',
                      scrollBeyondLastLine: false,
                      fontSize: 14,
                      readOnly: isSubmitting,
                    }}
                  />
                </Suspense>
              </div>
            )}
          />
          {errors.system_prompt && (
            <p className="mt-1 text-sm text-red-600">{errors.system_prompt.message}</p>
          )}
        </div>

        {/* Feature Toggles */}
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg pointer-events-auto">
            <div className="flex-1 pointer-events-none">
              <label htmlFor="planning_enabled" className="text-sm font-medium text-gray-900">
                Planning Enabled
              </label>
              <p className="text-xs text-gray-600 mt-1">
                Enable the planning tool (write_todos) for structured task decomposition
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                {...register('planning_enabled')}
                type="checkbox"
                id="planning_enabled"
                className="sr-only peer"
                disabled={isSubmitting}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus-visible:outline-none peer-focus-visible:ring-4 peer-focus-visible:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg pointer-events-auto">
            <div className="flex-1 pointer-events-none">
              <label htmlFor="filesystem_enabled" className="text-sm font-medium text-gray-900">
                Filesystem Enabled
              </label>
              <p className="text-xs text-gray-600 mt-1">
                Enable virtual filesystem middleware for context management
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                {...register('filesystem_enabled')}
                type="checkbox"
                id="filesystem_enabled"
                className="sr-only peer"
                disabled={isSubmitting}
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus-visible:outline-none peer-focus-visible:ring-4 peer-focus-visible:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>

        {/* Subagent Orchestration - Only in Edit Mode */}
        {isEditMode && agent && (
          <div className="border-t border-gray-200 pt-6">
            <button
              type="button"
              onClick={() => setIsSubagentsExpanded(!isSubagentsExpanded)}
              className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              disabled={isSubmitting}
            >
              <div className="flex-1 text-left">
                <h3 className="text-sm font-medium text-gray-900">Subagent Orchestration</h3>
                <p className="text-xs text-gray-600 mt-1">
                  Configure subagents for hierarchical task delegation
                </p>
              </div>
              {isSubagentsExpanded ? (
                <ChevronUpIcon className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronDownIcon className="w-5 h-5 text-gray-500" />
              )}
            </button>

            {isSubagentsExpanded && (
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <SubagentManager agentId={agent.id} />
              </div>
            )}
          </div>
        )}

        <ModalFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isSubmitting}
            disabled={isSubmitting}
          >
            {isSubmitting
              ? isEditMode
                ? 'Updating...'
                : 'Creating...'
              : isEditMode
              ? 'Update Agent'
              : 'Create Agent'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
};

export default AgentFormModal;
