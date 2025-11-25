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
import {
  PlusIcon,
  ChartBarIcon,
  ServerStackIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import { PageLayout, PageHeader } from '../components/common/PageLayout';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Tabs } from '../components/common/Tabs';
import { SearchInput } from '../components/common/SearchInput';
import { Select } from '../components/common/Select';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { useExternalTools, useToolCatalog, useDeleteExternalTool } from '../hooks/useExternalTools';
import { useToast } from '../hooks/useToast';
import type { ExternalToolConfig, ExternalToolType } from '../types/externalTool';

// Lazy load modals and components
const ExternalToolConfigModal = lazy(
  () => import('../components/externalTools/ExternalToolConfigModal')
);
const ExternalToolCard = lazy(() => import('../components/externalTools/ExternalToolCard'));
const ToolCatalogCard = lazy(() => import('../components/externalTools/ToolCatalogCard'));
const DeleteConfirmModal = lazy(() => import('../components/common/DeleteConfirmModal'));

type ViewMode = 'catalog' | 'configured';

const toolTypeOptions = [
  { value: '', label: 'All Tool Types' },
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'gitlab', label: 'GitLab' },
  { value: 'elasticsearch', label: 'Elasticsearch' },
  { value: 'http', label: 'HTTP Client' },
];

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

  const tabs = [
    {
      id: 'configured',
      label: (
        <span className="flex items-center gap-2">
          My Tools
          <Badge variant="neutral" size="sm">{tools.length}</Badge>
        </span>
      ),
    },
    {
      id: 'catalog',
      label: (
        <span className="flex items-center gap-2">
          Marketplace
          <Badge variant="primary" size="sm">{catalog.length}</Badge>
        </span>
      ),
    },
  ];

  return (
    <PageErrorBoundary>
      <PageLayout>
        {/* Header */}
        <PageHeader
          title="External Tools"
          subtitle="Connect your agents to PostgreSQL, GitLab, Elasticsearch, and HTTP APIs"
          action={
            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="md"
                onClick={() => {/* Feature: Link to external tools analytics page */}}
                disabled
                leftIcon={<ChartBarIcon className="w-4 h-4" />}
              >
                Analytics
              </Button>
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  setSelectedCatalogType(null);
                  setIsCreateModalOpen(true);
                }}
                leftIcon={<PlusIcon className="w-4 h-4" />}
              >
                Configure Tool
              </Button>
            </div>
          }
        />

        {/* View Mode Tabs */}
        <div className="mb-6">
          <Tabs
            tabs={tabs}
            activeTab={viewMode}
            onChange={(id) => setViewMode(id as ViewMode)}
            variant="underline"
          />
        </div>

        {/* Filters (only for configured tools view) */}
        {viewMode === 'configured' && (
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
                  placeholder="Search configured tools..."
                />
              </div>

              <Select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value as ExternalToolType | '')}
                options={toolTypeOptions}
                className="w-44"
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
        )}

        {/* Error State */}
        {isToolsError && viewMode === 'configured' && (
          <div className="bg-error-50 border border-error-200 rounded-xl p-4 mb-6">
            <p className="text-sm text-error-700">
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
              <EmptyState
                variant="default"
                icon={<ServerStackIcon className="w-12 h-12" />}
                title={hasActiveFilters ? 'No tools match your filters' : 'No tools configured yet'}
                description={hasActiveFilters
                  ? 'Try adjusting your search or filter criteria'
                  : 'Connect your first external tool to get started'}
                action={{
                  label: 'Configure Your First Tool',
                  onClick: () => {
                    setSelectedCatalogType(null);
                    setIsCreateModalOpen(true);
                  },
                }}
              />
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
                <p className="text-sm text-surface-500">
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
      </PageLayout>
    </PageErrorBoundary>
  );
};

export default ExternalTools;
