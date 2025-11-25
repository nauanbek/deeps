import React, { useState, useMemo, Suspense, lazy } from 'react';
import { PlusIcon, CpuChipIcon } from '@heroicons/react/24/outline';
import { Button } from '../components/common/Button';
import { ToastContainer } from '../components/common/Toast';
import { AgentList } from '../components/agents/AgentList';
import { PageLayout, PageHeader } from '../components/common/PageLayout';
import { SearchInput } from '../components/common/SearchInput';
import { EmptyState } from '../components/common/EmptyState';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import ModalErrorBoundary from '../components/common/ModalErrorBoundary';
import { useAgents, useCreateAgent, useUpdateAgent, useDeleteAgent } from '../hooks/useAgents';
import { useToast } from '../hooks/useToast';
import type { Agent, AgentCreate, AgentUpdate } from '../types/agent';

// Lazy load modals (only shown on user interaction)
const AgentFormModal = lazy(() => import('../components/agents/AgentFormModal').then(m => ({ default: m.AgentFormModal })));
const DeleteConfirmModal = lazy(() => import('../components/agents/DeleteConfirmModal').then(m => ({ default: m.DeleteConfirmModal })));
const ExecuteAgentModal = lazy(() => import('../components/agents/ExecuteAgentModal').then(m => ({ default: m.ExecuteAgentModal })));
const AgentAdvancedConfigModal = lazy(() => import('../components/agents/AgentAdvancedConfigModal').then(m => ({ default: m.AgentAdvancedConfigModal })));
const AgentToolsModal = lazy(() => import('../components/agents/AgentToolsModal').then(m => ({ default: m.AgentToolsModal })));

