/**
 * Analytics API Client
 *
 * Provides HTTP methods for retrieving detailed analytics including:
 * - Time-series execution data with customizable intervals
 * - Agent usage rankings and popularity metrics
 * - Token usage breakdowns by agent/model/day
 * - Error analysis and debugging insights
 * - Agent and system performance metrics
 * - Cost optimization recommendations
 * - Cost projection forecasts
 *
 * All methods require date range parameters and support filtering/grouping.
 *
 * @module api/analytics
 */

import { apiClient } from './client';
import {
  TimeSeriesDataPoint,
  AgentUsageRanking,
  TokenBreakdown,
  ErrorAnalysisItem,
  AgentPerformance,
  SystemPerformance,
  CostRecommendations,
  CostProjections,
} from '../types/analytics';

/**
 * Fetch time-series analytics for executions.
 *
 * Returns execution counts over time with configurable granularity.
 * Useful for trend analysis, usage graphs, and activity monitoring.
 *
 * @param {string} startDate - Start date in ISO 8601 format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO 8601 format (YYYY-MM-DD)
 * @param {'hour' | 'day' | 'week' | 'month'} interval - Time interval granularity
 * @param {number} [agentId] - Optional agent ID to filter by specific agent
 * @returns {Promise<TimeSeriesDataPoint[]>} Array of time-series data points
 * @throws {AxiosError} 401 if not authenticated, 422 if date range invalid
 *
 * @example
 * // Get daily execution trend for last 30 days
 * const timeSeries = await getExecutionTimeSeries(
 *   '2025-10-01',
 *   '2025-10-31',
 *   'day'
 * );
 *
 * @example
 * // Get hourly trend for specific agent
 * const agentTrend = await getExecutionTimeSeries(
 *   '2025-11-01',
 *   '2025-11-10',
 *   'hour',
 *   123
 * );
 */
export const getExecutionTimeSeries = async (
  startDate: string,
  endDate: string,
  interval: 'hour' | 'day' | 'week' | 'month',
  agentId?: number
): Promise<TimeSeriesDataPoint[]> => {
  const params: Record<string, string> = {
    start_date: startDate,
    end_date: endDate,
    interval,
  };

  if (agentId !== undefined) {
    params.agent_id = agentId.toString();
  }

  const response = await apiClient.get<{ data: TimeSeriesDataPoint[] }>(
    '/analytics/executions/time-series',
    { params }
  );
  return response.data.data;
};

/**
 * Fetch agent usage rankings.
 *
 * Returns agents sorted by execution count descending. Useful for
 * identifying most active agents, popular configurations, and usage patterns.
 *
 * @param {string} startDate - Start date in ISO 8601 format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO 8601 format (YYYY-MM-DD)
 * @param {number} [limit=10] - Maximum number of rankings to return
 * @returns {Promise<AgentUsageRanking[]>} Agent rankings with execution counts
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * // Get top 10 most active agents
 * const rankings = await getAgentUsageRankings(
 *   '2025-10-01',
 *   '2025-10-31'
 * );
 * rankings.forEach(r => console.log(`${r.agent_name}: ${r.execution_count} runs`));
 */
export const getAgentUsageRankings = async (
  startDate: string,
  endDate: string,
  limit: number = 10
): Promise<AgentUsageRanking[]> => {
  const response = await apiClient.get<{ rankings: AgentUsageRanking[] }>(
    '/analytics/agents/usage',
    {
      params: {
        start_date: startDate,
        end_date: endDate,
        limit,
      },
    }
  );
  return response.data.rankings;
};

/**
 * Fetch token usage breakdown with flexible grouping.
 *
 * Returns aggregated token usage (prompt, completion, total) grouped
 * by agent, model, or day. Essential for cost tracking and optimization.
 *
 * @param {string} startDate - Start date in ISO 8601 format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO 8601 format (YYYY-MM-DD)
 * @param {'agent' | 'model' | 'day'} groupBy - Grouping dimension
 * @returns {Promise<TokenBreakdown>} Token usage breakdown with costs
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * // Group token usage by agent to find expensive agents
 * const breakdown = await getTokenUsageBreakdown(
 *   '2025-10-01',
 *   '2025-10-31',
 *   'agent'
 * );
 *
 * @example
 * // Group by day to see daily cost trends
 * const dailyUsage = await getTokenUsageBreakdown(
 *   '2025-11-01',
 *   '2025-11-10',
 *   'day'
 * );
 */
export const getTokenUsageBreakdown = async (
  startDate: string,
  endDate: string,
  groupBy: 'agent' | 'model' | 'day'
): Promise<TokenBreakdown> => {
  const response = await apiClient.get<TokenBreakdown>(
    '/analytics/token-usage/breakdown',
    {
      params: {
        start_date: startDate,
        end_date: endDate,
        group_by: groupBy,
      },
    }
  );
  return response.data;
};

