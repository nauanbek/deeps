/**
 * Subagent API Client
 *
 * Provides HTTP methods for managing subagent hierarchies and delegation.
 * Subagents enable parent agents to delegate specialized tasks to child agents,
 * creating powerful multi-agent workflows with division of labor.
 *
 * Features:
 * - Hierarchical agent delegation
 * - Task-specific specialization
 * - Cycle detection (prevents infinite delegation loops)
 * - Automatic `task` tool injection for delegation
 *
 * All methods require authentication via JWT token.
 *
 * @module api/subagents
 */

import { apiClient } from './client';
import type { Subagent, SubagentCreate, SubagentUpdate } from '../types/subagent';

/**
 * Fetch all subagents for a parent agent.
 *
 * Returns list of child agents that can be delegated to by the parent.
 * The parent agent automatically receives a `task` tool to delegate
 * work to these subagents.
 *
 * @param {number} agentId - Parent agent ID to query
 * @returns {Promise<Subagent[]>} List of subagent configurations
 * @throws {AxiosError} 404 if agent not found, 401 if not authenticated
 *
 * @example
 * const subagents = await getAgentSubagents(123);
 * subagents.forEach(s => console.log(`${s.name}: ${s.description}`));
 */
export const getAgentSubagents = async (agentId: number): Promise<Subagent[]> => {
  const response = await apiClient.get<Subagent[]>(`/agents/${agentId}/subagents`);
  return response.data;
};

/**
 * Add a subagent to a parent agent.
 *
 * Enables the parent agent to delegate tasks to the child agent.
 * Includes cycle detection to prevent circular delegation (A→B→A).
 *
 * @param {number} agentId - Parent agent ID
 * @param {SubagentCreate} data - Subagent configuration
 * @param {number} data.child_agent_id - ID of agent to add as subagent
 * @param {string} [data.name] - Optional display name for delegation
 * @param {string} [data.description] - Optional description of subagent's role
 * @returns {Promise<Subagent>} Created subagent configuration
 * @throws {AxiosError} 404 if agent not found, 400 if cycle detected, 409 if already exists
 *
 * @example
 * // Add research agent as subagent to coordinator
 * const subagent = await addSubagent(123, {
 *   child_agent_id: 456,
 *   name: 'Research Specialist',
 *   description: 'Handles deep research tasks'
 * });
 */
export const addSubagent = async (
  agentId: number,
  data: SubagentCreate
): Promise<Subagent> => {
  const response = await apiClient.post<Subagent>(`/agents/${agentId}/subagents`, data);
  return response.data;
};

/**
 * Update subagent configuration.
 *
 * Modifies name or description for the delegation relationship.
 * Cannot change child_agent_id - delete and re-add instead.
 *
 * @param {number} agentId - Parent agent ID
 * @param {number} subagentId - Subagent configuration ID to update
 * @param {SubagentUpdate} data - Partial subagent data to update
 * @param {string} [data.name] - Updated display name
 * @param {string} [data.description] - Updated description
 * @returns {Promise<Subagent>} Updated subagent configuration
 * @throws {AxiosError} 404 if not found, 403 if not owner
 *
 * @example
 * const updated = await updateSubagent(123, 789, {
 *   description: 'Updated role: Handles research and fact-checking'
 * });
 */
export const updateSubagent = async (
  agentId: number,
  subagentId: number,
  data: SubagentUpdate
): Promise<Subagent> => {
  const response = await apiClient.put<Subagent>(
    `/agents/${agentId}/subagents/${subagentId}`,
    data
  );
  return response.data;
};

/**
 * Remove a subagent from a parent agent.
 *
 * Removes delegation capability - parent agent can no longer delegate
 * to this child agent. Does not delete the child agent itself.
 *
 * @param {number} agentId - Parent agent ID
 * @param {number} subagentId - Subagent configuration ID to remove
 * @returns {Promise<void>}
 * @throws {AxiosError} 404 if not found, 403 if not owner
 *
 * @example
 * await removeSubagent(123, 789);
 * console.log('Subagent removed from delegation hierarchy');
 */
export const removeSubagent = async (
  agentId: number,
  subagentId: number
): Promise<void> => {
  await apiClient.delete(`/agents/${agentId}/subagents/${subagentId}`);
};
