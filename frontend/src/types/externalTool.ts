/**
 * External Tool type definitions for LangChain Tools Integration
 *
 * These types correspond to the backend external_tool schemas
 */

// Tool types available in the system
export type ExternalToolType = 'postgresql' | 'gitlab' | 'elasticsearch' | 'http';

// Tool categories for marketplace
export type ToolCategory = 'database' | 'git' | 'logs' | 'monitoring' | 'http';

// Test status values
export type TestStatus = 'not_tested' | 'success' | 'failed';

/**
 * External Tool Configuration
 */
export interface ExternalToolConfig {
  id: number;
  user_id: number;
  tool_name: string;
  tool_type: ExternalToolType;
  provider: string;
  configuration: Record<string, any>;
  is_active: boolean;
  test_status: TestStatus | null;
  test_error_message: string | null;
  last_tested_at: string | null;
  created_at: string;
  updated_at: string | null;
}

/**
 * Create external tool configuration
 */
export interface ExternalToolConfigCreate {
  tool_name: string;
  tool_type: ExternalToolType;
  provider?: string;
  configuration: Record<string, any>;
}

/**
 * Update external tool configuration
 */
export interface ExternalToolConfigUpdate {
  tool_name?: string;
  configuration?: Record<string, any>;
  is_active?: boolean;
}

/**
 * Tool catalog item (marketplace)
 */
export interface ToolCatalogItem {
  tool_type: ExternalToolType;
  provider: string;
  name: string;
  description: string;
  category: ToolCategory;
  icon: string;
  required_fields: string[];
  optional_fields: string[];
  example_configuration: Record<string, any>;
}

/**
 * Connection test request
 */
export interface ConnectionTestRequest {
  override_config?: Record<string, any>;
}

/**
 * Connection test response
 */
export interface ConnectionTestResponse {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

/**
 * Tool usage statistics
 */
export interface ToolUsageStats {
  tool_name: string;
  tool_type: ExternalToolType;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  avg_duration_ms: number;
  last_execution_at: string | null;
}

/**
 * Tool usage analytics response
 */
export interface ToolUsageAnalytics {
  total_tools: number;
  active_tools: number;
  total_executions: number;
  success_rate: number;
  tools: ToolUsageStats[];
  time_range: string;
}

/**
 * Paginated tool config list response
 */
export interface ExternalToolConfigListResponse {
  tools: ExternalToolConfig[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

/**
 * Tool catalog response (all available tools)
 */
export interface ToolCatalogResponse {
  tools: ToolCatalogItem[];
  total: number;
}

/**
 * Tool execution log entry
 */
export interface ToolExecutionLog {
  id: number;
  tool_config_id: number;
  tool_name: string;
  tool_type: ExternalToolType;
  user_id: number;
  agent_id: number | null;
  execution_id: number | null;
  input_params: Record<string, any>;
  output_result: string | null;
  success: boolean;
  duration_ms: number;
  error_message: string | null;
  created_at: string;
}

/**
 * Tool filters for listing
 */
export interface ExternalToolFilters {
  tool_type?: ExternalToolType;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

/**
 * Tool configuration field definition (for dynamic forms)
 */
export interface ToolConfigField {
  name: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'password' | 'url';
  required: boolean;
  default?: any;
  placeholder?: string;
  description?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    options?: string[];
  };
}

/**
 * Tool configuration schema (for dynamic form generation)
 */
export interface ToolConfigSchema {
  tool_type: ExternalToolType;
  fields: ToolConfigField[];
}
