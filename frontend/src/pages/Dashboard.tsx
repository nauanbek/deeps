import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CpuChipIcon,
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { Loading } from '../components/common/Loading';
import { MetricCard } from '../components/dashboard/MetricCard';
import { AgentHealthList } from '../components/dashboard/AgentHealthList';
import { ExecutionStatsChart } from '../components/dashboard/ExecutionStatsChart';
import { TokenUsageChart } from '../components/dashboard/TokenUsageChart';
import { RecentActivityFeed } from '../components/dashboard/RecentActivityFeed';
import DateRangePicker from '../components/common/DateRangePicker';
import ExecutionTrendsChart from '../components/analytics/ExecutionTrendsChart';
import AgentRankingsTable from '../components/analytics/AgentRankingsTable';
import CostProjectionsCard from '../components/analytics/CostProjectionsCard';
import SystemHealthCard from '../components/analytics/SystemHealthCard';
import PageErrorBoundary from '../components/common/PageErrorBoundary';
import WidgetErrorBoundary from '../components/common/WidgetErrorBoundary';
import {
  useDashboardOverview,
  useAgentHealth,
  useExecutionStats,
  useTokenUsage,
  useRecentExecutions,
} from '../hooks/useMonitoring';
import {
  useExecutionTimeSeries,
  useAgentUsageRankings,
  useCostProjections,
  useSystemPerformance,
} from '../hooks/useAnalytics';
import { subDays } from 'date-fns';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [startDate, setStartDate] = useState(subDays(new Date(), 7).toISOString());
  const [endDate, setEndDate] = useState(new Date().toISOString());

  const { data: overview, isLoading: overviewLoading } = useDashboardOverview();
  const { data: agentHealth, isLoading: healthLoading } = useAgentHealth();
  const { data: executionStats, isLoading: statsLoading } = useExecutionStats(7);
  const { data: tokenUsage, isLoading: tokenLoading } = useTokenUsage(30);
  const { data: recentExecutions, isLoading: executionsLoading } = useRecentExecutions(10);

  // Enhanced analytics data
  const timeSeriesQuery = useExecutionTimeSeries(startDate, endDate, 'day');
  const agentRankingsQuery = useAgentUsageRankings(startDate, endDate, 5);
  const costProjectionsQuery = useCostProjections(30);
  const systemPerformanceQuery = useSystemPerformance();

  const handleDateRangeChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  if (overviewLoading) {
    return <Loading text="Loading dashboard..." />;
  }

  return (
    <PageErrorBoundary>
      <main className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">Overview of your AI agents and executions</p>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <WidgetErrorBoundary widgetName="Total Agents">
            <MetricCard
              title="Total Agents"
              value={overview?.total_agents || 0}
              subtitle={overview?.active_agents ? `${overview.active_agents} active` : undefined}
              icon={<CpuChipIcon className="w-6 h-6 text-primary-600" />}
              onClick={() => navigate('/agents')}
            />
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Total Executions">
            <MetricCard
              title="Total Executions"
              value={overview?.total_executions || 0}
              subtitle={`${overview?.executions_today || 0} today`}
              icon={<PlayIcon className="w-6 h-6 text-blue-600" />}
              onClick={() => navigate('/executions')}
            />
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Success Rate">
            <MetricCard
              title="Success Rate"
              value={`${overview?.success_rate?.toFixed(1) || 0}%`}
              icon={<CheckCircleIcon className="w-6 h-6 text-green-600" />}
            />
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Avg Execution Time">
            <MetricCard
              title="Avg Execution Time"
              value={`${overview?.avg_execution_time?.toFixed(1) || 0}s`}
              icon={<ClockIcon className="w-6 h-6 text-yellow-600" />}
            />
          </WidgetErrorBoundary>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <WidgetErrorBoundary widgetName="Execution Statistics">
            {statsLoading ? (
              <div className="bg-white rounded-lg p-6 shadow">
                <Loading text="Loading statistics..." />
              </div>
            ) : executionStats ? (
              <ExecutionStatsChart stats={executionStats} />
            ) : null}
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Token Usage">
            {tokenLoading ? (
              <div className="bg-white rounded-lg p-6 shadow">
                <Loading text="Loading token usage..." />
              </div>
            ) : tokenUsage ? (
              <TokenUsageChart usage={tokenUsage} />
            ) : null}
          </WidgetErrorBoundary>
        </div>

        {/* Agent Health and Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h2 className="text-xl font-semibold mb-4 text-gray-900">Agent Health</h2>
            <WidgetErrorBoundary widgetName="Agent Health">
              {healthLoading ? (
                <Loading text="Loading agent health..." />
              ) : agentHealth && agentHealth.length > 0 ? (
                <AgentHealthList agents={agentHealth} />
              ) : (
                <div className="bg-white rounded-lg p-6 shadow text-center text-gray-500">
                  <p>No agent health data available</p>
                </div>
              )}
            </WidgetErrorBoundary>
          </div>

          <div>
            <WidgetErrorBoundary widgetName="Recent Activity">
              {executionsLoading ? (
                <div className="bg-white rounded-lg p-6 shadow">
                  <Loading text="Loading recent activity..." />
                </div>
              ) : recentExecutions ? (
                <RecentActivityFeed executions={recentExecutions} />
              ) : null}
            </WidgetErrorBoundary>
          </div>
        </div>

      {/* Advanced Analytics Section */}
      <div className="mt-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">Advanced Analytics</h2>
          <button
            onClick={() => navigate('/analytics')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Full Analytics
          </button>
        </div>

        {/* Date Range Filter */}
        <div className="mb-6">
          <DateRangePicker onRangeChange={handleDateRangeChange} defaultRange="last7days" />
        </div>

          {/* System Health and Cost Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {systemPerformanceQuery.data && (
              <WidgetErrorBoundary widgetName="System Health">
                <SystemHealthCard
                  data={systemPerformanceQuery.data}
                  isLoading={systemPerformanceQuery.isLoading}
                  error={systemPerformanceQuery.error}
                />
              </WidgetErrorBoundary>
            )}
            {costProjectionsQuery.data && (
              <WidgetErrorBoundary widgetName="Cost Projections">
                <CostProjectionsCard
                  data={costProjectionsQuery.data}
                  isLoading={costProjectionsQuery.isLoading}
                  error={costProjectionsQuery.error}
                />
              </WidgetErrorBoundary>
            )}
          </div>

          {/* Execution Trends */}
          <div className="mb-6">
            <WidgetErrorBoundary widgetName="Execution Trends">
              <ExecutionTrendsChart
                data={timeSeriesQuery.data || []}
                isLoading={timeSeriesQuery.isLoading}
                error={timeSeriesQuery.error}
              />
            </WidgetErrorBoundary>
          </div>

          {/* Top Agents */}
          <div>
            <WidgetErrorBoundary widgetName="Agent Rankings">
              <AgentRankingsTable
                data={agentRankingsQuery.data || []}
                isLoading={agentRankingsQuery.isLoading}
                error={agentRankingsQuery.error}
                onAgentClick={(agentId) => navigate(`/agents/${agentId}`)}
              />
            </WidgetErrorBoundary>
          </div>
        </div>
      </main>
    </PageErrorBoundary>
  );
};

export default Dashboard;
