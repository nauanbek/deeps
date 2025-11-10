/**
 * React Query hooks for Monitoring API operations.
 *
 * Provides real-time monitoring hooks for dashboard metrics,
 * agent health, execution statistics, and token usage.
 * Most hooks use automatic refetching to keep data fresh.
 */

import { useQuery } from '@tanstack/react-query';
import { monitoringApi } from '../api/monitoring';

/**
 * Hook to fetch dashboard overview metrics.
 *
 * Retrieves high-level system metrics including total agents,
 * executions, success rate, and costs. Auto-refreshes every 30 seconds.
 *
 * @returns {UseQueryResult<DashboardOverview>} Query result containing dashboard metrics
 *
 * @example
 * const { data: overview } = useDashboardOverview();
 * console.log(`Total agents: ${overview?.total_agents}`);
 */
export const useDashboardOverview = () => {
  return useQuery({
    queryKey: ['monitoring', 'dashboard'],
    queryFn: monitoringApi.getDashboardOverview,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

/**
 * Hook to fetch agent health metrics.
 *
 * Retrieves health metrics for a specific agent or all agents,
 * including execution counts, success rate, and average execution time.
 * Auto-refreshes every 30 seconds.
 *
 * @param {number} [agentId] - Optional agent ID to filter by
 * @returns {UseQueryResult<AgentHealth[]>} Query result containing agent health data
 *
 * @example
 * // Get health for all agents
 * const { data: healthMetrics } = useAgentHealth();
 *
 * @example
 * // Get health for specific agent
 * const { data: agentHealth } = useAgentHealth(123);
 */
export const useAgentHealth = (agentId?: number) => {
  return useQuery({
    queryKey: ['monitoring', 'agents', 'health', agentId],
    queryFn: () => monitoringApi.getAgentHealth(agentId),
    refetchInterval: 30000,
  });
};

/**
 * Hook to fetch execution statistics by status.
 *
 * Returns execution counts grouped by status (completed, failed, etc.)
 * for a specified time period.
 *
 * @param {number} [days=7] - Number of days to include in statistics
 * @returns {UseQueryResult<ExecutionStats>} Query result containing execution statistics
 *
 * @example
 * const { data: stats } = useExecutionStats(30);
 * console.log(stats?.by_status.completed);
 */
export const useExecutionStats = (days: number = 7) => {
  return useQuery({
    queryKey: ['monitoring', 'executions', 'stats', days],
    queryFn: () => monitoringApi.getExecutionStats(days),
  });
};

/**
 * Hook to fetch token usage summary.
 *
 * Retrieves aggregated token usage (prompt, completion, total)
 * and estimated costs for a specified time period.
 *
 * @param {number} [days=30] - Number of days to include in summary
 * @returns {UseQueryResult<TokenUsageSummary>} Query result containing token usage data
 *
 * @example
 * const { data: usage } = useTokenUsage(7);
 * console.log(`Total tokens: ${usage?.total_tokens}`);
 * console.log(`Estimated cost: $${usage?.estimated_cost}`);
 */
export const useTokenUsage = (days: number = 30) => {
  return useQuery({
    queryKey: ['monitoring', 'usage', 'tokens', days],
    queryFn: () => monitoringApi.getTokenUsage(days),
  });
};

/**
 * Hook to fetch recent executions.
 *
 * Retrieves the most recent executions across all agents.
 * Auto-refreshes every 15 seconds to show latest activity.
 *
 * @param {number} [limit=10] - Maximum number of executions to return
 * @returns {UseQueryResult<Execution[]>} Query result containing recent executions
 *
 * @example
 * const { data: recent } = useRecentExecutions(20);
 */
export const useRecentExecutions = (limit: number = 10) => {
  return useQuery({
    queryKey: ['monitoring', 'executions', 'recent', limit],
    queryFn: () => monitoringApi.getRecentExecutions(limit),
    refetchInterval: 15000, // Refresh every 15 seconds
  });
};

/**
 * Hook to fetch recent execution errors.
 *
 * Retrieves the most recent failed executions with error messages.
 * Auto-refreshes every 30 seconds. Useful for error monitoring dashboards.
 *
 * @param {number} [limit=10] - Maximum number of errors to return
 * @returns {UseQueryResult<Execution[]>} Query result containing recent errors
 *
 * @example
 * const { data: errors } = useRecentErrors(5);
 * errors?.forEach(e => console.error(e.error_message));
 */
export const useRecentErrors = (limit: number = 10) => {
  return useQuery({
    queryKey: ['monitoring', 'executions', 'errors', limit],
    queryFn: () => monitoringApi.getRecentErrors(limit),
    refetchInterval: 30000,
  });
};

/**
 * Hook to fetch system-wide metrics.
 *
 * Legacy hook for backward compatibility. Provides comprehensive
 * system metrics. Auto-refreshes every 30 seconds.
 *
 * @returns {UseQueryResult<SystemMetrics>} Query result containing system metrics
 * @deprecated Use useDashboardOverview instead
 */
export const useSystemMetrics = () => {
  return useQuery({
    queryKey: ['monitoring', 'metrics'],
    queryFn: monitoringApi.getSystemMetrics,
    refetchInterval: 30000,
  });
};

/**
 * Hook to fetch execution timeline.
 *
 * Legacy hook for backward compatibility. Retrieves execution
 * history over time for timeline visualization.
 *
 * @param {number} [days=7] - Number of days to include
 * @returns {UseQueryResult<ExecutionTimeline>} Query result containing timeline data
 * @deprecated Use useExecutionTimeSeries from useAnalytics instead
 */
export const useExecutionTimeline = (days: number = 7) => {
  return useQuery({
    queryKey: ['monitoring', 'timeline', days],
    queryFn: () => monitoringApi.getExecutionTimeline(days),
  });
};

/**
 * Hook to fetch model usage statistics.
 *
 * Legacy hook for backward compatibility. Retrieves usage
 * breakdown by AI model (Claude, GPT, etc.).
 *
 * @returns {UseQueryResult<ModelUsage>} Query result containing model usage data
 * @deprecated Use useTokenUsageBreakdown from useAnalytics instead
 */
export const useModelUsage = () => {
  return useQuery({
    queryKey: ['monitoring', 'model-usage'],
    queryFn: monitoringApi.getModelUsage,
  });
};

/**
 * Hook to fetch system health status.
 *
 * Checks backend health including database connectivity,
 * Redis status, and API availability. Auto-refreshes every minute.
 *
 * @returns {UseQueryResult<HealthStatus>} Query result containing health status
 *
 * @example
 * const { data: health } = useHealthStatus();
 * if (health?.status === 'healthy') console.log('System OK');
 */
export const useHealthStatus = () => {
  return useQuery({
    queryKey: ['monitoring', 'health'],
    queryFn: monitoringApi.getHealth,
    refetchInterval: 60000,
  });
};
