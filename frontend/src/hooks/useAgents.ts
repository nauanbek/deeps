/**
 * React Query hooks for Agent API operations.
 *
 * Provides hooks for managing AI agents including CRUD operations,
 * fetching agent metrics, and automatic cache invalidation.
 * All hooks use TanStack Query for server state management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentsApi } from '../api/agents';
import type { AgentCreate, AgentUpdate } from '../types/agent';

/**
 * Hook to fetch all agents for the current user.
 *
 * @returns {UseQueryResult<Agent[]>} Query result containing list of agents
 *
 * @example
 * const { data: agents, isLoading, error } = useAgents();
 */
export const useAgents = () => {
  return useQuery({
    queryKey: ['agents'],
    queryFn: agentsApi.getAll,
  });
};

/**
 * Hook to fetch a single agent by ID.
 *
 * @param {number} id - Agent ID to fetch
 * @returns {UseQueryResult<Agent>} Query result containing agent details
 *
 * @example
 * const { data: agent, isLoading } = useAgent(123);
 */
export const useAgent = (id: number) => {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: () => agentsApi.getById(id),
    enabled: !!id,
  });
};

/**
 * Hook to create a new agent.
 *
 * Automatically invalidates the agents list cache on success
 * to reflect the newly created agent.
 *
 * @returns {UseMutationResult} Mutation result for creating an agent
 *
 * @example
 * const createAgent = useCreateAgent();
 * createAgent.mutate({
 *   name: 'My Agent',
 *   model_provider: 'anthropic',
 *   model_name: 'claude-3-5-sonnet-20241022',
 *   system_prompt: 'You are a helpful assistant.'
 * });
 */
export const useCreateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentCreate) => agentsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
};

/**
 * Hook to update an existing agent.
 *
 * Invalidates both the agents list and the specific agent cache
 * to ensure UI consistency after update.
 *
 * @returns {UseMutationResult} Mutation result for updating an agent
 *
 * @example
 * const updateAgent = useUpdateAgent();
 * updateAgent.mutate({
 *   id: 123,
 *   data: { name: 'Updated Agent Name', temperature: 0.8 }
 * });
 */
export const useUpdateAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AgentUpdate }) =>
      agentsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['agents', variables.id] });
    },
  });
};

/**
 * Hook to delete an agent (soft delete).
 *
 * Sets the agent's is_active flag to false rather than permanently deleting.
 * Invalidates the agents list cache to remove the deleted agent from UI.
 *
 * @returns {UseMutationResult} Mutation result for deleting an agent
 *
 * @example
 * const deleteAgent = useDeleteAgent();
 * deleteAgent.mutate(123);
 */
export const useDeleteAgent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => agentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
};

/**
 * Hook to fetch agent performance metrics.
 *
 * Retrieves execution statistics, success rate, token usage,
 * and other performance indicators for a specific agent.
 *
 * @param {number} id - Agent ID to fetch metrics for
 * @returns {UseQueryResult<AgentMetrics>} Query result containing agent metrics
 *
 * @example
 * const { data: metrics } = useAgentMetrics(123);
 * console.log(`Success rate: ${metrics.success_rate}%`);
 */
export const useAgentMetrics = (id: number) => {
  return useQuery({
    queryKey: ['agents', id, 'metrics'],
    queryFn: () => agentsApi.getMetrics(id),
    enabled: !!id,
  });
};
