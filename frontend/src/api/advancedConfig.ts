/**
 * Advanced Configuration API Client
 *
 * Provides HTTP methods for managing advanced deepagents features including:
 * - **Backend Storage**: Configure StateBackend, FilesystemBackend, StoreBackend, or CompositeBackend
 * - **Long-term Memory**: Create persistent memory namespaces and manage memory files
 * - **Human-in-the-Loop (HITL)**: Configure approval workflows for sensitive tool operations
 * - **Execution Approvals**: Submit approve/reject/edit decisions for pending tool calls
 *
 * These features unlock the full power of the deepagents framework for
 * sophisticated agent architectures with persistent state, memory, and human oversight.
 *
 * All methods require authentication via JWT token.
 *
 * @module api/advancedConfig
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface BackendConfig {
  id?: number;
  agent_id?: number;
  backend_type: 'state' | 'filesystem' | 'store' | 'composite';
  config: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface MemoryNamespace {
  id?: number;
  agent_id?: number;
  namespace: string;
  store_type: 'postgresql' | 'redis' | 'custom';
  config: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface MemoryFile {
  key: string;
  value?: string;
  size_bytes: number;
  content_type?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MemoryFileList {
  namespace: string;
  files: MemoryFile[];
  total_files: number;
  total_size_bytes: number;
}

export interface InterruptConfig {
  id?: number;
  agent_id?: number;
  tool_name: string;
  allowed_decisions: Array<'approve' | 'edit' | 'reject'>;
  config: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface ExecutionApproval {
  id: number;
  execution_id: number;
  tool_name: string;
  tool_args: Record<string, any>;
  status: 'pending' | 'approved' | 'rejected' | 'edited';
  decision_data: Record<string, any>;
  decided_by_id?: number;
  decided_at?: string;
  created_at: string;
}

export interface ApprovalDecision {
  decision: 'approve' | 'reject' | 'edit';
  edited_args?: Record<string, any>;
  reason?: string;
}

export interface AgentAdvancedConfig {
  backend_config?: BackendConfig;
  memory_namespace?: MemoryNamespace;
  interrupt_configs: InterruptConfig[];
}

// ============================================================================
// API Client
// ============================================================================

export const advancedConfigApi = {
  // ============================================================================
  // Backend Configuration
  // ============================================================================

  /**
   * Create backend storage configuration for an agent.
   *
   * Configures how the agent stores data during execution. Options include:
   * - **state**: In-memory state (default, ephemeral)
   * - **filesystem**: File operations with optional sandboxing
   * - **store**: PostgreSQL persistent storage (long-term memory)
   * - **composite**: Hybrid routing (e.g., /memories/ → store, /scratch/ → state)
   *
   * @param {number} agentId - Agent ID to configure
   * @param {Object} data - Backend configuration data
   * @param {'state' | 'filesystem' | 'store' | 'composite'} data.backend_type - Backend type
   * @param {Record<string, any>} data.config - Backend-specific configuration JSON
   * @returns {Promise<BackendConfig>} Created backend configuration
   * @throws {AxiosError} 404 if agent not found, 400 if validation fails
   *
   * @example
   * // Configure composite backend with persistent memory
   * const config = await advancedConfigApi.createBackendConfig(123, {
   *   backend_type: 'composite',
   *   config: {
   *     routes: {
   *       '/memories/': { type: 'store' }
   *     },
   *     default: { type: 'state' }
   *   }
   * });
   */
  createBackendConfig: async (agentId: number, data: Omit<BackendConfig, 'id' | 'agent_id' | 'created_at' | 'updated_at'>): Promise<BackendConfig> => {
    const response = await apiClient.post<BackendConfig>(`/agents/${agentId}/backend`, data);
    return response.data;
  },

  /**
   * Fetch backend storage configuration for an agent.
   *
   * @param {number} agentId - Agent ID to query
   * @returns {Promise<BackendConfig>} Backend configuration
   * @throws {AxiosError} 404 if agent not found or no config exists
   *
   * @example
   * const config = await advancedConfigApi.getBackendConfig(123);
   * console.log('Backend type:', config.backend_type);
   */
  getBackendConfig: async (agentId: number): Promise<BackendConfig> => {
    const response = await apiClient.get<BackendConfig>(`/agents/${agentId}/backend`);
    return response.data;
  },

  /**
   * Update backend storage configuration.
   *
   * @param {number} agentId - Agent ID to update
   * @param {Object} data - Partial backend configuration to update
   * @returns {Promise<BackendConfig>} Updated backend configuration
   * @throws {AxiosError} 404 if agent or config not found, 400 if validation fails
   *
   * @example
   * const updated = await advancedConfigApi.updateBackendConfig(123, {
   *   config: { sandbox: true }
   * });
   */
  updateBackendConfig: async (agentId: number, data: Partial<Omit<BackendConfig, 'id' | 'agent_id' | 'created_at' | 'updated_at'>>): Promise<BackendConfig> => {
    const response = await apiClient.put<BackendConfig>(`/agents/${agentId}/backend`, data);
    return response.data;
  },

  /**
   * Delete backend storage configuration.
   *
   * Reverts agent to default in-memory state backend.
   *
   * @param {number} agentId - Agent ID to delete config for
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if agent or config not found
   *
   * @example
   * await advancedConfigApi.deleteBackendConfig(123);
   */
  deleteBackendConfig: async (agentId: number): Promise<void> => {
    await apiClient.delete(`/agents/${agentId}/backend`);
  },

  // ============================================================================
  // Memory Namespace
  // ============================================================================

  /**
   * Create long-term memory namespace for an agent.
   *
   * Enables persistent memory storage across agent sessions. Memory files
   * stored in this namespace persist in PostgreSQL and are accessible
   * via the `/memories/` path during agent execution.
   *
   * @param {number} agentId - Agent ID to create namespace for
   * @param {Object} [data={}] - Namespace configuration
   * @param {string} [data.store_type='postgresql'] - Storage backend type
   * @param {Record<string, any>} [data.config] - Store-specific configuration
   * @returns {Promise<MemoryNamespace>} Created memory namespace
   * @throws {AxiosError} 404 if agent not found, 409 if namespace already exists
   *
   * @example
   * const namespace = await advancedConfigApi.createMemoryNamespace(123);
   * console.log('Memory namespace created:', namespace.namespace);
   */
  createMemoryNamespace: async (agentId: number, data: { store_type?: string; config?: Record<string, any> } = {}): Promise<MemoryNamespace> => {
    const response = await apiClient.post<MemoryNamespace>(`/agents/${agentId}/memory/namespace`, data);
    return response.data;
  },

  /**
   * Fetch memory namespace for an agent.
   *
   * @param {number} agentId - Agent ID to query
   * @returns {Promise<MemoryNamespace>} Memory namespace details
   * @throws {AxiosError} 404 if agent not found or no namespace exists
   *
   * @example
   * const namespace = await advancedConfigApi.getMemoryNamespace(123);
   */
  getMemoryNamespace: async (agentId: number): Promise<MemoryNamespace> => {
    const response = await apiClient.get<MemoryNamespace>(`/agents/${agentId}/memory/namespace`);
    return response.data;
  },

  /**
   * Delete memory namespace and all associated memory files.
   *
   * WARNING: This permanently deletes all memory files for the agent.
   *
   * @param {number} agentId - Agent ID to delete namespace for
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if agent or namespace not found
   *
   * @example
   * await advancedConfigApi.deleteMemoryNamespace(123);
   */
  deleteMemoryNamespace: async (agentId: number): Promise<void> => {
    await apiClient.delete(`/agents/${agentId}/memory/namespace`);
  },

  // ============================================================================
  // Memory Files
  // ============================================================================

  /**
   * List memory files in agent's namespace.
   *
   * Returns all memory files with optional prefix filtering.
   * Memory files are persistent across agent sessions and accessible
   * via `/memories/{key}` during execution.
   *
   * @param {number} agentId - Agent ID to query
   * @param {string} [prefix] - Optional prefix filter (e.g., 'context/')
   * @returns {Promise<MemoryFileList>} List of memory files with metadata
   * @throws {AxiosError} 404 if agent or namespace not found
   *
   * @example
   * const files = await advancedConfigApi.listMemoryFiles(123);
   * console.log(`${files.total_files} files, ${files.total_size_bytes} bytes`);
   *
   * @example
   * // List files with prefix
   * const contextFiles = await advancedConfigApi.listMemoryFiles(123, 'context/');
   */
  listMemoryFiles: async (agentId: number, prefix?: string): Promise<MemoryFileList> => {
    const params = prefix ? { prefix } : {};
    const response = await apiClient.get<MemoryFileList>(`/agents/${agentId}/memory/files`, { params });
    return response.data;
  },

  /**
   * Fetch a single memory file by key.
   *
   * Returns file content and metadata.
   *
   * @param {number} agentId - Agent ID to query
   * @param {string} fileKey - File key (path) in memory namespace
   * @returns {Promise<MemoryFile>} Memory file with content
   * @throws {AxiosError} 404 if file not found
   *
   * @example
   * const file = await advancedConfigApi.getMemoryFile(123, 'context.md');
   * console.log('Content:', file.value);
   */
  getMemoryFile: async (agentId: number, fileKey: string): Promise<MemoryFile> => {
    const response = await apiClient.get<MemoryFile>(`/agents/${agentId}/memory/files/${encodeURIComponent(fileKey)}`);
    return response.data;
  },

  /**
   * Create or update a memory file.
   *
   * Stores file content in PostgreSQL for persistent access across sessions.
   * If file key exists, it will be updated.
   *
   * @param {number} agentId - Agent ID to store file for
   * @param {Object} data - File data
   * @param {string} data.key - File key (path) in namespace
   * @param {string} data.value - File content (text)
   * @param {string} [data.content_type='text/plain'] - MIME content type
   * @returns {Promise<MemoryFile>} Created memory file
   * @throws {AxiosError} 404 if namespace not found, 400 if validation fails
   *
   * @example
   * const file = await advancedConfigApi.createMemoryFile(123, {
   *   key: 'research_context.md',
   *   value: '# Research Context\n\nCurrent focus: AI safety',
   *   content_type: 'text/markdown'
   * });
   */
  createMemoryFile: async (agentId: number, data: { key: string; value: string; content_type?: string }): Promise<MemoryFile> => {
    const response = await apiClient.post<MemoryFile>(`/agents/${agentId}/memory/files`, data);
    return response.data;
  },

  /**
   * Delete a memory file.
   *
   * Permanently removes file from memory namespace.
   *
   * @param {number} agentId - Agent ID
   * @param {string} fileKey - File key to delete
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if file not found
   *
   * @example
   * await advancedConfigApi.deleteMemoryFile(123, 'old_context.md');
   */
  deleteMemoryFile: async (agentId: number, fileKey: string): Promise<void> => {
    await apiClient.delete(`/agents/${agentId}/memory/files/${encodeURIComponent(fileKey)}`);
  },

  // ============================================================================
  // HITL Interrupt Configuration
  // ============================================================================

  /**
   * Create HITL (Human-in-the-Loop) interrupt configuration.
   *
   * Configures which tools require human approval before execution.
   * When an agent attempts to use a configured tool, execution pauses
   * and waits for human approval/rejection/editing.
   *
   * @param {number} agentId - Agent ID to configure
   * @param {Object} data - Interrupt configuration
   * @param {string} data.tool_name - Tool name to intercept (e.g., 'delete_file')
   * @param {Array<'approve' | 'edit' | 'reject'>} data.allowed_decisions - Allowed decision types
   * @param {Record<string, any>} [data.config] - Additional configuration
   * @returns {Promise<InterruptConfig>} Created interrupt configuration
   * @throws {AxiosError} 404 if agent not found, 409 if tool already configured
   *
   * @example
   * // Require approval for file deletion
   * const config = await advancedConfigApi.createInterruptConfig(123, {
   *   tool_name: 'delete_file',
   *   allowed_decisions: ['approve', 'reject'],
   *   config: { notification_email: 'admin@example.com' }
   * });
   */
  createInterruptConfig: async (agentId: number, data: Omit<InterruptConfig, 'id' | 'agent_id' | 'created_at' | 'updated_at'>): Promise<InterruptConfig> => {
    const response = await apiClient.post<InterruptConfig>(`/agents/${agentId}/interrupt`, data);
    return response.data;
  },

  /**
   * List all HITL interrupt configurations for an agent.
   *
   * @param {number} agentId - Agent ID to query
   * @returns {Promise<Object>} List of interrupt configurations
   * @throws {AxiosError} 404 if agent not found
   *
   * @example
   * const { configs, total } = await advancedConfigApi.listInterruptConfigs(123);
   * console.log(`${total} tools require approval`);
   */
  listInterruptConfigs: async (agentId: number): Promise<{ configs: InterruptConfig[]; total: number }> => {
    const response = await apiClient.get<{ configs: InterruptConfig[]; total: number }>(`/agents/${agentId}/interrupt`);
    return response.data;
  },

  /**
   * Fetch interrupt configuration for a specific tool.
   *
   * @param {number} agentId - Agent ID to query
   * @param {string} toolName - Tool name to query
   * @returns {Promise<InterruptConfig>} Interrupt configuration
   * @throws {AxiosError} 404 if configuration not found
   *
   * @example
   * const config = await advancedConfigApi.getInterruptConfig(123, 'delete_file');
   */
  getInterruptConfig: async (agentId: number, toolName: string): Promise<InterruptConfig> => {
    const response = await apiClient.get<InterruptConfig>(`/agents/${agentId}/interrupt/${encodeURIComponent(toolName)}`);
    return response.data;
  },

  /**
   * Update interrupt configuration for a tool.
   *
   * @param {number} agentId - Agent ID
   * @param {string} toolName - Tool name to update
   * @param {Object} data - Partial configuration to update
   * @returns {Promise<InterruptConfig>} Updated interrupt configuration
   * @throws {AxiosError} 404 if configuration not found
   *
   * @example
   * const updated = await advancedConfigApi.updateInterruptConfig(123, 'delete_file', {
   *   allowed_decisions: ['approve', 'edit', 'reject']
   * });
   */
  updateInterruptConfig: async (agentId: number, toolName: string, data: Partial<Omit<InterruptConfig, 'id' | 'agent_id' | 'tool_name' | 'created_at' | 'updated_at'>>): Promise<InterruptConfig> => {
    const response = await apiClient.put<InterruptConfig>(`/agents/${agentId}/interrupt/${encodeURIComponent(toolName)}`, data);
    return response.data;
  },

  /**
   * Delete interrupt configuration for a tool.
   *
   * Removes approval requirement - tool will execute without interruption.
   *
   * @param {number} agentId - Agent ID
   * @param {string} toolName - Tool name to remove interrupt for
   * @returns {Promise<void>}
   * @throws {AxiosError} 404 if configuration not found
   *
   * @example
   * await advancedConfigApi.deleteInterruptConfig(123, 'delete_file');
   */
  deleteInterruptConfig: async (agentId: number, toolName: string): Promise<void> => {
    await apiClient.delete(`/agents/${agentId}/interrupt/${encodeURIComponent(toolName)}`);
  },

  // ============================================================================
  // Execution Approvals (HITL)
  // ============================================================================

  /**
   * List approval requests for an execution.
   *
   * Returns all approval requests (pending, approved, rejected, edited)
   * for a specific agent execution. Use this to build approval UIs.
   *
   * @param {number} executionId - Execution ID to query
   * @param {string} [statusFilter] - Filter by status ('pending', 'approved', 'rejected', 'edited')
   * @returns {Promise<Object>} Approval list with counts
   * @throws {AxiosError} 404 if execution not found
   *
   * @example
   * const { approvals, pending_count } = await advancedConfigApi.listExecutionApprovals(456);
   * console.log(`${pending_count} approvals awaiting decision`);
   */
  listExecutionApprovals: async (executionId: number, statusFilter?: string): Promise<{ approvals: ExecutionApproval[]; total: number; pending_count: number }> => {
    const params = statusFilter ? { status_filter: statusFilter } : {};
    const response = await apiClient.get<{ approvals: ExecutionApproval[]; total: number; pending_count: number }>(`/executions/${executionId}/approvals`, { params });
    return response.data;
  },

  /**
   * Fetch a single approval request.
   *
   * @param {number} executionId - Execution ID
   * @param {number} approvalId - Approval ID to fetch
   * @returns {Promise<ExecutionApproval>} Approval details including tool name and arguments
   * @throws {AxiosError} 404 if approval not found
   *
   * @example
   * const approval = await advancedConfigApi.getExecutionApproval(456, 789);
   * console.log(`Tool: ${approval.tool_name}`, approval.tool_args);
   */
  getExecutionApproval: async (executionId: number, approvalId: number): Promise<ExecutionApproval> => {
    const response = await apiClient.get<ExecutionApproval>(`/executions/${executionId}/approvals/${approvalId}`);
    return response.data;
  },

  /**
   * Submit approval decision (approve/reject/edit).
   *
   * Decides whether to allow, deny, or modify a tool execution request.
   * - **approve**: Allow tool to execute with original arguments
   * - **reject**: Deny tool execution
   * - **edit**: Modify tool arguments before execution
   *
   * @param {number} executionId - Execution ID
   * @param {number} approvalId - Approval ID to decide
   * @param {ApprovalDecision} decision - Decision data
   * @param {'approve' | 'reject' | 'edit'} decision.decision - Decision type
   * @param {Record<string, any>} [decision.edited_args] - Modified arguments (required for 'edit')
   * @param {string} [decision.reason] - Optional reason for decision
   * @returns {Promise<ExecutionApproval>} Updated approval with decision
   * @throws {AxiosError} 404 if approval not found, 400 if decision invalid
   *
   * @example
   * // Approve tool execution
   * await advancedConfigApi.submitApprovalDecision(456, 789, {
   *   decision: 'approve',
   *   reason: 'Looks safe to proceed'
   * });
   *
   * @example
   * // Edit tool arguments before execution
   * await advancedConfigApi.submitApprovalDecision(456, 789, {
   *   decision: 'edit',
   *   edited_args: { file_path: '/safe/path.txt' },
   *   reason: 'Redirected to safe directory'
   * });
   */
  submitApprovalDecision: async (executionId: number, approvalId: number, decision: ApprovalDecision): Promise<ExecutionApproval> => {
    const response = await apiClient.post<ExecutionApproval>(`/executions/${executionId}/approvals/${approvalId}/decide`, decision);
    return response.data;
  },

  // ============================================================================
  // Combined Endpoint
  // ============================================================================

  /**
   * Fetch all advanced configuration for an agent in a single request.
   *
   * Returns backend config, memory namespace, and interrupt configs together.
   * More efficient than making 3 separate API calls when loading agent settings.
   *
   * @param {number} agentId - Agent ID to query
   * @returns {Promise<AgentAdvancedConfig>} All advanced configuration
   * @throws {AxiosError} 404 if agent not found
   *
   * @example
   * const config = await advancedConfigApi.getAllAdvancedConfig(123);
   * console.log('Backend:', config.backend_config?.backend_type);
   * console.log('Memory:', config.memory_namespace?.namespace);
   * console.log('HITL rules:', config.interrupt_configs.length);
   */
  getAllAdvancedConfig: async (agentId: number): Promise<AgentAdvancedConfig> => {
    const response = await apiClient.get<AgentAdvancedConfig>(`/agents/${agentId}/advanced-config`);
    return response.data;
  },
};

export default advancedConfigApi;
