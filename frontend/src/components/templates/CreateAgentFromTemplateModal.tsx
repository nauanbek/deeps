/**
 * CreateAgentFromTemplateModal Component
 * Modal for creating an agent from a template with optional overrides
 */

import React, { useState } from 'react';
import { Template } from '../../types/template';
import { CreateAgentFromTemplateRequest } from '../../types/template';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface CreateAgentFromTemplateModalProps {
  template: Template | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (templateId: number, data: CreateAgentFromTemplateRequest) => void;
  isLoading?: boolean;
}

export const CreateAgentFromTemplateModal: React.FC<
  CreateAgentFromTemplateModalProps
> = ({ template, isOpen, onClose, onSubmit, isLoading = false }) => {
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    temperature: number;
    maxTokens: number;
  }>({
    name: template?.name || '',
    description: template?.description || '',
    temperature: template?.config_template.temperature || 0.7,
    maxTokens: template?.config_template.max_tokens || 4096,
  });

  // Reset form when template changes
  React.useEffect(() => {
    if (template) {
      setFormData({
        name: template.name,
        description: template.description,
        temperature: template.config_template.temperature,
        maxTokens: template.config_template.max_tokens,
      });
    }
  }, [template]);

  if (!isOpen || !template) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const requestData: CreateAgentFromTemplateRequest = {
      template_id: template.id,
      name: formData.name,
      description: formData.description,
      config_overrides: {
        temperature: formData.temperature,
        max_tokens: formData.maxTokens,
      },
    };

    onSubmit(template.id, requestData);
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && !isLoading) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-agent-title"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-fadeIn">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2
            id="create-agent-title"
            className="text-xl font-bold text-gray-900"
          >
            Create Agent from Template
          </h2>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
            aria-label="Close modal"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="px-6 py-6 space-y-6">
            {/* Template Reference */}
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-primary-900 mb-2">
                Template: {template.name}
              </h3>
              <p className="text-sm text-primary-700">
                This agent will be created with the configuration from this
                template. You can customize the settings below.
              </p>
            </div>

            {/* Agent Name */}
            <div>
              <label
                htmlFor="agent-name"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Agent Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="agent-name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
                disabled={isLoading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="Enter agent name"
              />
            </div>

            {/* Description */}
            <div>
              <label
                htmlFor="agent-description"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Description
              </label>
              <textarea
                id="agent-description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                disabled={isLoading}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="Describe what this agent does"
              />
            </div>

            {/* Configuration Overrides */}
            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Configuration Overrides
              </h3>

              <div className="grid grid-cols-2 gap-6">
                {/* Temperature */}
                <div>
                  <label
                    htmlFor="temperature"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Temperature
                  </label>
                  <input
                    type="number"
                    id="temperature"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        temperature: parseFloat(e.target.value),
                      })
                    }
                    disabled={isLoading}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Default: {template.config_template.temperature}
                  </p>
                </div>

                {/* Max Tokens */}
                <div>
                  <label
                    htmlFor="max-tokens"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    id="max-tokens"
                    min="1"
                    max="100000"
                    step="1"
                    value={formData.maxTokens}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        maxTokens: parseInt(e.target.value),
                      })
                    }
                    disabled={isLoading}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Default: {template.config_template.max_tokens}
                  </p>
                </div>
              </div>
            </div>

            {/* Preview Configuration */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Final Configuration Preview
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Model:</span>{' '}
                  <span className="font-medium text-gray-900">
                    {template.config_template.model_name}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Provider:</span>{' '}
                  <span className="font-medium text-gray-900 capitalize">
                    {template.config_template.model_provider}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Temperature:</span>{' '}
                  <span className="font-medium text-gray-900">
                    {formData.temperature}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Max Tokens:</span>{' '}
                  <span className="font-medium text-gray-900">
                    {formData.maxTokens}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Planning:</span>{' '}
                  <span className="font-medium text-gray-900">
                    {template.config_template.planning_enabled ? 'Yes' : 'No'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Filesystem:</span>{' '}
                  <span className="font-medium text-gray-900">
                    {template.config_template.filesystem_enabled ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3 bg-gray-50">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-white transition-colors text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.name.trim()}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating...' : 'Create Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAgentFromTemplateModal;
