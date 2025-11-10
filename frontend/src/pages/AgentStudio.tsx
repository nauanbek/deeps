import React, { useState, useMemo, Suspense, lazy } from 'react';
import { PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { Button } from '../components/common/Button';
import { ToastContainer } from '../components/common/Toast';
import { AgentList } from '../components/agents/AgentList';
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
  const handleCreateAgent = async (data: any) => {
    try {
      await createMutation.mutateAsync(data as AgentCreate);
      success('Agent created successfully');
      setIsCreateModalOpen(false);
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to create agent');
      throw err; // Re-throw to prevent modal from closing
    }
  };

  const handleUpdateAgent = async (data: any) => {
    if (!editingAgent) return;

    try {
      await updateMutation.mutateAsync({ id: editingAgent.id, data: data as AgentUpdate });
      success('Agent updated successfully');
      setEditingAgent(null);
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to update agent');
      throw err; // Re-throw to prevent modal from closing
    }
  };

  const handleDeleteAgent = async () => {
    if (!deletingAgent) return;

    try {
      await deleteMutation.mutateAsync(deletingAgent.id);
      success('Agent deleted successfully');
      setDeletingAgent(null);
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to delete agent');
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
      <main className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agent Studio</h1>
          <p className="text-gray-600 mt-2">
            Create, configure, and manage your AI agents
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => setIsCreateModalOpen(true)}
          className="self-start sm:self-auto"
        >
          <PlusIcon className="w-5 h-5 mr-2" />
          Create Agent
        </Button>
      </div>

      {/* Search Bar */}
      {agents && agents.length > 0 && (
        <div className="relative">
          <label htmlFor="agent-search" className="sr-only">
            Search agents
          </label>
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input
            id="agent-search"
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus-visible:outline-none focus-visible:placeholder-gray-400 focus-visible:ring-1 focus-visible:ring-primary-500 focus-visible:border-primary-500 sm:text-sm"
            placeholder="Search agents by name, description, or model..."
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
        <div className="text-center py-12">
          <p className="text-gray-600">
            No agents found matching "{searchQuery}"
          </p>
          <Button
            variant="ghost"
            onClick={() => setSearchQuery('')}
            className="mt-2"
          >
            Clear search
          </Button>
        </div>
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
      </main>
    </PageErrorBoundary>
  );
};

export default AgentStudio;
