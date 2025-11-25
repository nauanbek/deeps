import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import {
  CpuChipIcon,
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowRightIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { Loading } from '../components/common/Loading';
import { Card, StatCard } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { PageLayout, PageHeader } from '../components/common/PageLayout';
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

  const timeSeriesQuery = useExecutionTimeSeries(startDate, endDate, 'day');
  const agentRankingsQuery = useAgentUsageRankings(startDate, endDate, 5);
  const costProjectionsQuery = useCostProjections(30);
  const systemPerformanceQuery = useSystemPerformance();

  const handleDateRangeChange = (start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  };

  if (overviewLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loading text="Loading dashboard..." />
      </div>
    );
  }

  return (
    <PageErrorBoundary>
      <PageLayout>
        {/* Header */}
        <PageHeader
          title="Dashboard"
          subtitle="Overview of your AI agents and executions"
          action={
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate('/agents')}
              rightIcon={<ArrowRightIcon className="w-4 h-4" />}
            >
              Create Agent
            </Button>
          }
        />

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <WidgetErrorBoundary widgetName="Total Agents">
            <StatCard
              label="Total Agents"
              value={overview?.total_agents || 0}
              icon={<CpuChipIcon className="w-5 h-5" />}
              variant="primary"
              change={12}
              trend="up"
              changeLabel="vs last week"
            />
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Total Executions">
            <StatCard
              label="Total Executions"
              value={overview?.total_executions || 0}
              icon={<PlayIcon className="w-5 h-5" />}
              variant="default"
              change={overview?.executions_today || 0}
              trend="up"
              changeLabel="today"
            />
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Success Rate">
            <StatCard
              label="Success Rate"
              value={`${overview?.success_rate?.toFixed(1) || 0}%`}
              icon={<CheckCircleIcon className="w-5 h-5" />}
              variant="success"
              trend={overview?.success_rate && overview.success_rate > 90 ? 'up' : 'down'}
            />
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Avg Execution Time">
            <StatCard
              label="Avg Execution Time"
              value={`${overview?.avg_execution_time?.toFixed(1) || 0}s`}
              icon={<ClockIcon className="w-5 h-5" />}
              variant="warning"
              trend="neutral"
            />
          </WidgetErrorBoundary>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <WidgetErrorBoundary widgetName="Execution Statistics">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-surface-900">Execution Statistics</h3>
                <Badge variant="neutral">Last 7 days</Badge>
              </div>
              {statsLoading ? (
                <div className="flex items-center justify-center h-64">
                  <Loading text="Loading statistics..." />
                </div>
              ) : executionStats ? (
                <ExecutionStatsChart stats={executionStats} />
              ) : (
                <div className="flex items-center justify-center h-64 text-surface-500">
                  No data available
                </div>
              )}
            </Card>
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Token Usage">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-surface-900">Token Usage</h3>
                <Badge variant="neutral">Last 30 days</Badge>
              </div>
              {tokenLoading ? (
                <div className="flex items-center justify-center h-64">
                  <Loading text="Loading token usage..." />
                </div>
              ) : tokenUsage ? (
                <TokenUsageChart usage={tokenUsage} />
              ) : (
                <div className="flex items-center justify-center h-64 text-surface-500">
                  No data available
                </div>
              )}
            </Card>
          </WidgetErrorBoundary>
        </div>

        {/* Agent Health and Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <WidgetErrorBoundary widgetName="Agent Health">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-surface-900">Agent Health</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate('/agents')}>
                  View all
                </Button>
              </div>
              {healthLoading ? (
                <div className="flex items-center justify-center h-48">
                  <Loading text="Loading agent health..." />
                </div>
              ) : agentHealth && agentHealth.length > 0 ? (
                <AgentHealthList agents={agentHealth} />
              ) : (
                <div className="flex flex-col items-center justify-center h-48 text-center">
                  <CpuChipIcon className="w-12 h-12 text-surface-300 mb-3" />
                  <p className="text-surface-500">No agents created yet</p>
                  <Button
                    variant="primary"
                    size="sm"
                    className="mt-3"
                    onClick={() => navigate('/agents')}
                  >
                    Create your first agent
                  </Button>
                </div>
              )}
            </Card>
          </WidgetErrorBoundary>

          <WidgetErrorBoundary widgetName="Recent Activity">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-surface-900">Recent Activity</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate('/executions')}>
                  View all
                </Button>
              </div>
              {executionsLoading ? (
                <div className="flex items-center justify-center h-48">
                  <Loading text="Loading recent activity..." />
                </div>
              ) : recentExecutions && recentExecutions.length > 0 ? (
                <RecentActivityFeed executions={recentExecutions} />
              ) : (
                <div className="flex flex-col items-center justify-center h-48 text-center">
                  <PlayIcon className="w-12 h-12 text-surface-300 mb-3" />
                  <p className="text-surface-500">No recent executions</p>
                </div>
              )}
            </Card>
          </WidgetErrorBoundary>
        </div>

        {/* Advanced Analytics Section */}
        <div className="border-t border-surface-200 pt-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                <ArrowTrendingUpIcon className="w-6 h-6 text-primary-600" />
                Advanced Analytics
              </h2>
              <p className="text-surface-500 mt-1">Detailed insights and trends</p>
            </div>
            <div className="flex items-center gap-3">
              <DateRangePicker onRangeChange={handleDateRangeChange} defaultRange="last7days" />
              <Button
                variant="secondary"
                size="md"
                onClick={() => navigate('/analytics')}
                leftIcon={<ChartBarIcon className="w-4 h-4" />}
              >
                Full Analytics
              </Button>
            </div>
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
          <WidgetErrorBoundary widgetName="Agent Rankings">
            <AgentRankingsTable
              data={agentRankingsQuery.data || []}
              isLoading={agentRankingsQuery.isLoading}
              error={agentRankingsQuery.error}
              onAgentClick={(agentId) => navigate(`/agents/${agentId}`)}
            />
          </WidgetErrorBoundary>
        </div>
      </PageLayout>
    </PageErrorBoundary>
  );
};

export default Dashboard;
