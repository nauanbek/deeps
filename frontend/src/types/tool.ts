/**
 * Tool type definitions for the DeepAgents Control Platform
 */

export interface Tool {
  id: number;
  name: string;
  description: string | null;
  tool_type: 'builtin' | 'custom' | 'langgraph';
  configuration: Record<string, any> | null;
  schema_definition: Record<string, any> | null;
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface ToolCreate {
  name: string;
  description?: string;
  tool_type: 'builtin' | 'custom' | 'langgraph';
  configuration?: Record<string, any>;
  schema_definition?: Record<string, any>;
}

export interface ToolUpdate {
  name?: string;
  description?: string;
  tool_type?: 'builtin' | 'custom' | 'langgraph';
  configuration?: Record<string, any>;
  schema_definition?: Record<string, any>;
  is_active?: boolean;
}

export interface ToolFilters {
  skip?: number;
  limit?: number;
  tool_type?: string;
  search?: string;
  is_active?: boolean;
}

export interface ToolCategoriesResponse {
  categories: string[];
}
