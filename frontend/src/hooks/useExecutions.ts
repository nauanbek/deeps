/**
 * React Query hooks for Execution API operations.
 *
 * Provides hooks for managing agent executions including:
 * - Fetching execution history with filters
 * - Creating new executions
 * - Retrieving execution traces
 * - Cancelling running executions
 *
 * All hooks use TanStack Query for server state management
 * with automatic caching and invalidation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { executionsApi } from '../api/executions';
import type { ExecutionCreate } from '../types/execution';

/**
 * Hook to fetch executions with optional filters.
 *
 * @param {Object} params - Optional query parameters
 * @param {number} params.agent_id - Filter by agent ID
 * @param {string} params.status - Filter by status (pending, running, completed, failed, cancelled)
 * @param {number} params.limit - Maximum number of results
 * @param {number} params.offset - Pagination offset
 * @returns {UseQueryResult<Execution[]>} Query result containing list of executions
 *
 * @example
 * // Get all executions for specific agent
 * const { data: executions } = useExecutions({ agent_id: 123 });
 *
 * @example
 * // Get only failed executions
 * const { data: failures } = useExecutions({ status: 'failed' });
 */
export const useExecutions = (params?: {
  agent_id?: number;
  status?: string;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: ['executions', params],
    queryFn: () => executionsApi.getAll(params),
  });
};

/**
 * Hook to fetch a single execution by ID.
 *
 * @param {number} id - Execution ID to fetch
 * @returns {UseQueryResult<Execution>} Query result containing execution details
 *
 * @example
 * const { data: execution } = useExecution(456);
 * console.log(execution.status, execution.output);
 */
export const useExecution = (id: number) => {
  return useQuery({
    queryKey: ['executions', id],
    queryFn: () => executionsApi.getById(id),
    enabled: !!id,
  });
};

/**
 * Hook to create and start a new agent execution.
 *
 * Creates an execution record and immediately starts running
 * the agent with the provided prompt. Invalidates executions
 * cache on success.
 *
 * @returns {UseMutationResult} Mutation result for creating an execution
 *
 * @example
 * const createExecution = useCreateExecution();
 * createExecution.mutate({
 *   agent_id: 123,
 *   prompt: 'Analyze this dataset',
 *   execution_params: { max_iterations: 10 }
 * });
 */
export const useCreateExecution = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExecutionCreate) => executionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
    },
  });
};

/**
 * Hook to fetch execution traces (event log).
 *
 * Retrieves the complete trace history for an execution including
 * tool calls, LLM responses, and state updates. Automatically polls
 * every 2 seconds to show real-time progress for active executions.
 *
 * @param {number} id - Execution ID to fetch traces for
 * @returns {UseQueryResult<ExecutionTrace[]>} Query result containing execution traces
 *
 * @example
 * const { data: traces } = useExecutionTraces(456);
 * traces?.forEach(trace => console.log(trace.event_type, trace.content));
 */
export const useExecutionTraces = (id: number) => {
  return useQuery({
    queryKey: ['executions', id, 'traces'],
    queryFn: () => executionsApi.getTraces(id),
    enabled: !!id,
    refetchInterval: 2000, // Poll every 2 seconds for active executions
  });
};

/**
 * Hook to cancel a running execution.
 *
 * Sends a cancellation request to the backend to stop
 * a currently running execution. Invalidates both the
 * execution list and specific execution cache.
 *
 * @returns {UseMutationResult} Mutation result for cancelling an execution
 *
 * @example
 * const cancelExecution = useCancelExecution();
 * cancelExecution.mutate(456);
 */
export const useCancelExecution = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => executionsApi.cancel(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      queryClient.invalidateQueries({ queryKey: ['executions', id] });
    },
  });
};
