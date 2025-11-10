/**
 * Agent API Client
 *
 * Provides HTTP methods for managing AI agents including CRUD operations,
 * metrics retrieval, and configuration management. All methods return promises
 * and throw AxiosError on HTTP failures.
 *
 * @module api/agents
 */

import { apiClient } from './client';
import type { Agent, AgentCreate, AgentUpdate, AgentMetrics } from '../types/agent';

/**
 * Agent API methods for interacting with the backend /agents endpoints.
 * All methods require authentication via JWT token in Authorization header.
 */
export const agentsApi = {
  /**
   * Fetch all agents for the current user.
   *
   * @returns {Promise<Agent[]>} List of all agents
   * @throws {AxiosError} 401 if not authenticated, 500 on server error
   *
   * @example
   * const agents = await agentsApi.getAll();
   * console.log(`Found ${agents.length} agents`);
   */
  getAll: async (): Promise<Agent[]> => {
    const response = await apiClient.get<Agent[]>('/agents');
    return response.data;
  },

  /**
   * Fetch a single agent by ID.
   *
   * @param {number} id - Agent ID to retrieve
   * @returns {Promise<Agent>} Agent details
   * @throws {AxiosError} 404 if agent not found, 401 if unauthorized, 403 if not owner
   *
   * @example
   * const agent = await agentsApi.getById(123);
   * console.log(agent.name, agent.model_name);
   */
  getById: async (id: number): Promise<Agent> => {
    const response = await apiClient.get<Agent>(`/agents/${id}`);
    return response.data;
  },

  /**
   * Create a new agent.
   *
   * @param {AgentCreate} data - Agent configuration data
   * @returns {Promise<Agent>} Created agent with generated ID
   * @throws {AxiosError} 400 if validation fails, 401 if not authenticated, 409 if name exists
   *
   * @example
   * const newAgent = await agentsApi.create({
   *   name: 'Research Agent',
   *   model_provider: 'anthropic',
   *   model_name: 'claude-3-5-sonnet-20241022',
   *   system_prompt: 'You are a research assistant',
   *   temperature: 0.7
   * });
   */
  create: async (data: AgentCreate): Promise<Agent> => {
    const response = await apiClient.post<Agent>('/agents', data);
    return response.data;
  },

  /**
   * Update an existing agent.
   *
   * @param {number} id - Agent ID to update
   * @param {AgentUpdate} data - Partial agent data to update
   * @returns {Promise<Agent>} Updated agent
   * @throws {AxiosError} 404 if not found, 401 if unauthorized, 403 if not owner
   *
   * @example
   * const updated = await agentsApi.update(123, {
   *   name: 'Updated Agent Name',
   *   temperature: 0.8
   * });
   */
  update: async (id: number, data: AgentUpdate): Promise<Agent> => {
    const response = await apiClient.put<Agent>(`/agents/${id}`, data);
    return response.data;
  },

  /**
   * Delete an agent (soft delete - sets is_active to false).
   *
   * @param {number} id - Agent ID to delete
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if not found, 401 if unauthorized, 403 if not owner
   *
   * @example
   * await agentsApi.delete(123);
   * console.log('Agent deleted');
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/agents/${id}`);
  },

  /**
   * Fetch performance metrics for an agent.
   *
   * Includes execution counts, success rate, token usage, and cost estimates.
   *
   * @param {number} id - Agent ID to get metrics for
   * @returns {Promise<AgentMetrics>} Agent performance metrics
   * @throws {AxiosError} 404 if not found, 401 if unauthorized
   *
   * @example
   * const metrics = await agentsApi.getMetrics(123);
   * console.log(`Success rate: ${metrics.success_rate}%`);
   * console.log(`Total cost: $${metrics.total_cost}`);
   */
  getMetrics: async (id: number): Promise<AgentMetrics> => {
    const response = await apiClient.get<AgentMetrics>(`/agents/${id}/metrics`);
    return response.data;
  },
};
