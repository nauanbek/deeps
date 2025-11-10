/**
 * TemplateCard Component
 * Displays a template in card format with key information
 */

import React from 'react';
import { Template, CATEGORY_INFO } from '../../types/template';
import { SparklesIcon, ChartBarIcon, EyeIcon } from '@heroicons/react/24/outline';

interface TemplateCardProps {
  template: Template;
  onUseTemplate: (template: Template) => void;
  onViewDetails: (template: Template) => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  onUseTemplate,
  onViewDetails,
}) => {
  const categoryInfo = CATEGORY_INFO[template.category];

  // Truncate description to ~100 characters
  const truncatedDescription =
    template.description.length > 100
      ? `${template.description.substring(0, 100)}...`
      : template.description;

  // Show first 3 tags
  const visibleTags = template.tags.slice(0, 3);
  const remainingTags = template.tags.length - visibleTags.length;

  // Get model provider logo/name
  const providerInfo = {
    anthropic: { name: 'Claude', color: 'text-orange-600' },
    openai: { name: 'OpenAI', color: 'text-green-600' },
  };

  const provider = providerInfo[template.config_template.model_provider];

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 border border-gray-200 overflow-hidden group">
      {/* Card Header */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                {template.name}
              </h3>
              {template.is_featured && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  <SparklesIcon className="w-3 h-3" />
                  Featured
                </span>
              )}
            </div>

            {/* Category Badge */}
            <span
              className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${categoryInfo.bgColor} ${categoryInfo.color} ${categoryInfo.borderColor}`}
            >
              <span>{categoryInfo.icon}</span>
              {categoryInfo.label}
            </span>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 min-h-[3rem]">
          {truncatedDescription}
        </p>

        {/* Tags */}
        {template.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {visibleTags.map((tag, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
              >
                {tag}
              </span>
            ))}
            {remainingTags > 0 && (
              <span className="inline-block px-2 py-1 rounded text-xs bg-gray-100 text-gray-500">
                +{remainingTags} more
              </span>
            )}
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
          <div className="flex items-center gap-1">
            <ChartBarIcon className="w-4 h-4" />
            <span>{template.use_count} uses</span>
          </div>
          <div className={`font-medium ${provider.color}`}>{provider.name}</div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => onUseTemplate(template)}
            className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm"
          >
            Use Template
          </button>
          <button
            onClick={() => onViewDetails(template)}
            className="px-4 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors text-gray-700"
            aria-label="View details"
          >
            <EyeIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Loading skeleton for TemplateCard
 */
export const TemplateCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
      <div className="p-6 animate-pulse">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          </div>
        </div>
        <div className="space-y-2 mb-4">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
        <div className="flex gap-2 mb-4">
          <div className="h-6 bg-gray-200 rounded w-16"></div>
          <div className="h-6 bg-gray-200 rounded w-20"></div>
          <div className="h-6 bg-gray-200 rounded w-16"></div>
        </div>
        <div className="flex gap-2">
          <div className="flex-1 h-10 bg-gray-200 rounded-lg"></div>
          <div className="h-10 w-10 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    </div>
  );
};
