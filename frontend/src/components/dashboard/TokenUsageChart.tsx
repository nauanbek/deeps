import React, { Suspense, lazy } from 'react';
import { ComponentLoadingFallback } from '../common/LoadingFallback';
import type { TokenUsageSummary } from '../../types/monitoring';

// Lazy load Recharts components (heavy dependency)
const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })));
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })));
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })));
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })));
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })));
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })));
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })));

export interface TokenUsageChartProps {
  usage: TokenUsageSummary;
}

export const TokenUsageChart: React.FC<TokenUsageChartProps> = ({ usage }) => {
  const data = [
    { name: 'Prompt', tokens: usage.prompt_tokens, fill: '#3b82f6' },
    { name: 'Completion', tokens: usage.completion_tokens, fill: '#10b981' },
  ];

  return (
    <div className="bg-white rounded-lg p-6 shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold">Token Usage</h3>
          <p className="text-sm text-gray-600">Last {usage.period_days} days</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-gray-900">
            {usage.total_tokens.toLocaleString()}
          </p>
          <p className="text-sm text-gray-600">Total tokens</p>
          <p className="text-xs text-green-600 font-medium mt-1">
            ${usage.estimated_cost.toFixed(4)} cost
          </p>
        </div>
      </div>

      <Suspense fallback={<ComponentLoadingFallback />}>
        <div
          role="img"
          aria-label={`Bar chart showing token usage over the last ${usage.period_days} days. Prompt tokens: ${usage.prompt_tokens.toLocaleString()}, Completion tokens: ${usage.completion_tokens.toLocaleString()}, Total: ${usage.total_tokens.toLocaleString()} tokens with an estimated cost of $${usage.estimated_cost.toFixed(4)}`}
        >
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="tokens" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
        </div>
      </Suspense>
    </div>
  );
};

export default TokenUsageChart;
