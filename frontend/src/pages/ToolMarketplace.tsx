/**
 * ToolMarketplace page - Main page for managing custom tools
 */

import React, { useState, Suspense, lazy } from 'react';
import {
  PlusIcon,
  WrenchScrewdriverIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import { PageLayout, PageHeader } from '../components/common/PageLayout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { SearchInput } from '../components/common/SearchInput';
import { Select } from '../components/common/Select';
import { EmptyState } from '../components/common/EmptyState';
import { useTools, useDeleteTool } from '../hooks/useTools';
import { useToast } from '../hooks/useToast';
import ToolList from '../components/tools/ToolList';
import type { Tool } from '../types/tool';

// Lazy load modals (only shown on user interaction)
const ToolFormModal = lazy(() => import('../components/tools/ToolFormModal'));
const DeleteConfirmModal = lazy(() => import('../components/common/DeleteConfirmModal'));

const toolTypeOptions = [
  { value: '', label: 'All Types' },
  { value: 'builtin', label: 'Built-in' },
  { value: 'custom', label: 'Custom' },
  { value: 'langgraph', label: 'LangGraph' },
];

export const ToolMarketplace: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTool, setEditingTool] = useState<Tool | null>(null);
  const [deletingTool, setDeletingTool] = useState<Tool | null>(null);

  const { success: showSuccess, error: showError } = useToast();
  const deleteTool = useDeleteTool();

  // Fetch tools with filters
  const { data: tools = [], isLoading, isError, error } = useTools({
    search: searchQuery || undefined,
    tool_type: selectedType || undefined,
    is_active: true,
  });

  // Handle edit
  const handleEdit = (tool: Tool) => {
    setEditingTool(tool);
  };

  // Handle delete
  const handleDelete = (tool: Tool) => {
    setDeletingTool(tool);
  };

  const confirmDelete = async () => {
    if (!deletingTool) return;

    try {
      await deleteTool.mutateAsync({ id: deletingTool.id, hardDelete: false });
      showSuccess(`Tool "${deletingTool.name}" deleted successfully`);
      setDeletingTool(null);
    } catch (error: unknown) {
      let errorMessage = 'Failed to delete tool';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      showError(errorMessage);
    }
  };

  // Clear filters
  const clearFilters = () => {
    setSearchQuery('');
    setSelectedType('');
  };

  const hasActiveFilters = searchQuery || selectedType;

  return (
    <PageErrorBoundary>
      <PageLayout>
        {/* Header */}
        <PageHeader
          title="Custom Tools"
          subtitle="Create and manage tools for your AI agents"
          action={
            <Button
              variant="primary"
              size="md"
              onClick={() => setIsCreateModalOpen(true)}
              leftIcon={<PlusIcon className="w-4 h-4" />}
            >
              Create Tool
            </Button>
          }
        />

        {/* Filters */}
        <Card className="p-4 mb-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-2 text-surface-600">
              <FunnelIcon className="w-5 h-5" />
              <span className="text-sm font-medium">Filters</span>
            </div>

            <div className="flex-1 max-w-md">
              <SearchInput
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search tools by name..."
              />
            </div>

            <Select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              options={toolTypeOptions}
              className="w-36"
            />

            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </div>

          {/* Active Filters Display */}
          {hasActiveFilters && (
            <div className="mt-3 flex items-center gap-2">
              <span className="text-sm text-surface-500">Active:</span>
              {searchQuery && (
                <Badge variant="primary" size="sm">
                  Search: {searchQuery}
                </Badge>
              )}
              {selectedType && (
                <Badge variant="primary" size="sm">
                  Type: {selectedType}
                </Badge>
              )}
            </div>
          )}
        </Card>

        {/* Error State */}
        {isError && (
          <div className="bg-error-50 border border-error-200 rounded-xl p-4 mb-6">
            <p className="text-sm text-error-700">
              Failed to load tools: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        )}

        {/* Tool List or Empty State */}
        {!isLoading && tools.length === 0 ? (
          <EmptyState
            variant="default"
            icon={<WrenchScrewdriverIcon className="w-12 h-12" />}
            title={hasActiveFilters ? 'No tools match your filters' : 'No tools created yet'}
            description={hasActiveFilters
              ? 'Try adjusting your search or filter criteria'
              : 'Create your first custom tool to extend your agents capabilities'}
            action={{
              label: 'Create Your First Tool',
              onClick: () => setIsCreateModalOpen(true),
            }}
          />
        ) : (
          <ToolList
            tools={tools}
            onEdit={handleEdit}
            onDelete={handleDelete}
            isLoading={isLoading}
          />
        )}

        {/* Results Count */}
        {!isLoading && tools.length > 0 && (
          <div className="mt-6 text-center">
            <p className="text-sm text-surface-500">
              Showing {tools.length} tool{tools.length !== 1 ? 's' : ''}
            </p>
          </div>
        )}

        {/* Create Tool Modal */}
        {isCreateModalOpen && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setIsCreateModalOpen(false)}>
              <ToolFormModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Edit Tool Modal */}
        {editingTool && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setEditingTool(null)}>
              <ToolFormModal
                isOpen={true}
                tool={editingTool}
                onClose={() => setEditingTool(null)}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Delete Confirmation Modal */}
        {deletingTool && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setDeletingTool(null)}>
              <DeleteConfirmModal
                isOpen={true}
                title="Delete Tool"
                message={`Are you sure you want to delete "${deletingTool.name}"? This action cannot be undone.`}
                onConfirm={confirmDelete}
                onCancel={() => setDeletingTool(null)}
                confirmText="Delete"
                cancelText="Cancel"
                isLoading={deleteTool.isPending}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}
      </PageLayout>
    </PageErrorBoundary>
  );
};

export default ToolMarketplace;
