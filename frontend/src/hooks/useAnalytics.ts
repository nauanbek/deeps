import { useQuery, UseQueryResult } from '@tanstack/react-query';
import {
  getExecutionTimeSeries,
  getAgentUsageRankings,
  getTokenUsageBreakdown,
  getErrorAnalysis,
  getAgentPerformance,
  getSystemPerformance,
  getCostRecommendations,
  getCostProjections,
} from '../api/analytics';
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
 * Hook for fetching execution time-series analytics
 */
export const useExecutionTimeSeries = (
  startDate: string,
  endDate: string,
  interval: 'hour' | 'day' | 'week' | 'month',
  agentId?: number
): UseQueryResult<TimeSeriesDataPoint[], Error> => {
  return useQuery({
    queryKey: ['analytics', 'time-series', startDate, endDate, interval, agentId],
    queryFn: () => getExecutionTimeSeries(startDate, endDate, interval, agentId),
    staleTime: 120000, // 2 minutes
  });
};

/**
 * Hook for fetching agent usage rankings
 */
export const useAgentUsageRankings = (
  startDate: string,
  endDate: string,
  limit: number = 10
): UseQueryResult<AgentUsageRanking[], Error> => {
  return useQuery({
    queryKey: ['analytics', 'agent-usage', startDate, endDate, limit],
    queryFn: () => getAgentUsageRankings(startDate, endDate, limit),
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook for fetching token usage breakdown
 */
export const useTokenUsageBreakdown = (
  startDate: string,
  endDate: string,
  groupBy: 'agent' | 'model' | 'day'
): UseQueryResult<TokenBreakdown, Error> => {
  return useQuery({
    queryKey: ['analytics', 'token-usage', startDate, endDate, groupBy],
    queryFn: () => getTokenUsageBreakdown(startDate, endDate, groupBy),
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook for fetching error analysis
 */
export const useErrorAnalysis = (
  startDate: string,
  endDate: string,
  limit: number = 20
): UseQueryResult<ErrorAnalysisItem[], Error> => {
  return useQuery({
    queryKey: ['analytics', 'error-analysis', startDate, endDate, limit],
    queryFn: () => getErrorAnalysis(startDate, endDate, limit),
    staleTime: 300000, // 5 minutes
  });
};

/**
 * Hook for fetching agent performance metrics
 */
export const useAgentPerformance = (
  agentId: number,
  startDate: string,
  endDate: string,
  enabled: boolean = true
): UseQueryResult<AgentPerformance, Error> => {
  return useQuery({
    queryKey: ['analytics', 'agent-performance', agentId, startDate, endDate],
    queryFn: () => getAgentPerformance(agentId, startDate, endDate),
    staleTime: 60000, // 1 minute
    enabled,
  });
};

/**
 * Hook for fetching system performance metrics
 */
export const useSystemPerformance = (): UseQueryResult<SystemPerformance, Error> => {
  return useQuery({
    queryKey: ['analytics', 'system-performance'],
    queryFn: getSystemPerformance,
    staleTime: 60000, // 1 minute
    refetchInterval: 60000, // Auto-refetch every minute
  });
};

/**
 * Hook for fetching cost recommendations
 */
export const useCostRecommendations = (
  startDate: string,
  endDate: string
): UseQueryResult<CostRecommendations, Error> => {
  return useQuery({
    queryKey: ['analytics', 'cost-recommendations', startDate, endDate],
    queryFn: () => getCostRecommendations(startDate, endDate),
    staleTime: 600000, // 10 minutes
  });
};

/**
 * Hook for fetching cost projections
 */
export const useCostProjections = (
  projectionDays: number = 30
): UseQueryResult<CostProjections, Error> => {
  return useQuery({
    queryKey: ['analytics', 'cost-projections', projectionDays],
    queryFn: () => getCostProjections(projectionDays),
    staleTime: 600000, // 10 minutes
  });
};
