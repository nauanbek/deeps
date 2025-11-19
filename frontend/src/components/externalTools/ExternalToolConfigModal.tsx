/**
 * ExternalToolConfigModal - Modal for creating/editing external tool configurations
 *
 * Features:
 * - Dynamic form fields based on tool type
 * - Create and edit modes
 * - Connection testing
 * - Example configurations
 * - Validation with Zod
 */

import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import { Modal, ModalFooter } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Select } from '../common/Select';
import { Textarea } from '../common/Textarea';
import {
  useCreateExternalTool,
  useUpdateExternalTool,
  useTestConnection,
} from '../../hooks/useExternalTools';
import { useToast } from '../../hooks/useToast';
import type { ExternalToolConfig, ExternalToolType } from '../../types/externalTool';

// Validation schema
const toolConfigSchema = z.object({
  tool_name: z
    .string()
    .min(1, 'Tool name is required')
    .max(255, 'Tool name must be less than 255 characters'),
  tool_type: z.enum(['postgresql', 'gitlab', 'elasticsearch', 'http']),
  configuration: z.record(z.string(), z.any()),
});

type ToolConfigFormData = z.infer<typeof toolConfigSchema>;

interface ExternalToolConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  tool?: ExternalToolConfig;
  initialToolType?: ExternalToolType;
}

// Tool type configuration templates
const TOOL_CONFIG_TEMPLATES = {
  postgresql: {
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl_mode: 'prefer',
    read_only: true,
    timeout: 30,
    row_limit: 1000,
  },
  gitlab: {
    gitlab_url: 'https://gitlab.com',
    access_token: '',
    default_project: '',
    rate_limit: 600,
    timeout: 30,
  },
  elasticsearch: {
    host: '',
    port: 9200,
    api_key: '',
    index_patterns: ['logs-*'],
    use_ssl: true,
    verify_certs: true,
    max_results: 1000,
    timeout: 30,
  },
  http: {
    base_url: '',
    auth_type: 'none',
    bearer_token: '',
    api_key: '',
    allowed_domains: [],
    timeout: 30,
  },
};

// Field type definitions
type BaseFieldConfig = {
  name: string;
  label: string;
  type: string;
  required: boolean;
};

type SelectFieldConfig = BaseFieldConfig & {
  type: 'select';
  options: string[];
};

type FieldConfig = BaseFieldConfig | SelectFieldConfig;

// Field definitions for dynamic forms
const FIELD_CONFIGS: Record<ExternalToolType, FieldConfig[]> = {
  postgresql: [
    { name: 'host', label: 'Host', type: 'text', required: true },
    { name: 'port', label: 'Port', type: 'number', required: true },
    { name: 'database', label: 'Database', type: 'text', required: true },
    { name: 'username', label: 'Username', type: 'text', required: true },
    { name: 'password', label: 'Password', type: 'password', required: true },
    {
      name: 'ssl_mode',
      label: 'SSL Mode',
      type: 'select' as const,
      options: ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'],
      required: false,
    },
    { name: 'read_only', label: 'Read Only', type: 'checkbox', required: false },
    { name: 'timeout', label: 'Timeout (seconds)', type: 'number', required: false },
    { name: 'row_limit', label: 'Row Limit', type: 'number', required: false },
  ],
  gitlab: [
    { name: 'gitlab_url', label: 'GitLab URL', type: 'text', required: false },
    { name: 'access_token', label: 'Access Token', type: 'password', required: true },
    {
      name: 'default_project',
      label: 'Default Project (namespace/project)',
      type: 'text',
      required: false,
    },
    { name: 'rate_limit', label: 'Rate Limit (req/min)', type: 'number', required: false },
    { name: 'timeout', label: 'Timeout (seconds)', type: 'number', required: false },
  ],
  elasticsearch: [
    { name: 'host', label: 'Host', type: 'text', required: true },
    { name: 'port', label: 'Port', type: 'number', required: true },
    { name: 'api_key', label: 'API Key', type: 'password', required: true },
    {
      name: 'index_patterns',
      label: 'Index Patterns (comma-separated)',
      type: 'text',
      required: true,
    },
    { name: 'use_ssl', label: 'Use SSL', type: 'checkbox', required: false },
    { name: 'verify_certs', label: 'Verify Certificates', type: 'checkbox', required: false },
    { name: 'max_results', label: 'Max Results', type: 'number', required: false },
    { name: 'timeout', label: 'Timeout (seconds)', type: 'number', required: false },
  ],
  http: [
    { name: 'base_url', label: 'Base URL', type: 'text', required: false },
    {
      name: 'auth_type',
      label: 'Authentication Type',
      type: 'select' as const,
      options: ['none', 'bearer', 'api_key'],
      required: false,
    },
    { name: 'bearer_token', label: 'Bearer Token', type: 'password', required: false },
    { name: 'api_key', label: 'API Key', type: 'password', required: false },
    {
      name: 'allowed_domains',
      label: 'Allowed Domains (comma-separated)',
      type: 'text',
      required: true,
    },
    { name: 'timeout', label: 'Timeout (seconds)', type: 'number', required: false },
  ],
};

