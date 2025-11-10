/**
 * Custom Tools API Client
 *
 * Provides HTTP methods for managing custom LangChain-compatible tools.
 * Custom tools extend agent capabilities with user-defined functionality
 * implemented in Python code.
 *
 * Features:
 * - Create custom tools with Python implementation
 * - Attach tools to multiple agents
 * - Share tools across agents
 * - Soft delete for data preservation
 * - Category organization (API, Data Processing, Utility, etc.)
 *
 * All methods require authentication via JWT token.
 *
 * @module api/tools
 */

import { apiClient } from './client';
import type { Tool, ToolCreate, ToolUpdate, ToolFilters, ToolCategoriesResponse } from '../types/tool';

/**
 * Fetch list of custom tools with optional filters.
 *
 * Returns paginated list of tools owned by the current user.
 * Use filters to search by category, active status, or keyword.
 *
 * @param {ToolFilters} [params] - Optional filters
 * @param {string} [params.category] - Filter by category
 * @param {boolean} [params.is_active] - Filter by active status
 * @param {string} [params.search] - Search by name or description
 * @param {number} [params.page] - Page number (1-indexed)
 * @param {number} [params.page_size] - Results per page
 * @returns {Promise<Tool[]>} List of custom tools
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * // Get all active API tools
 * const apiTools = await getTools({
 *   category: 'api',
 *   is_active: true
 * });
 *
 * @example
 * // Search tools by keyword
 * const searchResults = await getTools({ search: 'weather' });
 */
export const getTools = async (params?: ToolFilters): Promise<Tool[]> => {
  const response = await apiClient.get<{
    tools: Tool[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
  }>('/tools', { params });
  return response.data.tools;
};

/**
 * Fetch a single custom tool by ID.
 *
 * Returns complete tool details including Python implementation code,
 * parameter schema, and usage statistics.
 *
 * @param {number} id - Tool ID to retrieve
 * @returns {Promise<Tool>} Tool details with implementation
 * @throws {AxiosError} 404 if tool not found, 403 if not owner, 401 if not authenticated
 *
 * @example
 * const tool = await getTool(123);
 * console.log(tool.name, tool.category);
 * console.log('Implementation:', tool.implementation);
 */
export const getTool = async (id: number): Promise<Tool> => {
  const response = await apiClient.get<Tool>(`/tools/${id}`);
  return response.data;
};

/**
 * Create a new custom tool.
 *
 * Defines a LangChain-compatible tool with Python implementation.
 * The implementation must define a function that accepts tool parameters
 * and returns a result.
 *
 * @param {ToolCreate} data - Tool configuration
 * @param {string} data.name - Tool name (snake_case recommended)
 * @param {string} data.description - Human-readable description for LLM
 * @param {string} data.category - Tool category (api, data, utility, etc.)
 * @param {Record<string, any>} data.parameters_schema - JSON Schema for parameters
 * @param {string} data.implementation - Python code implementing the tool
 * @returns {Promise<Tool>} Created tool with generated ID
 * @throws {AxiosError} 400 if validation fails, 409 if name exists, 401 if not authenticated
 *
 * @example
 * const tool = await createTool({
 *   name: 'weather_api',
 *   description: 'Fetches current weather for a city',
 *   category: 'api',
 *   parameters_schema: {
 *     type: 'object',
 *     properties: {
 *       city: { type: 'string', description: 'City name' }
 *     },
 *     required: ['city']
 *   },
 *   implementation: `
 * import requests
 *
 * def run(city: str) -> str:
 *     response = requests.get(f'https://api.weather.com/{city}')
 *     return response.json()
 *   `
 * });
 */
export const createTool = async (data: ToolCreate): Promise<Tool> => {
  const response = await apiClient.post<Tool>('/tools', data);
  return response.data;
};

/**
 * Update an existing custom tool.
 *
 * Modifies tool configuration or implementation. Partial updates supported.
 * WARNING: Changing implementation may break agents using this tool.
 *
 * @param {number} id - Tool ID to update
 * @param {ToolUpdate} data - Partial tool data to update
 * @returns {Promise<Tool>} Updated tool
 * @throws {AxiosError} 404 if not found, 403 if not owner, 400 if validation fails
 *
 * @example
 * const updated = await updateTool(123, {
 *   description: 'Updated: Now supports metric and imperial units',
 *   implementation: updatedPythonCode
 * });
 */
export const updateTool = async (id: number, data: ToolUpdate): Promise<Tool> => {
  const response = await apiClient.put<Tool>(`/tools/${id}`, data);
  return response.data;
};

/**
 * Delete a custom tool.
 *
 * By default performs soft delete (sets is_active=false) to preserve data.
 * Hard delete permanently removes tool from database.
 *
 * @param {number} id - Tool ID to delete
 * @param {boolean} [hardDelete=false] - If true, permanently delete from database
 * @returns {Promise<void>}
 * @throws {AxiosError} 404 if not found, 403 if not owner, 401 if not authenticated
 *
 * @example
 * // Soft delete (default)
 * await deleteTool(123);
 *
 * @example
 * // Hard delete (permanent)
 * await deleteTool(123, true);
 */
export const deleteTool = async (id: number, hardDelete = false): Promise<void> => {
  await apiClient.delete(`/tools/${id}`, {
    params: { hard_delete: hardDelete }
  });
};

/**
 * Fetch available tool categories.
 *
 * Returns list of predefined tool categories for organization.
 * Categories include: api, data_processing, utility, communication, etc.
 *
 * @returns {Promise<string[]>} Available tool categories
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * const categories = await getToolCategories();
 * console.log('Available categories:', categories);
 * // Output: ['api', 'data_processing', 'utility', ...]
 */
export const getToolCategories = async (): Promise<string[]> => {
  const response = await apiClient.get<ToolCategoriesResponse>('/tools/categories');
  return response.data.categories;
};
