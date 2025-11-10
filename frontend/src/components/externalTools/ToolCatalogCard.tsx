/**
 * ToolCatalogCard - Card component for displaying a tool in the marketplace catalog
 */

import React from 'react';
import {
  ServerIcon,
  CodeBracketSquareIcon,
  MagnifyingGlassCircleIcon,
  GlobeAltIcon,
  PlusCircleIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common/Button';
import type { ToolCatalogItem, ExternalToolType } from '../../types/externalTool';

interface ToolCatalogCardProps {
  catalogItem: ToolCatalogItem;
  onConfigure: (toolType: ExternalToolType) => void;
}

// Tool type icons
const getToolIcon = (toolType: ExternalToolType) => {
  switch (toolType) {
    case 'postgresql':
      return ServerIcon;
    case 'gitlab':
      return CodeBracketSquareIcon;
    case 'elasticsearch':
      return MagnifyingGlassCircleIcon;
    case 'http':
      return GlobeAltIcon;
    default:
      return ServerIcon;
  }
};

// Tool type colors
const getToolColor = (toolType: ExternalToolType) => {
  switch (toolType) {
    case 'postgresql':
      return 'bg-blue-500';
    case 'gitlab':
      return 'bg-orange-500';
    case 'elasticsearch':
      return 'bg-yellow-500';
    case 'http':
      return 'bg-purple-500';
    default:
      return 'bg-gray-500';
  }
};

// Category badge colors
const getCategoryColor = (category: string) => {
  switch (category) {
    case 'database':
      return 'bg-blue-100 text-blue-800';
    case 'git':
      return 'bg-orange-100 text-orange-800';
    case 'logs':
      return 'bg-yellow-100 text-yellow-800';
    case 'http':
      return 'bg-purple-100 text-purple-800';
    case 'monitoring':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export const ToolCatalogCard: React.FC<ToolCatalogCardProps> = ({ catalogItem, onConfigure }) => {
  const Icon = getToolIcon(catalogItem.tool_type);
  const colorClass = getToolColor(catalogItem.tool_type);
  const categoryColor = getCategoryColor(catalogItem.category);

  return (
    <div className="bg-white rounded-lg border border-gray-200 hover:border-primary-300 transition-all shadow-sm hover:shadow-md group">
      {/* Header with Icon */}
      <div className={`${colorClass} p-6 rounded-t-lg`}>
        <Icon className="w-12 h-12 text-white" />
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xl font-semibold text-gray-900">{catalogItem.name}</h3>
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${categoryColor}`}>
            {catalogItem.category}
          </span>
        </div>

        <p className="text-sm text-gray-600 mb-4 line-clamp-3">{catalogItem.description}</p>

        {/* Configuration Info */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Provider:</span>
            <span className="font-medium text-gray-900 capitalize">{catalogItem.provider}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Required Fields:</span>
            <span className="font-medium text-gray-900">{catalogItem.required_fields.length}</span>
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Optional Fields:</span>
            <span className="font-medium text-gray-900">{catalogItem.optional_fields.length}</span>
          </div>
        </div>

        {/* Required Fields List */}
        {catalogItem.required_fields.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-700 mb-2">Required Configuration:</p>
            <div className="flex flex-wrap gap-1">
              {catalogItem.required_fields.map((field) => (
                <span
                  key={field}
                  className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                >
                  {field}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Configure Button */}
        <div className="mt-6">
          <Button
            onClick={() => onConfigure(catalogItem.tool_type)}
            className="w-full flex items-center justify-center space-x-2"
            variant="primary"
          >
            <PlusCircleIcon className="w-5 h-5" />
            <span>Configure</span>
          </Button>
        </div>
      </div>

      {/* Feature Tags (Optional Fields) */}
      {catalogItem.optional_fields.length > 0 && (
        <div className="px-6 pb-6">
          <details className="group/details">
            <summary className="text-xs font-medium text-gray-600 cursor-pointer hover:text-gray-900 transition-colors">
              Optional Features ({catalogItem.optional_fields.length})
            </summary>
            <div className="mt-2 flex flex-wrap gap-1">
              {catalogItem.optional_fields.map((field) => (
                <span
                  key={field}
                  className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-50 text-gray-600"
                >
                  {field}
                </span>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default ToolCatalogCard;
