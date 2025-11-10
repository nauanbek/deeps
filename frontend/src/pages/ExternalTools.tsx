/**
 * External Tools page - Marketplace for LangChain external tools integration
 *
 * This page allows users to:
 * - Browse available external tools (PostgreSQL, GitLab, Elasticsearch, HTTP)
 * - Configure new tool connections
 * - Manage existing tool configurations
 * - Test connections
 * - View usage analytics
 */

import React, { useState, Suspense, lazy } from 'react';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useExternalTools, useToolCatalog, useDeleteExternalTool } from '../hooks/useExternalTools';
import { useToast } from '../hooks/useToast';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import type { ExternalToolConfig, ExternalToolType } from '../types/externalTool';

// Lazy load modals and components
const ExternalToolConfigModal = lazy(
  () => import('../components/externalTools/ExternalToolConfigModal')
);
const ExternalToolCard = lazy(() => import('../components/externalTools/ExternalToolCard'));
const ToolCatalogCard = lazy(() => import('../components/externalTools/ToolCatalogCard'));
const DeleteConfirmModal = lazy(() => import('../components/common/DeleteConfirmModal'));

type ViewMode = 'catalog' | 'configured';

export const ExternalTools: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('configured');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<ExternalToolType | ''>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedCatalogType, setSelectedCatalogType] = useState<ExternalToolType | null>(null);
  const [editingTool, setEditingTool] = useState<ExternalToolConfig | null>(null);
  const [deletingTool, setDeletingTool] = useState<ExternalToolConfig | null>(null);

  const { success: showSuccess, error: showError } = useToast();
  const deleteTool = useDeleteExternalTool();

  // Fetch configured tools
  const {
    data: toolsResponse,
    isLoading: isLoadingTools,
    isError: isToolsError,
    error: toolsError,
  } = useExternalTools({
    tool_type: selectedType || undefined,
    page: 1,
    page_size: 50,
  });

  // Fetch catalog
  const { data: catalogResponse, isLoading: isLoadingCatalog } = useToolCatalog();

  const tools = toolsResponse?.tools || [];
  const catalog = catalogResponse?.tools || [];

  // Filter tools by search query
  const filteredTools = searchQuery
    ? tools.filter((tool) =>
        tool.tool_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : tools;

  // Handle create from catalog
  const handleCreateFromCatalog = (toolType: ExternalToolType) => {
    setSelectedCatalogType(toolType);
    setIsCreateModalOpen(true);
  };

  // Handle edit
  const handleEdit = (tool: ExternalToolConfig) => {
    setEditingTool(tool);
  };

  // Handle delete
  const handleDelete = (tool: ExternalToolConfig) => {
    setDeletingTool(tool);
  };

  const confirmDelete = async () => {
    if (!deletingTool) return;

    try {
      await deleteTool.mutateAsync(deletingTool.id);
      showSuccess(`Tool "${deletingTool.tool_name}" deleted successfully`);
      setDeletingTool(null);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to delete tool';
      showError(errorMessage);
    }
  };

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  // Handle type filter change
  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedType(e.target.value as ExternalToolType | '');
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
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">External Tools</h1>
              <p className="mt-2 text-sm text-gray-600">
                Connect your agents to PostgreSQL, GitLab, Elasticsearch, and HTTP APIs
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                variant="secondary"
                onClick={() => {/* Feature: Link to external tools analytics page */}}
                disabled
                className="flex items-center space-x-2 opacity-50 cursor-not-allowed"
              >
                <ChartBarIcon className="w-5 h-5" />
                <span>Analytics</span>
              </Button>
              <Button
                onClick={() => {
                  setSelectedCatalogType(null);
                  setIsCreateModalOpen(true);
                }}
                className="flex items-center space-x-2"
              >
                <PlusIcon className="w-5 h-5" />
                <span>Configure Tool</span>
              </Button>
            </div>
          </div>

          {/* View Mode Tabs */}
          <div className="mt-6 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setViewMode('configured')}
                className={`${
                  viewMode === 'configured'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors`}
              >
                My Tools ({tools.length})
              </button>
              <button
                onClick={() => setViewMode('catalog')}
                className={`${
                  viewMode === 'catalog'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors`}
              >
                Marketplace ({catalog.length})
              </button>
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters (only for configured tools view) */}
        {viewMode === 'configured' && (
          <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="flex-1 relative">
                <label htmlFor="external-tool-search" className="sr-only">
                  Search external tools
                </label>
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />
                <input
                  id="external-tool-search"
                  type="search"
                  placeholder="Search configured tools..."
                  value={searchQuery}
                  onChange={handleSearchChange}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>

              {/* Type Filter */}
              <div className="relative">
                <FunnelIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                <select
                  value={selectedType}
                  onChange={handleTypeChange}
                  className="pl-10 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 appearance-none cursor-pointer min-w-[180px]"
                >
                  <option value="">All Tool Types</option>
                  <option value="postgresql">PostgreSQL</option>
                  <option value="gitlab">GitLab</option>
                  <option value="elasticsearch">Elasticsearch</option>
                  <option value="http">HTTP Client</option>
                </select>
              </div>

              {/* Clear Filters */}
              {hasActiveFilters && (
                <Button variant="secondary" onClick={clearFilters} size="sm">
                  Clear
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
        )}

        {/* Error State */}
        {isToolsError && viewMode === 'configured' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-red-800">
              Failed to load tools:{' '}
              {toolsError instanceof Error ? toolsError.message : 'Unknown error'}
            </p>
          </div>
        )}

        {/* Loading State */}
        {(isLoadingTools || isLoadingCatalog) && (
          <div className="flex justify-center items-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {/* Configured Tools View */}
        {!isLoadingTools && viewMode === 'configured' && (
          <>
            {filteredTools.length === 0 ? (
              <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                <p className="text-gray-500 mb-4">
                  {hasActiveFilters
                    ? 'No tools match your filters'
                    : 'No tools configured yet'}
                </p>
                <Button
                  onClick={() => {
                    setSelectedCatalogType(null);
                    setIsCreateModalOpen(true);
                  }}
                >
                  Configure Your First Tool
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Suspense fallback={<LoadingSpinner />}>
                  {filteredTools.map((tool) => (
                    <ExternalToolCard
                      key={tool.id}
                      tool={tool}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  ))}
                </Suspense>
              </div>
            )}

            {/* Results Count */}
            {filteredTools.length > 0 && (
              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600">
                  Showing {filteredTools.length} of {tools.length} configured tool
                  {tools.length !== 1 ? 's' : ''}
                </p>
              </div>
            )}
          </>
        )}

        {/* Catalog View */}
        {!isLoadingCatalog && viewMode === 'catalog' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Suspense fallback={<LoadingSpinner />}>
              {catalog.map((item) => (
                <ToolCatalogCard
                  key={item.tool_type}
                  catalogItem={item}
                  onConfigure={handleCreateFromCatalog}
                />
              ))}
            </Suspense>
          </div>
        )}
      </div>

      {/* Create/Edit Tool Modal */}
        {(isCreateModalOpen || editingTool) && (
          <Suspense fallback={null}>
            <ModalErrorBoundary
              onClose={() => {
                setIsCreateModalOpen(false);
                setEditingTool(null);
                setSelectedCatalogType(null);
              }}
            >
              <ExternalToolConfigModal
                isOpen={true}
                tool={editingTool || undefined}
                initialToolType={selectedCatalogType || undefined}
                onClose={() => {
                  setIsCreateModalOpen(false);
                  setEditingTool(null);
                  setSelectedCatalogType(null);
                }}
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
                title="Delete Tool Configuration"
                message={`Are you sure you want to delete "${deletingTool.tool_name}"? This will remove the tool from all agents using it. This action cannot be undone.`}
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

export default ExternalTools;
