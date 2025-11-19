import React, { Suspense, lazy } from 'react';
import { ComponentLoadingFallback } from '../common/LoadingFallback';
import type { ExecutionStats } from '../../types/monitoring';

// Lazy load Recharts components (heavy dependency)
const PieChart = lazy(() => import('recharts').then(m => ({ default: m.PieChart })));
const Pie = lazy(() => import('recharts').then(m => ({ default: m.Pie })));
const Cell = lazy(() => import('recharts').then(m => ({ default: m.Cell })));
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })));
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })));
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })));

export interface ExecutionStatsChartProps {
  stats: ExecutionStats;
}

const STATUS_COLORS: Record<string, string> = {
  completed: '#10b981',
  failed: '#ef4444',
  running: '#3b82f6',
  pending: '#6b7280',
  cancelled: '#f59e0b',
};

export const ExecutionStatsChart: React.FC<ExecutionStatsChartProps> = ({ stats }) => {
  const data = Object.entries(stats.by_status).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    originalName: name,
  }));

  const totalExecutions = data.reduce((sum, item) => sum + item.value, 0);

  if (totalExecutions === 0) {
    return (
      <div className="bg-white rounded-lg p-6 shadow">
        <h3 className="text-lg font-semibold mb-4">Execution Statistics</h3>
        <div className="text-center py-12 text-gray-500">
          <p>No execution data available</p>
        </div>
      </div>
    );
  }

  const chartDescription = data
    .map((item) => `${item.name}: ${item.value} (${((item.value / totalExecutions) * 100).toFixed(0)}%)`)
    .join(', ');

  return (
    <div className="bg-white rounded-lg p-6 shadow">
      <h3 className="text-lg font-semibold mb-4">Execution Statistics</h3>
      <Suspense fallback={<ComponentLoadingFallback />}>
        <div
          role="img"
          aria-label={`Pie chart showing execution statistics: ${chartDescription}`}
        >
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(props: { percent?: number; name?: string }) => {
                const percent = props.percent || 0;
                return percent > 0 ? `${props.name}: ${(percent * 100).toFixed(0)}%` : '';
              }}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={STATUS_COLORS[entry.originalName.toLowerCase()]}
                />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
        </div>
      </Suspense>
    </div>
  );
};

export default ExecutionStatsChart;
