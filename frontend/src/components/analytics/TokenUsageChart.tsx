import React, { Suspense, lazy } from 'react';
import { ComponentLoadingFallback } from '../common/LoadingFallback';
import { TokenBreakdown } from '../../types/analytics';

// Lazy load Recharts components (heavy dependency)
const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })));
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })));
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })));
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })));
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })));
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })));
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })));
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })));

interface TokenUsageChartProps {
  data: TokenBreakdown;
  groupBy: 'agent' | 'model' | 'day';
  isLoading?: boolean;
  error?: Error | null;
}

const TokenUsageChart: React.FC<TokenUsageChartProps> = ({
  data,
  groupBy,
  isLoading = false,
  error = null,
}) => {
  const groupByLabel = groupBy.charAt(0).toUpperCase() + groupBy.slice(1);

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Token Usage by {groupByLabel}
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-gray-500">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Token Usage by {groupByLabel}
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-red-500">Error loading chart data: {error.message}</div>
        </div>
      </div>
    );
  }

  if (!data || !data.breakdown || data.breakdown.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Token Usage by {groupByLabel}
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-gray-500">
            No token usage data available for the selected period
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Token Usage by {groupByLabel}
        </h3>
        <div className="text-sm text-gray-600">
          <span className="font-semibold">{data.total_tokens.toLocaleString()}</span> tokens •{' '}
          <span className="font-semibold">${data.total_cost.toFixed(2)}</span>
        </div>
      </div>
      <Suspense fallback={<ComponentLoadingFallback />}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.breakdown}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="group_key"
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '0.375rem',
                color: '#f9fafb',
              }}
            />
            <Legend />
            <Bar
              dataKey="prompt_tokens"
              stackId="tokens"
              fill="#3b82f6"
              name="Prompt Tokens"
            />
            <Bar
              dataKey="completion_tokens"
              stackId="tokens"
              fill="#8b5cf6"
              name="Completion Tokens"
            />
          </BarChart>
        </ResponsiveContainer>
      </Suspense>
    </div>
  );
};

export default TokenUsageChart;
