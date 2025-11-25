import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  BoltIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import { PageLayout, PageHeader } from '../components/common/PageLayout';
import { Card } from '../components/common/Card';
import { Tabs, TabPanel } from '../components/common/Tabs';
import { Select } from '../components/common/Select';
import { Badge } from '../components/common/Badge';
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

const tokenGroupByOptions = [
  { value: 'agent', label: 'Agent' },
  { value: 'model', label: 'Model' },
  { value: 'day', label: 'Day' },
];

const Analytics: React.FC = () => {
  const navigate = useNavigate();
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
    {
      id: 'overview' as const,
      label: 'Overview',
      icon: <ChartBarIcon className="w-4 h-4" />,
    },
    {
      id: 'performance' as const,
      label: 'Performance',
      icon: <BoltIcon className="w-4 h-4" />,
    },
    {
      id: 'costs' as const,
      label: 'Costs',
      icon: <CurrencyDollarIcon className="w-4 h-4" />,
    },
    {
      id: 'errors' as const,
      label: 'Errors',
      icon: <ExclamationTriangleIcon className="w-4 h-4" />,
      badge: errorAnalysisQuery.data?.length || 0,
    },
  ];

  return (
    <PageErrorBoundary>
      <PageLayout>
        {/* Header */}
        <PageHeader
          title="Analytics"
          subtitle="Comprehensive analytics and insights for your AI agents"
          action={
            <div className="flex items-center gap-3">
              <Badge variant="neutral" className="hidden sm:flex items-center gap-1.5">
                <CalendarIcon className="w-4 h-4" />
                Last 7 days
              </Badge>
              <DateRangePicker
                onRangeChange={handleDateRangeChange}
                defaultRange="last7days"
              />
            </div>
          }
        />

        {/* Tabs */}
        <div className="mb-6">
          <Tabs
            tabs={tabs.map(tab => ({
              id: tab.id,
              label: (
                <span className="flex items-center gap-2">
                  {tab.icon}
                  {tab.label}
                  {tab.badge !== undefined && tab.badge > 0 && (
                    <Badge variant="error" size="sm">{tab.badge}</Badge>
                  )}
                </span>
              ),
            }))}
            activeTab={activeTab}
            onChange={(id) => setActiveTab(id as TabType)}
            variant="pills"
          />
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
                onAgentClick={(agentId) => navigate(`/agents/${agentId}`)}
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

              <Card className="p-4">
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-surface-700">
                      Group token usage by:
                    </span>
                    <Select
                      value={tokenGroupBy}
                      onChange={(e) => setTokenGroupBy(e.target.value as 'agent' | 'model' | 'day')}
                      options={tokenGroupByOptions}
                      className="w-32"
                    />
                  </div>
                </div>
              </Card>

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
                onAgentClick={(agentId) => navigate(`/agents/${agentId}`)}
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
                onAgentClick={(agentId) => navigate(`/agents/${agentId}`)}
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
      </PageLayout>
    </PageErrorBoundary>
  );
};

export default Analytics;
