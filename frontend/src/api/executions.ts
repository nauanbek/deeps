/**
 * Execution API Client
 *
 * Provides HTTP methods for managing agent executions including starting,
 * monitoring, and cancelling executions. Also supports fetching execution
 * traces for real-time monitoring and debugging.
 *
 * @module api/executions
 */

import { apiClient } from './client';
import type { Execution, ExecutionCreate, ExecutionTrace } from '../types/execution';

/**
 * Execution API methods for interacting with the backend /executions endpoints.
 * All methods require authentication via JWT token in Authorization header.
 */
export const executionsApi = {
  /**
   * Fetch executions with optional filters.
   *
   * @param {Object} [params] - Query parameters for filtering
   * @param {number} [params.agent_id] - Filter by agent ID
   * @param {string} [params.status] - Filter by status (pending, running, completed, failed, cancelled)
   * @param {number} [params.limit] - Maximum number of results
   * @param {number} [params.offset] - Pagination offset
   * @returns {Promise<Execution[]>} List of executions matching filters
   * @throws {AxiosError} 401 if not authenticated, 422 if invalid params
   *
   * @example
   * // Get all executions
   * const all = await executionsApi.getAll();
   *
   * @example
   * // Get failed executions for specific agent
   * const failures = await executionsApi.getAll({
   *   agent_id: 123,
   *   status: 'failed'
   * });
   */
  getAll: async (params?: {
    agent_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Execution[]> => {
    const response = await apiClient.get<Execution[]>('/executions', { params });
    return response.data;
  },

  /**
   * Fetch a single execution by ID.
   *
   * @param {number} id - Execution ID to retrieve
   * @returns {Promise<Execution>} Execution details including status, output, and metrics
   * @throws {AxiosError} 404 if execution not found, 401 if unauthorized
   *
   * @example
   * const execution = await executionsApi.getById(456);
   * console.log(execution.status, execution.output);
   */
  getById: async (id: number): Promise<Execution> => {
    const response = await apiClient.get<Execution>(`/executions/${id}`);
    return response.data;
  },

  /**
   * Create and start a new execution.
   *
   * Immediately begins executing the agent with the provided prompt.
   * Use getTraces() or WebSocket streaming to monitor progress in real-time.
   *
   * @param {ExecutionCreate} data - Execution configuration
   * @param {number} data.agent_id - Agent ID to execute
   * @param {string} data.prompt - User input prompt
   * @param {Object} [data.execution_params] - Optional parameter overrides
   * @returns {Promise<Execution>} Created execution with status 'pending' or 'running'
   * @throws {AxiosError} 404 if agent not found, 400 if validation fails
   *
   * @example
   * const execution = await executionsApi.create({
   *   agent_id: 123,
   *   prompt: 'Analyze this dataset and provide insights',
   *   execution_params: { max_iterations: 10 }
   * });
   * console.log('Execution started:', execution.id);
   */
  create: async (data: ExecutionCreate): Promise<Execution> => {
    const response = await apiClient.post<Execution>('/executions', data);
    return response.data;
  },

  /**
   * Fetch execution traces (event log).
   *
   * Returns the complete execution event history including tool calls,
   * LLM responses, and state updates. Useful for debugging and monitoring.
   *
   * @param {number} id - Execution ID to get traces for
   * @returns {Promise<ExecutionTrace[]>} List of trace events in chronological order
   * @throws {AxiosError} 404 if execution not found, 401 if unauthorized
   *
   * @example
   * const traces = await executionsApi.getTraces(456);
   * traces.forEach(trace => {
   *   console.log(`[${trace.event_type}]`, trace.content);
   * });
   */
  getTraces: async (id: number): Promise<ExecutionTrace[]> => {
    const response = await apiClient.get<ExecutionTrace[]>(`/executions/${id}/traces`);
    return response.data;
  },

  /**
   * Cancel a running execution.
   *
   * Sends a cancellation request to stop the execution. The execution
   * status will change to 'cancelled' once the agent processes the signal.
   *
   * @param {number} id - Execution ID to cancel
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if not found, 400 if already completed, 401 if unauthorized
   *
   * @example
   * await executionsApi.cancel(456);
   * console.log('Cancellation requested');
   */
  cancel: async (id: number): Promise<void> => {
    await apiClient.post(`/executions/${id}/cancel`);
  },
};