export const AgentStudio: React.FC = () => {
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [deletingAgent, setDeletingAgent] = useState<Agent | null>(null);
  const [executingAgent, setExecutingAgent] = useState<Agent | null>(null);
  const [advancedConfigAgent, setAdvancedConfigAgent] = useState<Agent | null>(null);
  const [managingToolsAgent, setManagingToolsAgent] = useState<Agent | null>(null);

  // Queries and mutations
  const { data: agents, isLoading, isError, refetch } = useAgents();
  const createMutation = useCreateAgent();
  const updateMutation = useUpdateAgent();
  const deleteMutation = useDeleteAgent();

  // Toast notifications
  const { toasts, removeToast, success, error } = useToast();

  // Filter agents based on search query
  const filteredAgents = useMemo(() => {
    if (!agents) return [];
    if (!searchQuery.trim()) return agents;

    const query = searchQuery.toLowerCase();
    return agents.filter(
      (agent) =>
        agent.name.toLowerCase().includes(query) ||
        agent.description?.toLowerCase().includes(query) ||
        agent.model_provider.toLowerCase().includes(query) ||
        agent.model_name.toLowerCase().includes(query)
    );
  }, [agents, searchQuery]);

  // Handlers
  const handleCreateAgent = async (data: AgentCreate) => {
    try {
      await createMutation.mutateAsync(data);
      success('Agent created successfully');
      setIsCreateModalOpen(false);
    } catch (err: unknown) {
      let errorMessage = 'Failed to create agent';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      error(errorMessage);
      throw err; // Re-throw to prevent modal from closing
    }
  };

  const handleUpdateAgent = async (data: AgentUpdate) => {
    if (!editingAgent) return;

    try {
      await updateMutation.mutateAsync({ id: editingAgent.id, data });
      success('Agent updated successfully');
      setEditingAgent(null);
    } catch (err: unknown) {
      let errorMessage = 'Failed to update agent';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      error(errorMessage);
      throw err; // Re-throw to prevent modal from closing
    }
  };

  const handleDeleteAgent = async () => {
    if (!deletingAgent) return;

    try {
      await deleteMutation.mutateAsync(deletingAgent.id);
      success('Agent deleted successfully');
      setDeletingAgent(null);
    } catch (err: unknown) {
      let errorMessage = 'Failed to delete agent';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      }
      error(errorMessage);
    }
  };

  const handleEdit = (agent: Agent) => {
    setEditingAgent(agent);
  };

  const handleDelete = (agentId: number) => {
    const agent = agents?.find((a) => a.id === agentId);
    if (agent) {
      setDeletingAgent(agent);
    }
  };

  const handleExecute = (agentId: number) => {
    const agent = agents?.find((a) => a.id === agentId);
    if (agent) {
      setExecutingAgent(agent);
    }
  };

  const handleAdvancedConfig = (agent: Agent) => {
    setAdvancedConfigAgent(agent);
  };

  const handleManageTools = (agent: Agent) => {
    setManagingToolsAgent(agent);
  };

  return (
    <PageErrorBoundary>
      <PageLayout>
        {/* Header */}
        <PageHeader
          title="Agent Studio"
          subtitle="Create, configure, and manage your AI agents"
          action={
            <Button
              variant="primary"
              size="md"
              onClick={() => setIsCreateModalOpen(true)}
              leftIcon={<PlusIcon className="w-4 h-4" />}
            >
              Create Agent
            </Button>
          }
        />

        {/* Search Bar */}
        {agents && agents.length > 0 && (
          <div className="mb-6">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search agents by name, description, or model..."
              showShortcut={true}
            />
          </div>
        )}

        {/* Agent List */}
        <AgentList
          agents={filteredAgents}
          isLoading={isLoading}
          isError={isError}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onExecute={handleExecute}
          onAdvancedConfig={handleAdvancedConfig}
          onManageTools={handleManageTools}
          onRetry={refetch}
        />

        {/* Search results message */}
        {searchQuery && filteredAgents.length === 0 && !isLoading && (
          <EmptyState
            variant="search"
            title="No agents found"
            description={`No agents matching "${searchQuery}"`}
            action={{
              label: 'Clear search',
              onClick: () => setSearchQuery(''),
            }}
          />
        )}

        {/* Empty state when no agents exist */}
        {!isLoading && !isError && agents && agents.length === 0 && (
          <EmptyState
            variant="default"
            icon={<CpuChipIcon className="w-12 h-12" />}
            title="No agents yet"
            description="Get started by creating your first AI agent"
            action={{
              label: 'Create Agent',
              onClick: () => setIsCreateModalOpen(true),
            }}
          />
        )}

        {/* Create Modal */}
        {isCreateModalOpen && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setIsCreateModalOpen(false)}>
              <AgentFormModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onSubmit={handleCreateAgent}
                isSubmitting={createMutation.isPending}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Edit Modal */}
        {editingAgent && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setEditingAgent(null)}>
              <AgentFormModal
                isOpen={!!editingAgent}
                onClose={() => setEditingAgent(null)}
                onSubmit={handleUpdateAgent}
                agent={editingAgent}
                isSubmitting={updateMutation.isPending}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Delete Confirmation Modal */}
        {deletingAgent && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setDeletingAgent(null)}>
              <DeleteConfirmModal
                isOpen={!!deletingAgent}
                onClose={() => setDeletingAgent(null)}
                onConfirm={handleDeleteAgent}
                agent={deletingAgent}
                isDeleting={deleteMutation.isPending}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Execute Agent Modal */}
        {executingAgent && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setExecutingAgent(null)}>
              <ExecuteAgentModal
                agent={executingAgent}
                onClose={() => setExecutingAgent(null)}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Advanced Configuration Modal */}
        {advancedConfigAgent && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setAdvancedConfigAgent(null)}>
              <AgentAdvancedConfigModal
                agent={advancedConfigAgent}
                isOpen={!!advancedConfigAgent}
                onClose={() => setAdvancedConfigAgent(null)}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Manage Tools Modal */}
        {managingToolsAgent && (
          <Suspense fallback={null}>
            <ModalErrorBoundary onClose={() => setManagingToolsAgent(null)}>
              <AgentToolsModal
                isOpen={!!managingToolsAgent}
                agent={managingToolsAgent}
                onClose={() => setManagingToolsAgent(null)}
              />
            </ModalErrorBoundary>
          </Suspense>
        )}

        {/* Toast Notifications */}
        <ToastContainer toasts={toasts} onDismiss={removeToast} />
      </PageLayout>
    </PageErrorBoundary>
  );
};

export default AgentStudio;
