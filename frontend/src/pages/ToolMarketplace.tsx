/**
 * ToolMarketplace page - Main page for managing tools
 */

import React, { useState, Suspense, lazy } from 'react';
import { PlusIcon, MagnifyingGlassIcon, FunnelIcon } from '@heroicons/react/24/outline';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import { useTools, useDeleteTool } from '../hooks/useTools';
import { useToast } from '../hooks/useToast';
import ToolList from '../components/tools/ToolList';
import { Button } from '../components/common/Button';
import type { Tool } from '../types/tool';

// Lazy load modals (only shown on user interaction)
const ToolFormModal = lazy(() => import('../components/tools/ToolFormModal'));
const DeleteConfirmModal = lazy(() => import('../components/common/DeleteConfirmModal'));

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

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  // Handle type filter change
  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedType(e.target.value);
  };

  // Clear filters
  const clearFilters = () => {
    setSearchQuery('');
    setSelectedType('');
  };

  const hasActiveFilters = searchQuery || selectedType;

  return (
    <PageErrorBoundary>
      <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Tool Marketplace</h1>
              <p className="mt-2 text-sm text-gray-600">
                Create and manage tools for your AI agents
              </p>
            </div>
            <Button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center space-x-2"
            >
              <PlusIcon className="w-5 h-5" />
              <span>Create Tool</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg border-gray-200 p-4 mb-6">
          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="flex-1 relative">
              <label htmlFor="tool-search" className="sr-only">
                Search tools
              </label>
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />
              <input
                id="tool-search"
                type="search"
                placeholder="Search tools by name..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-4 py-2 border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-primary-500"
              />
            </div>

            {/* Type Filter */}
            <div className="relative">
              <FunnelIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                value={selectedType}
                onChange={handleTypeChange}
                className="pl-10 pr-8 py-2 border-gray-300 rounded-lg focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-primary-500 appearance-none cursor-pointer min-w-[160px]"
              >
                <option value="">All Types</option>
                <option value="builtin">Built-in</option>
                <option value="custom">Custom</option>
                <option value="langgraph">LangGraph</option>
              </select>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <Button variant="secondary" onClick={clearFilters} size="sm">
                Clear Filters
              </Button>
            )}
          </div>

          {/* Active Filters Display */}
          {hasActiveFilters && (
            <div className="mt-3 flex items-center space-x-2">
              <span className="text-sm text-gray-500">Active filters:</span>
              {searchQuery && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-primary-100 text-primary-800">
                  Search: {searchQuery}
                </span>
              )}
              {selectedType && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-primary-100 text-primary-800">
                  Type: {selectedType}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Error State */}
        {isError && (
          <div className="bg-red-50 border-red-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-red-800">
              Failed to load tools: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        )}

        {/* Tool List */}
        <ToolList
          tools={tools}
          onEdit={handleEdit}
          onDelete={handleDelete}
          isLoading={isLoading}
        />

        {/* Results Count */}
        {!isLoading && tools.length > 0 && (
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Showing {tools.length} tool{tools.length !== 1 ? 's' : ''}
            </p>
          </div>
        )}
      </div>

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
      </main>
    </PageErrorBoundary>
  );
};

export default ToolMarketplace;
