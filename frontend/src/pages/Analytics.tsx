import React, { useState } from 'react';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import { subDays } from 'date-fns';
import DateRangePicker from '../components/common/DateRangePicker';
import ExecutionTrendsChart from '../components/analytics/ExecutionTrendsChart';
import TokenUsageChart from '../components/analytics/TokenUsageChart';
import AgentRankingsTable from '../components/analytics/AgentRankingsTable';
import CostProjectionsCard from '../components/analytics/CostProjectionsCard';
import ErrorAnalysisTable from '../components/analytics/ErrorAnalysisTable';
import SystemHealthCard from '../components/analytics/SystemHealthCard';
import CostRecommendationsCard from '../components/analytics/CostRecommendationsCard';
import {
  useExecutionTimeSeries,
  useAgentUsageRankings,
  useTokenUsageBreakdown,
  useErrorAnalysis,
  useSystemPerformance,
  useCostRecommendations,
  useCostProjections,
} from '../hooks/useAnalytics';

type TabType = 'overview' | 'performance' | 'costs' | 'errors';

const Analytics: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [startDate, setStartDate] = useState(subDays(new Date(), 7).toISOString());
  const [endDate, setEndDate] = useState(new Date().toISOString());
  const [tokenGroupBy, setTokenGroupBy] = useState<'agent' | 'model' | 'day'>('agent');

  const handleDateRangeChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  // Fetch data using hooks
  const timeSeriesQuery = useExecutionTimeSeries(startDate, endDate, 'day') || {};
  const agentRankingsQuery = useAgentUsageRankings(startDate, endDate, 10) || {};
  const tokenBreakdownQuery = useTokenUsageBreakdown(startDate, endDate, tokenGroupBy) || {};
  const errorAnalysisQuery = useErrorAnalysis(startDate, endDate, 20) || {};
  const systemPerformanceQuery = useSystemPerformance() || {};
  const costRecommendationsQuery = useCostRecommendations(startDate, endDate) || {};
  const costProjectionsQuery = useCostProjections(30) || {};

  const tabs = [
    { id: 'overview' as const, label: 'Overview' },
    { id: 'performance' as const, label: 'Performance' },
    { id: 'costs' as const, label: 'Costs' },
    { id: 'errors' as const, label: 'Errors' },
  ];

  return (
    <PageErrorBoundary>
      <main className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Analytics
        </h1>
        <p className="text-gray-600">
          Comprehensive analytics and insights for your AI agents
        </p>
      </div>

      {/* Date Range Picker */}
      <div className="mb-6">
        <DateRangePicker onRangeChange={handleDateRangeChange} defaultRange="last7days" />
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b-gray-200">
          <nav className="-mb-px flex space-x-8" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {systemPerformanceQuery.data && (
                <SystemHealthCard
                  data={systemPerformanceQuery.data}
                  isLoading={systemPerformanceQuery.isLoading}
                  error={systemPerformanceQuery.error}
                />
              )}
              {costProjectionsQuery.data && (
                <CostProjectionsCard
                  data={costProjectionsQuery.data}
                  isLoading={costProjectionsQuery.isLoading}
                  error={costProjectionsQuery.error}
                />
              )}
            </div>

            <ExecutionTrendsChart
              data={timeSeriesQuery.data || []}
              isLoading={timeSeriesQuery.isLoading}
              error={timeSeriesQuery.error}
            />

            <AgentRankingsTable
              data={agentRankingsQuery.data || []}
              isLoading={agentRankingsQuery.isLoading}
              error={agentRankingsQuery.error}
            />
          </>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <>
            <ExecutionTrendsChart
              data={timeSeriesQuery.data || []}
              isLoading={timeSeriesQuery.isLoading}
              error={timeSeriesQuery.error}
            />

            <div className="bg-white p-4 rounded-lg shadow mb-4">
              <label htmlFor="token-group-by" className="text-sm font-medium text-gray-700 mr-3">
                Group token usage by:
              </label>
              <select
                id="token-group-by"
                value={tokenGroupBy}
                onChange={(e) => setTokenGroupBy(e.target.value as 'agent' | 'model' | 'day')}
                className="px-3 py-1 border-gray-300 rounded bg-white text-gray-900"
              >
                <option value="agent">Agent</option>
                <option value="model">Model</option>
                <option value="day">Day</option>
              </select>
            </div>

            {tokenBreakdownQuery.data && (
              <TokenUsageChart
                data={tokenBreakdownQuery.data}
                groupBy={tokenGroupBy}
                isLoading={tokenBreakdownQuery.isLoading}
                error={tokenBreakdownQuery.error}
              />
            )}

            <AgentRankingsTable
              data={agentRankingsQuery.data || []}
              isLoading={agentRankingsQuery.isLoading}
              error={agentRankingsQuery.error}
            />
          </>
        )}

        {/* Costs Tab */}
        {activeTab === 'costs' && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {costProjectionsQuery.data && (
                <CostProjectionsCard
                  data={costProjectionsQuery.data}
                  isLoading={costProjectionsQuery.isLoading}
                  error={costProjectionsQuery.error}
                />
              )}
              {costRecommendationsQuery.data && (
                <CostRecommendationsCard
                  data={costRecommendationsQuery.data}
                  isLoading={costRecommendationsQuery.isLoading}
                  error={costRecommendationsQuery.error}
                />
              )}
            </div>

            {tokenBreakdownQuery.data && (
              <TokenUsageChart
                data={tokenBreakdownQuery.data}
                groupBy={tokenGroupBy}
                isLoading={tokenBreakdownQuery.isLoading}
                error={tokenBreakdownQuery.error}
              />
            )}

            <AgentRankingsTable
              data={agentRankingsQuery.data || []}
              isLoading={agentRankingsQuery.isLoading}
              error={agentRankingsQuery.error}
            />
          </>
        )}

        {/* Errors Tab */}
        {activeTab === 'errors' && (
          <>
            <ErrorAnalysisTable
              data={errorAnalysisQuery.data || []}
              isLoading={errorAnalysisQuery.isLoading}
              error={errorAnalysisQuery.error}
            />
          </>
        )}
      </div>
      </main>
    </PageErrorBoundary>
  );
};

export default Analytics;