/**
 * Fetch error analysis with failure patterns.
 *
 * Returns most common errors grouped by error message with occurrence
 * counts. Useful for debugging, identifying systemic issues, and
 * prioritizing fixes.
 *
 * @param {string} startDate - Start date in ISO 8601 format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO 8601 format (YYYY-MM-DD)
 * @param {number} [limit=20] - Maximum number of error types to return
 * @returns {Promise<ErrorAnalysisItem[]>} Error patterns with counts
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * // Identify top error patterns for last week
 * const errors = await getErrorAnalysis(
 *   '2025-11-03',
 *   '2025-11-10',
 *   10
 * );
 * errors.forEach(e => console.log(`${e.error_message}: ${e.count} occurrences`));
 */
export const getErrorAnalysis = async (
  startDate: string,
  endDate: string,
  limit: number = 20
): Promise<ErrorAnalysisItem[]> => {
  const response = await apiClient.get<{ errors: ErrorAnalysisItem[] }>(
    '/analytics/error-analysis',
    {
      params: {
        start_date: startDate,
        end_date: endDate,
        limit,
      },
    }
  );
  return response.data.errors;
};

/**
 * Fetch performance metrics for a specific agent.
 *
 * Returns detailed performance data including execution counts,
 * success/failure rates, average execution time, and token usage.
 * Essential for agent optimization and benchmarking.
 *
 * @param {number} agentId - Agent ID to analyze
 * @param {string} startDate - Start date in ISO 8601 format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO 8601 format (YYYY-MM-DD)
 * @returns {Promise<AgentPerformance>} Comprehensive agent performance metrics
 * @throws {AxiosError} 404 if agent not found, 401 if not authenticated
 *
 * @example
 * const performance = await getAgentPerformance(
 *   123,
 *   '2025-10-01',
 *   '2025-10-31'
 * );
 * console.log(`Success rate: ${performance.success_rate}%`);
 * console.log(`Avg execution time: ${performance.avg_execution_time}s`);
 */
export const getAgentPerformance = async (
  agentId: number,
  startDate: string,
  endDate: string
): Promise<AgentPerformance> => {
  const response = await apiClient.get<AgentPerformance>(
    `/analytics/performance/agents/${agentId}`,
    {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    }
  );
  return response.data;
};

/**
 * Fetch system-wide performance metrics.
 *
 * Returns overall system health including database pool status,
 * Redis cache stats, API response times, and resource utilization.
 * No date range required - returns current system state.
 *
 * @returns {Promise<SystemPerformance>} Real-time system performance data
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * const systemPerf = await getSystemPerformance();
 * console.log(`DB Pool: ${systemPerf.db_pool_size}/${systemPerf.db_pool_max}`);
 * console.log(`API P95 latency: ${systemPerf.api_p95_latency}ms`);
 */
export const getSystemPerformance = async (): Promise<SystemPerformance> => {
  const response = await apiClient.get<SystemPerformance>(
    '/analytics/performance/system'
  );
  return response.data;
};

/**
 * Fetch AI-generated cost optimization recommendations.
 *
 * Analyzes usage patterns and identifies opportunities to reduce costs
 * such as switching models, reducing temperature, or optimizing prompts.
 * Includes estimated savings for each recommendation.
 *
 * @param {string} startDate - Start date in ISO 8601 format (YYYY-MM-DD)
 * @param {string} endDate - End date in ISO 8601 format (YYYY-MM-DD)
 * @returns {Promise<CostRecommendations>} List of cost optimization recommendations
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * const recommendations = await getCostRecommendations(
 *   '2025-10-01',
 *   '2025-10-31'
 * );
 * recommendations.items.forEach(r => {
 *   console.log(`${r.recommendation} - Save: $${r.estimated_savings}`);
 * });
 */
export const getCostRecommendations = async (
  startDate: string,
  endDate: string
): Promise<CostRecommendations> => {
  const response = await apiClient.get<CostRecommendations>(
    '/analytics/cost/recommendations',
    {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    }
  );
  return response.data;
};

/**
 * Fetch cost projections based on current usage trends.
 *
 * Analyzes historical spending patterns and forecasts future costs.
 * Useful for budgeting, capacity planning, and cost control.
 *
 * @param {number} [projectionDays=30] - Number of days to project into the future
 * @returns {Promise<CostProjections>} Projected costs with confidence intervals
 * @throws {AxiosError} 401 if not authenticated
 *
 * @example
 * // Project costs for next 30 days
 * const projections = await getCostProjections(30);
 * console.log(`Projected monthly cost: $${projections.projected_total}`);
 *
 * @example
 * // Project costs for next quarter
 * const quarterlyProjection = await getCostProjections(90);
 */
export const getCostProjections = async (
  projectionDays: number = 30
): Promise<CostProjections> => {
  const response = await apiClient.get<CostProjections>(
    '/analytics/cost/projections',
    {
      params: {
        projection_days: projectionDays,
      },
    }
  );
  return response.data;
};
