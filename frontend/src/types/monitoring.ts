// Dashboard overview metrics
export interface DashboardOverview {
  total_agents: number;
  active_agents?: number; // Not in backend but useful for UI
  total_executions: number;
  executions_today: number;
  success_rate: number;
  avg_execution_time?: number; // Not in backend schema but useful
  total_tokens_used: number;
  estimated_total_cost: number;
}

// Agent health metrics
export interface AgentHealth {
  agent_id: number;
  agent_name: string;
  total_executions: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  avg_execution_time: number;
  last_execution_at: string | null;
}

// Execution statistics
export interface ExecutionStats {
  by_status: {
    pending: number;
    running: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
  period_days: number;
}

// Token usage summary
export interface TokenUsageSummary {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost: number;
  period_days: number;
}

// Legacy interfaces for backward compatibility
export interface SystemMetrics {
  total_agents: number;
  active_agents: number;
  total_executions: number;
  running_executions: number;
  success_rate: number;
  average_execution_time: number;
  total_tokens_used: number;
}

export interface ExecutionTimeline {
  date: string;
  total_executions: number;
  successful: number;
  failed: number;
}

export interface ModelUsage {
  model: string;
  execution_count: number;
  total_tokens: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'down';
  database: boolean;
  cache: boolean;
  timestamp: string;
}
