/**
 * Backend Configuration Tab
 *
 * Allows users to configure storage backends for agents:
 * - StateBackend (ephemeral)
 * - FilesystemBackend (real/virtual FS)
 * - StoreBackend (persistent)
 * - CompositeBackend (hybrid routing)
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../common/Button';
import { JSONSchemaEditor, useJSONEditor } from '../../common/JSONSchemaEditor';
import {
  useBackendConfig,
  useCreateBackendConfig,
  useUpdateBackendConfig,
  useDeleteBackendConfig,
} from '../../../hooks/useAdvancedConfig';
import type { BackendConfig } from '../../../api/advancedConfig';

interface BackendConfigTabProps {
  agentId: number;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

// JSON Schema for backend configuration
const BACKEND_SCHEMA = {
  type: 'object',
  required: ['backend_type', 'config'],
  properties: {
    backend_type: {
      type: 'string',
      enum: ['state', 'filesystem', 'store', 'composite'],
      description: 'Storage backend type',
    },
    config: {
      type: 'object',
      description: 'Backend-specific configuration',
    },
  },
};

// Example configurations for each backend type
const EXAMPLES = {
  state: {
    backend_type: 'state',
    config: {},
  },
  filesystem: {
    backend_type: 'filesystem',
    config: {
      root_dir: '/workspace/agent_123',
      virtual_mode: false,
    },
  },
  store: {
    backend_type: 'store',
    config: {
      namespace: 'agent_123',
    },
  },
  composite: {
    backend_type: 'composite',
    config: {
      routes: {
        '/memories/': { type: 'store' },
        '/scratch/': { type: 'state' },
      },
      default: { type: 'state' },
    },
  },
};

export const BackendConfigTab: React.FC<BackendConfigTabProps> = ({
  agentId,
  onSuccess,
  onError,
}) => {
  // Data fetching
  const { data: existingConfig, isLoading } = useBackendConfig(agentId, true);
  const createMutation = useCreateBackendConfig();
  const updateMutation = useUpdateBackendConfig();
  const deleteMutation = useDeleteBackendConfig();

  // JSON Editor state
  const { value, error, onChange, getParsedValue, isValid, reset } = useJSONEditor();

  // Selected example
  const [selectedExample, setSelectedExample] = useState<keyof typeof EXAMPLES | ''>('');

  // Load existing config into editor
  useEffect(() => {
    if (existingConfig) {
      reset({
        backend_type: existingConfig.backend_type,
        config: existingConfig.config,
      });
    }
  }, [existingConfig, reset]);

  // Handlers
  const handleLoadExample = (exampleKey: keyof typeof EXAMPLES) => {
    setSelectedExample(exampleKey);
    reset(EXAMPLES[exampleKey]);
  };

  const handleSave = async () => {
    if (!isValid()) {
      onError?.('Invalid JSON configuration');
      return;
    }

    const parsedValue = getParsedValue();
    if (!parsedValue) {
      onError?.('Failed to parse JSON');
      return;
    }

    try {
      if (existingConfig) {
        // Update existing
        await updateMutation.mutateAsync({
          agentId,
          data: parsedValue,
        });
        onSuccess?.();
      } else {
        // Create new
        await createMutation.mutateAsync({
          agentId,
          data: parsedValue,
        });
        onSuccess?.();
      }
    } catch (err: unknown) {
      let errorMessage = 'Failed to save backend configuration';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      onError?.(errorMessage);
    }
  };

  const handleDelete = async () => {
    if (!existingConfig) return;

    if (window.confirm('Are you sure you want to delete the backend configuration? This will revert to default StateBackend.')) {
      try {
        await deleteMutation.mutateAsync(agentId);
        reset({ backend_type: 'state', config: {} });
        onSuccess?.();
      } catch (err: unknown) {
        let errorMessage = 'Failed to delete backend configuration';
        if (err && typeof err === 'object' && 'response' in err) {
          const axiosError = err as { response?: { data?: { detail?: string } } };
          errorMessage = axiosError.response?.data?.detail || errorMessage;
        }
        onError?.(errorMessage);
      }
    }
  };

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const isDeleting = deleteMutation.isPending;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600">Loading backend configuration...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-gray-900">Backend Storage Configuration</h3>
        <p className="mt-1 text-sm text-gray-600">
          Configure how the agent stores files and state. StateBackend is ephemeral (default),
          while FilesystemBackend, StoreBackend, and CompositeBackend provide persistent storage.
        </p>
      </div>

      {/* Example selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Load Example Configuration
        </label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {Object.keys(EXAMPLES).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => handleLoadExample(key as keyof typeof EXAMPLES)}
              className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                selectedExample === key
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* JSON Editor */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Configuration (JSON)
        </label>
        <JSONSchemaEditor
          value={value}
          onChange={onChange}
          schema={BACKEND_SCHEMA}
          error={error}
          height="500px"
          placeholder="Enter backend configuration..."
        />
      </div>

      {/* Info boxes */}
      <div className="space-y-3">
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Backend Types:</h4>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li><strong>state:</strong> Ephemeral in-memory storage (default, fastest)</li>
            <li><strong>filesystem:</strong> Real or virtual filesystem access</li>
            <li><strong>store:</strong> Persistent cross-thread storage (PostgreSQL)</li>
            <li><strong>composite:</strong> Hybrid routing (e.g., /memories/ → store)</li>
          </ul>
        </div>

        {existingConfig && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-800">
                  Backend configuration is active. Current type: <strong>{existingConfig.backend_type}</strong>
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div>
          {existingConfig && (
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={isDeleting || isSaving}
            >
              {isDeleting ? 'Deleting...' : 'Delete Configuration'}
            </Button>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="secondary"
            onClick={() => {
              if (existingConfig) {
                reset({
                  backend_type: existingConfig.backend_type,
                  config: existingConfig.config,
                });
              } else {
                reset({ backend_type: 'state', config: {} });
              }
              setSelectedExample('');
            }}
            disabled={isSaving || isDeleting}
          >
            Reset
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={!isValid() || isSaving || isDeleting}
          >
            {isSaving ? 'Saving...' : existingConfig ? 'Update Configuration' : 'Create Configuration'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BackendConfigTab;
