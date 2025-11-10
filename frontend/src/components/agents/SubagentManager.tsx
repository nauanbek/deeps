/**
 * SubagentManager component - Manages subagents for a parent agent
 */

import React, { useState } from 'react';
import { PlusIcon, PencilIcon, TrashIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import { useAgentSubagents, useRemoveSubagent } from '../../hooks/useSubagents';
import SubagentSelectionModal from './SubagentSelectionModal';
import SubagentEditModal from './SubagentEditModal';
import type { Subagent } from '../../types/subagent';

interface SubagentManagerProps {
  agentId: number;
}

export const SubagentManager: React.FC<SubagentManagerProps> = ({ agentId }) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingSubagent, setEditingSubagent] = useState<Subagent | null>(null);

  const { data: subagents, isLoading, isError } = useAgentSubagents(agentId);
  const removeSubagent = useRemoveSubagent();

  const handleDelete = (subagentId: number) => {
    if (window.confirm('Are you sure you want to remove this subagent?')) {
      removeSubagent.mutate({ agentId, subagentId });
    }
  };

  const handleEdit = (subagent: Subagent) => {
    setEditingSubagent(subagent);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-gray-600">Loading subagents...</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading subagents. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Add Button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Subagents</h3>
        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
          aria-label="Add subagent"
        >
          <PlusIcon className="w-4 h-4" />
          <span>Add Subagent</span>
        </button>
      </div>

      {/* Subagents List */}
      {subagents && subagents.length === 0 ? (
        <div className="bg-gray-50 border-gray-200 rounded-lg p-8 text-center">
          <UserGroupIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-700 font-medium">No subagents configured.</p>
          <p className="text-gray-600 text-sm mt-1">Add a subagent to enable task delegation.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {subagents?.map((subagent) => (
            <article
              key={subagent.id}
              className="bg-white border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="font-semibold text-gray-900">
                      {subagent.subagent.name}
                    </h4>
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                      Priority: {subagent.priority}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 italic">
                    {subagent.delegation_prompt || 'Uses default system prompt'}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => handleEdit(subagent)}
                    className="p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                    aria-label="Edit"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(subagent.subagent_id)}
                    className="p-2 text-red-700 hover:bg-red-50 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
                    aria-label="Delete"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Modals */}
      <SubagentSelectionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        agentId={agentId}
      />

      {editingSubagent && (
        <SubagentEditModal
          isOpen={true}
          onClose={() => setEditingSubagent(null)}
          agentId={agentId}
          subagent={editingSubagent}
        />
      )}
    </div>
  );
};

export default SubagentManager;
