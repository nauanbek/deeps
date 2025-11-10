/**
 * TemplateDetailModal Component
 * Displays full template details in a modal with tabs
 */

import React, { useState } from 'react';
import { Template, CATEGORY_INFO } from '../../types/template';
import {
  XMarkIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  TrashIcon,
  SparklesIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';

interface TemplateDetailModalProps {
  template: Template;
  isOpen: boolean;
  onClose: () => void;
  onUseTemplate: (template: Template) => void;
  onEditTemplate?: (template: Template) => void;
  onDeleteTemplate?: (template: Template) => void;
  onExportTemplate: (templateId: number) => void;
  currentUserId?: number;
}

type Tab = 'overview' | 'configuration' | 'prompt';

export const TemplateDetailModal: React.FC<TemplateDetailModalProps> = ({
  template,
  isOpen,
  onClose,
  onUseTemplate,
  onEditTemplate,
  onDeleteTemplate,
  onExportTemplate,
  currentUserId,
}) => {
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  if (!isOpen) return null;

  const categoryInfo = CATEGORY_INFO[template.category];
  const isOwner = currentUserId === template.created_by_id;

  const providerInfo = {
    anthropic: { name: 'Claude', color: 'text-orange-600' },
    openai: { name: 'OpenAI', color: 'text-green-600' },
  };

  const provider = providerInfo[template.config_template.model_provider];

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const tabs = [
    { id: 'overview' as Tab, label: 'Overview' },
    { id: 'configuration' as Tab, label: 'Configuration' },
    { id: 'prompt' as Tab, label: 'System Prompt' },
  ];

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="template-detail-title"
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-fadeIn">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h2
                id="template-detail-title"
                className="text-2xl font-bold text-gray-900"
              >
                {template.name}
              </h2>
              {template.is_featured && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                  <SparklesIcon className="w-4 h-4" />
                  Featured
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <span
                className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${categoryInfo.bgColor} ${categoryInfo.color} border ${categoryInfo.borderColor}`}
              >
                <span>{categoryInfo.icon}</span>
                {categoryInfo.label}
              </span>
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <ChartBarIcon className="w-4 h-4" />
                {template.use_count} uses
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <nav className="flex gap-6" aria-label="Template details tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Description
                </h3>
                <p className="text-gray-700 leading-relaxed">
                  {template.description}
                </p>
              </div>

              {template.tags.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Tags
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {template.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-block px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 border border-gray-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-1">
                    Created
                  </h3>
                  <p className="text-gray-900">
                    {format(new Date(template.created_at), 'PPP')}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-1">
                    Last Updated
                  </h3>
                  <p className="text-gray-900">
                    {format(new Date(template.updated_at), 'PPP')}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'configuration' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                    Model Provider
                  </h3>
                  <p className={`text-lg font-medium ${provider.color}`}>
                    {provider.name}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                    Model Name
                  </h3>
                  <p className="text-lg font-medium text-gray-900">
                    {template.config_template.model_name}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                    Temperature
                  </h3>
                  <p className="text-lg font-medium text-gray-900">
                    {template.config_template.temperature}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                    Max Tokens
                  </h3>
                  <p className="text-lg font-medium text-gray-900">
                    {template.config_template.max_tokens}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                    Planning Enabled
                  </h3>
                  <p className="text-lg font-medium text-gray-900">
                    {template.config_template.planning_enabled ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                    Filesystem Enabled
                  </h3>
                  <p className="text-lg font-medium text-gray-900">
                    {template.config_template.filesystem_enabled ? 'Yes' : 'No'}
                  </p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                  Tool IDs
                </h3>
                <p className="text-gray-900">
                  {template.config_template.tool_ids.length > 0
                    ? template.config_template.tool_ids.join(', ')
                    : 'None'}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'prompt' && (
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">
                System Prompt
              </h3>
              <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm text-gray-100 font-mono whitespace-pre-wrap">
                  {template.config_template.system_prompt}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex gap-2">
            <button
              onClick={() => onExportTemplate(template.id)}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-white transition-colors text-gray-700"
            >
              <ArrowDownTrayIcon className="w-5 h-5" />
              Export
            </button>
            {isOwner && onEditTemplate && (
              <button
                onClick={() => onEditTemplate(template)}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-white transition-colors text-gray-700"
              >
                <PencilIcon className="w-5 h-5" />
                Edit
              </button>
            )}
            {isOwner && onDeleteTemplate && (
              <button
                onClick={() => onDeleteTemplate(template)}
                className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 rounded-lg hover:bg-red-50 transition-colors text-red-700"
              >
                <TrashIcon className="w-5 h-5" />
                Delete
              </button>
            )}
          </div>
          <button
            onClick={() => onUseTemplate(template)}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Use This Template
          </button>
        </div>
      </div>
    </div>
  );
};

export default TemplateDetailModal;