export const ExternalToolConfigModal: React.FC<ExternalToolConfigModalProps> = ({
  isOpen,
  onClose,
  tool,
  initialToolType,
}) => {
  const isEditMode = !!tool;
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({});
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const { success: showSuccess, error: showError } = useToast();
  const createTool = useCreateExternalTool();
  const updateTool = useUpdateExternalTool();
  const testConnection = useTestConnection();

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ToolConfigFormData>({
    resolver: zodResolver(toolConfigSchema),
    defaultValues: {
      tool_name: '',
      tool_type: initialToolType || 'postgresql',
      configuration: {},
    },
  });

  const selectedToolType = watch('tool_type');
  const currentConfig = watch('configuration');

  // Initialize form values
  useEffect(() => {
    if (isOpen) {
      if (tool) {
        // Edit mode - populate with existing tool
        reset({
          tool_name: tool.tool_name,
          tool_type: tool.tool_type,
          configuration: tool.configuration,
        });
      } else {
        // Create mode - initialize with template
        const template = initialToolType
          ? TOOL_CONFIG_TEMPLATES[initialToolType]
          : TOOL_CONFIG_TEMPLATES.postgresql;
        reset({
          tool_name: '',
          tool_type: initialToolType || 'postgresql',
          configuration: { ...template },
        });
      }
      setTestResult(null);
    }
  }, [isOpen, tool, initialToolType, reset]);

  // Update configuration template when tool type changes
  useEffect(() => {
    if (!isEditMode && selectedToolType) {
      const template = TOOL_CONFIG_TEMPLATES[selectedToolType];
      setValue('configuration', { ...template });
    }
  }, [selectedToolType, setValue, isEditMode]);

  const handleFormSubmit = async (data: ToolConfigFormData) => {
    // Process configuration before submission
    const processedConfig = { ...data.configuration };

    // Convert comma-separated strings to arrays
    if (selectedToolType === 'elasticsearch' && typeof processedConfig.index_patterns === 'string') {
      processedConfig.index_patterns = processedConfig.index_patterns
        .split(',')
        .map((s: string) => s.trim())
        .filter((s: string) => s);
    }
    if (selectedToolType === 'http' && typeof processedConfig.allowed_domains === 'string') {
      processedConfig.allowed_domains = processedConfig.allowed_domains
        .split(',')
        .map((s: string) => s.trim())
        .filter((s: string) => s);
    }

    try {
      if (isEditMode && tool) {
        await updateTool.mutateAsync({
          id: tool.id,
          data: {
            tool_name: data.tool_name,
            configuration: processedConfig,
          },
        });
        showSuccess(`Tool "${data.tool_name}" updated successfully`);
      } else {
        await createTool.mutateAsync({
          tool_name: data.tool_name,
          tool_type: data.tool_type,
          configuration: processedConfig,
        });
        showSuccess(`Tool "${data.tool_name}" created successfully`);
      }
      onClose();
    } catch (error: unknown) {
      let errorMessage = 'Failed to save tool configuration';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      showError(errorMessage);
    }
  };

  const handleTestConnection = async () => {
    if (!tool && !isEditMode) {
      showError('Please save the tool configuration first before testing');
      return;
    }

    setTestResult(null);
    try {
      const result = await testConnection.mutateAsync({
        id: tool!.id,
      });
      setTestResult(result);
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
      setTestResult({ success: false, message: errorMessage });
      showError(errorMessage);
    }
  };

  const togglePasswordVisibility = (fieldName: string) => {
    setShowPassword((prev) => ({ ...prev, [fieldName]: !prev[fieldName] }));
  };

  const fields = FIELD_CONFIGS[selectedToolType] || [];

  const isSubmitting = createTool.isPending || updateTool.isPending;
  const isTesting = testConnection.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Tool Configuration' : 'Configure External Tool'}
      size="lg"
      showCloseButton={!isSubmitting}
    >
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* Tool Name */}
        <div>
          <label htmlFor="tool_name" className="block text-sm font-medium text-gray-700 mb-1">
            Tool Name <span className="text-red-500">*</span>
          </label>
          <Input
            id="tool_name"
            {...register('tool_name')}
            placeholder="e.g., Production Database, My GitLab"
            error={errors.tool_name?.message}
          />
        </div>

        {/* Tool Type (only in create mode) */}
        {!isEditMode && (
          <div>
            <label htmlFor="tool_type" className="block text-sm font-medium text-gray-700 mb-1">
              Tool Type <span className="text-red-500">*</span>
            </label>
            <Select id="tool_type" {...register('tool_type')}>
              <option value="postgresql">PostgreSQL Database</option>
              <option value="gitlab">GitLab Repository</option>
              <option value="elasticsearch">Elasticsearch Logs</option>
              <option value="http">HTTP API Client</option>
            </Select>
          </div>
        )}

        {/* Tool Type Display (edit mode) */}
        {isEditMode && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tool Type</label>
            <div className="px-3 py-2 bg-gray-50 border border-gray-300 rounded-md text-gray-900 capitalize">
              {tool?.tool_type}
            </div>
          </div>
        )}

        {/* Dynamic Configuration Fields */}
        <div className="border-t border-gray-200 pt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-4">Configuration</h4>
          <div className="space-y-4">
            {fields.map((field) => {
              const configValue = currentConfig?.[field.name];

              if (field.type === 'checkbox') {
                return (
                  <div key={field.name} className="flex items-center">
                    <input
                      type="checkbox"
                      id={field.name}
                      checked={Boolean(configValue)}
                      onChange={(e) => {
                        setValue(`configuration.${field.name}`, e.target.checked);
                      }}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <label htmlFor={field.name} className="ml-2 text-sm text-gray-700">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                  </div>
                );
              }

              if (field.type === 'select') {
                const selectField = field as SelectFieldConfig;
                return (
                  <div key={field.name}>
                    <label htmlFor={field.name} className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <Select
                      id={field.name}
                      value={String(configValue || '')}
                      onChange={(e) => {
                        setValue(`configuration.${field.name}`, e.target.value);
                      }}
                    >
                      {selectField.options.map((opt: string) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </Select>
                  </div>
                );
              }

              if (field.type === 'password') {
                return (
                  <div key={field.name}>
                    <label htmlFor={field.name} className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    <div className="relative">
                      <Input
                        id={field.name}
                        type={showPassword[field.name] ? 'text' : 'password'}
                        value={String(configValue || '')}
                        onChange={(e) => {
                          setValue(`configuration.${field.name}`, e.target.value);
                        }}
                        placeholder={isEditMode ? '***ENCRYPTED***' : ''}
                      />
                      <button
                        type="button"
                        onClick={() => togglePasswordVisibility(field.name)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPassword[field.name] ? (
                          <EyeSlashIcon className="w-5 h-5" />
                        ) : (
                          <EyeIcon className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>
                );
              }

              return (
                <div key={field.name}>
                  <label htmlFor={field.name} className="block text-sm font-medium text-gray-700 mb-1">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <Input
                    id={field.name}
                    type={field.type}
                    value={field.type === 'number' ? Number(configValue || 0) : String(configValue || '')}
                    onChange={(e) => {
                      const value =
                        field.type === 'number' ? parseFloat(e.target.value) : e.target.value;
                      setValue(`configuration.${field.name}`, value);
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Test Result */}
        {testResult && (
          <div
            className={`p-3 rounded-md ${
              testResult.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <div className="flex items-start">
              {testResult.success ? (
                <CheckCircleIcon className="w-5 h-5 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
              ) : (
                <ExclamationCircleIcon className="w-5 h-5 text-red-600 mt-0.5 mr-2 flex-shrink-0" />
              )}
              <div className="flex-1">
                <p
                  className={`text-sm font-medium ${
                    testResult.success ? 'text-green-800' : 'text-red-800'
                  }`}
                >
                  {testResult.success ? 'Connection Successful' : 'Connection Failed'}
                </p>
                <p
                  className={`text-xs mt-1 ${
                    testResult.success ? 'text-green-700' : 'text-red-700'
                  }`}
                >
                  {testResult.message}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <ModalFooter>
          {isEditMode && (
            <Button
              type="button"
              variant="secondary"
              onClick={handleTestConnection}
              disabled={isTesting || isSubmitting}
            >
              {isTesting ? 'Testing...' : 'Test Connection'}
            </Button>
          )}
          <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : isEditMode ? 'Save Changes' : 'Create Tool'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
};

export default ExternalToolConfigModal;
