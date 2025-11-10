/**
 * React Query hooks for Subagent API operations.
 *
 * Provides hooks for managing subagent hierarchies including
 * fetching, adding, updating, and removing subagent relationships.
 * Enables delegation patterns where agents can invoke specialized
 * subagents for specific tasks.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAgentSubagents,
  addSubagent,
  updateSubagent,
  removeSubagent,
} from '../api/subagents';
import type { SubagentCreate, SubagentUpdate } from '../types/subagent';

/**
 * Hook to fetch all subagents for a parent agent.
 *
 * Retrieves the list of configured subagents that can be delegated to
 * by the specified parent agent. Cached for 1 minute.
 *
 * @param {number | undefined} agentId - Parent agent ID to fetch subagents for
 * @returns {UseQueryResult<Subagent[]>} Query result containing subagent list
 *
 * @example
 * const { data: subagents } = useAgentSubagents(123);
 * console.log(`Agent has ${subagents?.length} subagents`);
 */
export const useAgentSubagents = (agentId: number | undefined) => {
  return useQuery({
    queryKey: ['agents', agentId, 'subagents'],
    queryFn: () => getAgentSubagents(agentId!),
    enabled: !!agentId,
    staleTime: 60000, // 1 minute
  });
};

/**
 * Hook to add a new subagent to a parent agent.
 *
 * Creates a delegation relationship allowing the parent agent
 * to invoke the subagent with optional delegation prompt override.
 * Automatically invalidates the subagent list cache.
 *
 * @returns {UseMutationResult} Mutation result for adding a subagent
 *
 * @example
 * const addSubagent = useAddSubagent();
 * addSubagent.mutate({
 *   agentId: 123,
 *   data: {
 *     subagent_id: 456,
 *     delegation_prompt: 'You are a specialized code reviewer',
 *     priority: 10
 *   }
 * });
 */
export const useAddSubagent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, data }: { agentId: number; data: SubagentCreate }) =>
      addSubagent(agentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['agents', variables.agentId, 'subagents'],
      });
    },
  });
};

/**
 * Hook to update an existing subagent relationship.
 *
 * Allows updating the delegation prompt or priority for an existing
 * subagent relationship. Invalidates the subagent list cache.
 *
 * @returns {UseMutationResult} Mutation result for updating a subagent
 *
 * @example
 * const updateSubagent = useUpdateSubagent();
 * updateSubagent.mutate({
 *   agentId: 123,
 *   subagentId: 456,
 *   data: { priority: 20 }
 * });
 */
export const useUpdateSubagent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      agentId,
      subagentId,
      data,
    }: {
      agentId: number;
      subagentId: number;
      data: SubagentUpdate;
    }) => updateSubagent(agentId, subagentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['agents', variables.agentId, 'subagents'],
      });
    },
  });
};

/**
 * Hook to remove a subagent from a parent agent.
 *
 * Deletes the delegation relationship between parent and subagent.
 * The subagent itself is not deleted, only the relationship.
 * Automatically invalidates the subagent list cache.
 *
 * @returns {UseMutationResult} Mutation result for removing a subagent
 *
 * @example
 * const removeSubagent = useRemoveSubagent();
 * removeSubagent.mutate({ agentId: 123, subagentId: 456 });
 */
export const useRemoveSubagent = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, subagentId }: { agentId: number; subagentId: number }) =>
      removeSubagent(agentId, subagentId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['agents', variables.agentId, 'subagents'],
      });
    },
  });
};
