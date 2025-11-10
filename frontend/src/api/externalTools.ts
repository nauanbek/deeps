/**
 * External Tools API Client
 *
 * Provides HTTP methods for managing external tool integrations including:
 * - **PostgreSQL**: Read-only database queries with timeout/row limits
 * - **GitLab**: Code search, file reading, commits, MRs, issues
 * - **Elasticsearch**: Search and analytics across indexed data
 * - **HTTP Client**: RESTful API calls with domain whitelisting
 *
 * Features:
 * - Encrypted credential storage (Fernet AES-128)
 * - Connection testing before save
 * - Usage analytics and monitoring
 * - Multi-tenancy with user-level isolation
 * - Rate limiting (60 executions/min per user)
 *
 * All methods require authentication via JWT token.
 *
 * @module api/externalTools
 */

import { apiClient } from './client';
import type {
  ExternalToolConfig,
  ExternalToolConfigCreate,
  ExternalToolConfigUpdate,
  ExternalToolConfigListResponse,
  ToolCatalogResponse,
  ConnectionTestRequest,
  ConnectionTestResponse,
  ToolUsageAnalytics,
  ExternalToolFilters,
} from '../types/externalTool';

export const externalToolsApi = {
  /**
   * Fetch all external tool configurations with optional filters.
   *
   * Returns paginated list of tool configurations owned by the current user.
   * Use filters to narrow results by tool type or active status.
   *
   * @param {ExternalToolFilters} [filters] - Optional filters
   * @param {string} [filters.tool_type] - Filter by type (postgresql, gitlab, elasticsearch, http)
   * @param {boolean} [filters.is_active] - Filter by active status
   * @param {number} [filters.page] - Page number (1-indexed)
   * @param {number} [filters.page_size] - Results per page
   * @returns {Promise<ExternalToolConfigListResponse>} Paginated tool configuration list
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * // Get all active PostgreSQL configurations
   * const configs = await externalToolsApi.getAll({
   *   tool_type: 'postgresql',
   *   is_active: true
   * });
   */
  getAll: async (filters?: ExternalToolFilters): Promise<ExternalToolConfigListResponse> => {
    const params = new URLSearchParams();

    if (filters?.tool_type) params.append('tool_type', filters.tool_type);
    if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const response = await apiClient.get<ExternalToolConfigListResponse>(
      `/external-tools?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Fetch a single external tool configuration by ID.
   *
   * Returns complete configuration including encrypted credentials
   * (credentials are sanitized in response - only visibility flags shown).
   *
   * @param {number} id - Tool configuration ID to retrieve
   * @returns {Promise<ExternalToolConfig>} Tool configuration details
   * @throws {AxiosError} 404 if not found, 403 if not owner, 401 if not authenticated
   *
   * @example
   * const config = await externalToolsApi.getById(123);
   * console.log(config.tool_name, config.tool_type);
   */
  getById: async (id: number): Promise<ExternalToolConfig> => {
    const response = await apiClient.get<ExternalToolConfig>(`/external-tools/${id}`);
    return response.data;
  },

  /**
   * Create a new external tool configuration.
   *
   * Stores tool connection details with encrypted credentials.
   * Credentials are encrypted using Fernet (AES-128 CBC) before storage.
   *
   * @param {ExternalToolConfigCreate} data - Tool configuration data
   * @param {string} data.tool_name - Display name for the tool
   * @param {'postgresql' | 'gitlab' | 'elasticsearch' | 'http'} data.tool_type - Tool type
   * @param {Record<string, any>} data.config - Tool-specific configuration (host, database, etc.)
   * @returns {Promise<ExternalToolConfig>} Created tool configuration
   * @throws {AxiosError} 400 if validation fails, 409 if name exists, 401 if not authenticated
   *
   * @example
   * // Create PostgreSQL tool configuration
   * const config = await externalToolsApi.create({
   *   tool_name: 'Production DB',
   *   tool_type: 'postgresql',
   *   config: {
   *     host: 'db.example.com',
   *     port: 5432,
   *     database: 'myapp',
   *     username: 'readonly',
   *     password: 'secret123'
   *   }
   * });
   */
  create: async (data: ExternalToolConfigCreate): Promise<ExternalToolConfig> => {
    const response = await apiClient.post<ExternalToolConfig>('/external-tools', data);
    return response.data;
  },

  /**
   * Update an existing external tool configuration.
   *
   * Partial updates supported. If updating credentials, provide new values
   * in plaintext - they will be re-encrypted automatically.
   *
   * @param {number} id - Tool configuration ID to update
   * @param {ExternalToolConfigUpdate} data - Partial configuration data to update
   * @returns {Promise<ExternalToolConfig>} Updated tool configuration
   * @throws {AxiosError} 404 if not found, 403 if not owner, 400 if validation fails
   *
   * @example
   * const updated = await externalToolsApi.update(123, {
   *   is_active: false,
   *   config: { timeout: 60 }
   * });
   */
  update: async (id: number, data: ExternalToolConfigUpdate): Promise<ExternalToolConfig> => {
    const response = await apiClient.put<ExternalToolConfig>(`/external-tools/${id}`, data);
    return response.data;
  },

  /**
   * Delete an external tool configuration.
   *
   * Permanently removes tool configuration and encrypted credentials.
   * This action cannot be undone. Agents using this tool will lose access.
   *
   * @param {number} id - Tool configuration ID to delete
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if not found, 403 if not owner, 401 if not authenticated
   *
   * @example
   * await externalToolsApi.delete(123);
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/external-tools/${id}`);
  },

  /**
   * Test connection to an external tool.
   *
   * Validates credentials and connectivity before saving configuration.
   * For PostgreSQL: executes `SELECT 1` test query.
   * For GitLab: validates API token and fetches user info.
   * For Elasticsearch: pings cluster health endpoint.
   * For HTTP: performs GET request to base URL.
   *
   * @param {number} id - Tool configuration ID to test
   * @param {ConnectionTestRequest} [request] - Optional test parameters
   * @returns {Promise<ConnectionTestResponse>} Test result with success/failure details
   * @throws {AxiosError} 404 if configuration not found, 500 if connection fails
   *
   * @example
   * const result = await externalToolsApi.testConnection(123);
   * if (result.success) {
   *   console.log('Connection successful:', result.message);
   * } else {
   *   console.error('Connection failed:', result.error);
   * }
   */
  testConnection: async (
    id: number,
    request?: ConnectionTestRequest
  ): Promise<ConnectionTestResponse> => {
    const response = await apiClient.post<ConnectionTestResponse>(
      `/external-tools/${id}/test`,
      request || {}
    );
    return response.data;
  },

  /**
   * Fetch external tool catalog (marketplace).
   *
   * Returns metadata for all available external tool types including:
   * - Tool type ID and display name
   * - Description and use cases
   * - Required/optional configuration fields
   * - Capability descriptions
   *
   * Used to populate tool marketplace UI with available integrations.
   *
   * @returns {Promise<ToolCatalogResponse>} Tool catalog with metadata
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const catalog = await externalToolsApi.getCatalog();
   * catalog.tools.forEach(tool => {
   *   console.log(`${tool.name}: ${tool.description}`);
   * });
   */
  getCatalog: async (): Promise<ToolCatalogResponse> => {
    const response = await apiClient.get<ToolCatalogResponse>('/external-tools/catalog/all');
    return response.data;
  },

  /**
   * Fetch tool usage analytics.
   *
   * Returns execution statistics including:
   * - Total executions per tool type
   * - Success/failure rates
   * - Average execution time
   * - Most frequently used tools
   *
   * @param {number} [days=30] - Number of days to include in analytics
   * @returns {Promise<ToolUsageAnalytics>} Usage analytics data
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const analytics = await externalToolsApi.getAnalytics(7);
   * console.log(`PostgreSQL executions: ${analytics.by_tool_type.postgresql}`);
   */
  getAnalytics: async (days: number = 30): Promise<ToolUsageAnalytics> => {
    const response = await apiClient.get<ToolUsageAnalytics>(
      `/external-tools/analytics/usage?days=${days}`
    );
    return response.data;
  },

  /**
   * Get total count of tool configurations.
   *
   * Returns count of tools matching filters. Useful for pagination
   * and dashboard statistics.
   *
   * @param {ExternalToolFilters} [filters] - Optional filters
   * @returns {Promise<number>} Total count of matching configurations
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const activeCount = await externalToolsApi.getCount({ is_active: true });
   * console.log(`${activeCount} active tools`);
   */
  getCount: async (filters?: ExternalToolFilters): Promise<number> => {
    const params = new URLSearchParams();

    if (filters?.tool_type) params.append('tool_type', filters.tool_type);
    if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));

    const response = await apiClient.get<{ total: number }>(
      `/external-tools/count?${params.toString()}`
    );
    return response.data.total;
  },
};
