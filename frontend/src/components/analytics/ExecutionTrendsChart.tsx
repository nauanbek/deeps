import React, { Suspense, lazy } from 'react';
import { ComponentLoadingFallback } from '../common/LoadingFallback';
import { format } from 'date-fns';
import { TimeSeriesDataPoint } from '../../types/analytics';

// Lazy load Recharts components (heavy dependency)
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })));
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })));
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })));
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })));
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })));
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })));
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })));
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })));

interface ExecutionTrendsChartProps {
  data: TimeSeriesDataPoint[];
  isLoading?: boolean;
  error?: Error | null;
}

const ExecutionTrendsChart: React.FC<ExecutionTrendsChartProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Execution Trends
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
          Execution Trends
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-red-500">Error loading chart data: {error.message}</div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Execution Trends
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-gray-500">
            No execution data available for the selected period
          </div>
        </div>
      </div>
    );
  }

  const chartData = data.map((point) => ({
    ...point,
    formattedTime: format(new Date(point.timestamp), 'MMM dd, HH:mm'),
  }));

  const totalExecutions = data.reduce((sum, point) => sum + point.total_executions, 0);
  const totalSuccessful = data.reduce((sum, point) => sum + point.successful, 0);
  const totalFailed = data.reduce((sum, point) => sum + point.failed, 0);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">
        Execution Trends
      </h3>
      <Suspense fallback={<ComponentLoadingFallback />}>
        <div
          role="img"
          aria-label={`Line chart showing execution trends over time. Total executions: ${totalExecutions}, Successful: ${totalSuccessful}, Failed: ${totalFailed}. Data points range from ${chartData[0]?.formattedTime} to ${chartData[chartData.length - 1]?.formattedTime}`}
        >
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="formattedTime"
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
            <Line
              type="monotone"
              dataKey="total_executions"
              stroke="#3b82f6"
              name="Total"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="successful"
              stroke="#10b981"
              name="Successful"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="failed"
              stroke="#ef4444"
              name="Failed"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
        </div>
      </Suspense>
    </div>
  );
};

export default ExecutionTrendsChart;
