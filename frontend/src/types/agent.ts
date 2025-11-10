export interface Agent {
  id: number;
  name: string;
  description: string | null;
  system_prompt: string;
  model_provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number | null;
  planning_enabled: boolean;
  filesystem_enabled: boolean;
  additional_config: Record<string, any>;
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  updated_at: string | null;
  langchain_tool_ids?: number[];
}

export interface AgentCreate {
  name: string;
  description?: string | null;
  system_prompt: string;
  model_provider: string;
  model_name: string;
  temperature?: number;
  max_tokens?: number | null;
  planning_enabled?: boolean;
  filesystem_enabled?: boolean;
  additional_config?: Record<string, any>;
}

export interface AgentUpdate {
  name?: string;
  description?: string | null;
  system_prompt?: string;
  model_provider?: string;
  model_name?: string;
  temperature?: number;
  max_tokens?: number | null;
  planning_enabled?: boolean;
  filesystem_enabled?: boolean;
  additional_config?: Record<string, any>;
  langchain_tool_ids?: number[];
}

export interface AgentMetrics {
  agent_id: number;
  agent_name: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_duration_seconds: number;
  total_tokens_used: number;
  last_execution_at: string | null;
}
