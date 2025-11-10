/**
 * ToolCard component - Displays a single tool in card format
 */

import React from 'react';
import { WrenchIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import type { Tool } from '../../types/tool';

interface ToolCardProps {
  tool: Tool;
  onEdit: () => void;
  onDelete: () => void;
}

export const ToolCard: React.FC<ToolCardProps> = ({ tool, onEdit, onDelete }) => {
  const getTypeColor = (type: string): string => {
    switch (type) {
      case 'builtin':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'custom':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'langgraph':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const configCount = tool.configuration ? Object.keys(tool.configuration).length : 0;

  return (
    <div className="bg-white rounded-lg border-gray-200 p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <WrenchIcon className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{tool.name}</h3>
            <span
              className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(
                tool.tool_type
              )}`}
            >
              {tool.tool_type}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 mb-4 line-clamp-3">
        {tool.description || 'No description provided'}
      </p>

      {/* Configuration Info */}
      {configCount > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500">
            {configCount} configuration option{configCount !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center space-x-2 pt-4 border-t-gray-200">
        <button
          onClick={onEdit}
          className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
          aria-label={`Edit ${tool.name}`}
        >
          <PencilIcon className="w-4 h-4" />
          <span>Edit</span>
        </button>
        <button
          onClick={onDelete}
          className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          aria-label={`Delete ${tool.name}`}
        >
          <TrashIcon className="w-4 h-4" />
          <span>Delete</span>
        </button>
      </div>
    </div>
  );
};

export default ToolCard;
