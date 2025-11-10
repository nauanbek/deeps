/**
 * Monitoring API Client
 *
 * Provides HTTP methods for real-time system monitoring, dashboard metrics,
 * agent health tracking, and execution statistics. Used by dashboard and
 * monitoring pages for live system status visualization.
 *
 * @module api/monitoring
 */

import { apiClient } from './client';
import type {
  DashboardOverview,
  AgentHealth,
  ExecutionStats,
  TokenUsageSummary,
  SystemMetrics,
  ExecutionTimeline,
  ModelUsage,
  HealthStatus,
} from '../types/monitoring';
import type { Execution } from '../types/execution';

/**
 * Monitoring API methods for system health and metrics.
 * All methods require authentication via JWT token.
 */
export const monitoringApi = {
  /**
   * Fetch dashboard overview metrics.
   *
   * Returns high-level system metrics including total agents, executions,
   * success rate, and costs. Ideal for dashboard widgets.
   *
   * @returns {Promise<DashboardOverview>} Dashboard metrics
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const overview = await monitoringApi.getDashboardOverview();
   * console.log(`Total agents: ${overview.total_agents}`);
   */
  getDashboardOverview: async (): Promise<DashboardOverview> => {
    const response = await apiClient.get<DashboardOverview>('/monitoring/dashboard');
    return response.data;
  },

  /**
   * Fetch agent health metrics.
   *
   * Returns health metrics for all agents or a specific agent including
   * execution counts, success rate, and average execution time.
   *
   * @param {number} [agentId] - Optional agent ID to filter by
   * @returns {Promise<AgentHealth[]>} Agent health metrics
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const allHealth = await monitoringApi.getAgentHealth();
   * const specificHealth = await monitoringApi.getAgentHealth(123);
   */
  getAgentHealth: async (agentId?: number): Promise<AgentHealth[]> => {
    const response = await apiClient.get<AgentHealth[]>('/monitoring/agents/health', {
      params: agentId ? { agent_id: agentId } : {},
    });
    return response.data;
  },

  /**
   * Fetch execution statistics by status.
   *
   * Returns execution counts grouped by status (completed, failed, etc.)
   * for the specified time period.
   *
   * @param {number} [days=7] - Number of days to include in statistics
   * @returns {Promise<ExecutionStats>} Execution statistics
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const stats = await monitoringApi.getExecutionStats(30);
   * console.log(stats.by_status.completed);
   */
  getExecutionStats: async (days: number = 7): Promise<ExecutionStats> => {
    const response = await apiClient.get<ExecutionStats>('/monitoring/executions/stats', {
      params: { days },
    });
    return response.data;
  },

  /**
   * Fetch token usage summary.
   *
   * Returns aggregated token usage (prompt, completion, total) and
   * estimated costs for the specified time period.
   *
   * @param {number} [days=30] - Number of days to include
   * @returns {Promise<TokenUsageSummary>} Token usage summary
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const usage = await monitoringApi.getTokenUsage(7);
   * console.log(`Cost: $${usage.estimated_cost}`);
   */
  getTokenUsage: async (days: number = 30): Promise<TokenUsageSummary> => {
    const response = await apiClient.get<TokenUsageSummary>('/monitoring/usage/tokens', {
      params: { days },
    });
    return response.data;
  },

  /**
   * Fetch recent executions.
   *
   * Returns the most recent executions across all agents,
   * sorted by creation time descending.
   *
   * @param {number} [limit=10] - Maximum number to return
   * @returns {Promise<Execution[]>} Recent executions
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const recent = await monitoringApi.getRecentExecutions(20);
   */
  getRecentExecutions: async (limit: number = 10): Promise<Execution[]> => {
    const response = await apiClient.get<Execution[]>('/monitoring/executions/recent', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Fetch recent execution errors.
   *
   * Returns the most recent failed executions with error messages.
   * Useful for error monitoring dashboards.
   *
   * @param {number} [limit=10] - Maximum number to return
   * @returns {Promise<Execution[]>} Recent failed executions
   * @throws {AxiosError} 401 if not authenticated
   *
   * @example
   * const errors = await monitoringApi.getRecentErrors(5);
   * errors.forEach(e => console.error(e.error_message));
   */
  getRecentErrors: async (limit: number = 10): Promise<Execution[]> => {
    const response = await apiClient.get<Execution[]>('/monitoring/executions/errors', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Fetch system-wide metrics (legacy).
   *
   * @deprecated Use getDashboardOverview instead
   * @returns {Promise<SystemMetrics>} System metrics
   */
  getSystemMetrics: async (): Promise<SystemMetrics> => {
    const response = await apiClient.get<SystemMetrics>('/monitoring/metrics');
    return response.data;
  },

  /**
   * Fetch execution timeline (legacy).
   *
   * @deprecated Use analytics API getExecutionTimeSeries instead
   * @param {number} [days=7] - Number of days
   * @returns {Promise<ExecutionTimeline[]>} Timeline data
   */
  getExecutionTimeline: async (days: number = 7): Promise<ExecutionTimeline[]> => {
    const response = await apiClient.get<ExecutionTimeline[]>('/monitoring/timeline', {
      params: { days },
    });
    return response.data;
  },

  /**
   * Fetch model usage statistics (legacy).
   *
   * @deprecated Use analytics API getTokenUsageBreakdown instead
   * @returns {Promise<ModelUsage[]>} Model usage data
   */
  getModelUsage: async (): Promise<ModelUsage[]> => {
    const response = await apiClient.get<ModelUsage[]>('/monitoring/model-usage');
    return response.data;
  },

  /**
   * Fetch system health status.
   *
   * Checks backend health including database connectivity,
   * Redis status, and API availability.
   *
   * @returns {Promise<HealthStatus>} Health status
   *
   * @example
   * const health = await monitoringApi.getHealth();
   * if (health.status === 'healthy') console.log('System OK');
   */
  getHealth: async (): Promise<HealthStatus> => {
    const response = await apiClient.get<HealthStatus>('/health');
    return response.data;
  },
};
