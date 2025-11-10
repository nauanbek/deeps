export interface TimeSeriesDataPoint {
  timestamp: string;
  total_executions: number;
  successful: number;
  failed: number;
  cancelled: number;
  avg_duration_seconds: number;
  total_tokens: number;
  estimated_cost: number;
}

export interface AgentUsageRanking {
  agent_id: number;
  agent_name: string;
  execution_count: number;
  success_rate: number;
  total_tokens: number;
  estimated_cost: number;
  avg_duration_seconds: number;
}

export interface TokenBreakdownItem {
  group_key: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost: number;
}

export interface TokenBreakdown {
  total_tokens: number;
  total_cost: number;
  breakdown: TokenBreakdownItem[];
}

export interface ErrorAnalysisItem {
  error_pattern: string;
  count: number;
  affected_agents: number[];
  first_seen: string;
  last_seen: string;
}

export interface PerformanceMetrics {
  total_executions: number;
  success_rate: number;
  avg_duration_seconds: number;
  min_duration_seconds: number;
  max_duration_seconds: number;
  p50_duration_seconds: number;
  p95_duration_seconds: number;
  p99_duration_seconds: number;
  avg_tokens_per_execution: number;
  total_cost: number;
  uptime_percentage: number;
}

export interface AgentPerformance {
  agent_id: number;
  agent_name: string;
  metrics: PerformanceMetrics;
  recent_failures: Array<{
    execution_id: number;
    error_message: string;
    timestamp: string;
  }>;
}

export interface SystemPerformance {
  uptime_seconds: number;
  total_agents: number;
  active_agents: number;
  total_executions: number;
  executions_last_24h: number;
  success_rate_last_24h: number;
  avg_response_time_ms: number;
  database_size_mb: number;
  cache_hit_rate: number;
}

export interface CostRecommendation {
  type: string;
  description: string;
  agent_id: number | null;
  estimated_savings: number;
  impact: string;
}

export interface CostRecommendations {
  total_cost: number;
  potential_savings: number;
  recommendations: CostRecommendation[];
}

export interface CostProjections {
  current_daily_cost: number;
  projected_monthly_cost: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  trend_percentage: number;
  breakdown_by_agent: Array<{
    agent_id: number;
    agent_name: string;
    projected_cost: number;
    percentage_of_total: number;
  }>;
}
