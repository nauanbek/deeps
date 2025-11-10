import React from 'react';
import { CostProjections } from '../../types/analytics';

interface CostProjectionsCardProps {
  data: CostProjections;
  isLoading?: boolean;
  error?: Error | null;
}

const CostProjectionsCard: React.FC<CostProjectionsCardProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Cost Projections
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
          Cost Projections
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-red-500">Error loading cost data: {error.message}</div>
        </div>
      </div>
    );
  }

  const getTrendIcon = () => {
    switch (data.trend) {
      case 'increasing':
        return '↑';
      case 'decreasing':
        return '↓';
      case 'stable':
        return '→';
      default:
        return '';
    }
  };

  const getTrendColor = () => {
    switch (data.trend) {
      case 'increasing':
        return 'text-red-500';
      case 'decreasing':
        return 'text-green-500';
      case 'stable':
        return 'text-gray-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">
        Cost Projections
      </h3>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <p className="text-sm text-gray-600 mb-1">Current Daily Cost</p>
          <p className="text-2xl font-bold text-gray-900">
            ${data.current_daily_cost.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600 mb-1">Projected Monthly Cost</p>
          <p className="text-2xl font-bold text-gray-900">
            ${data.projected_monthly_cost.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-2">
          <p className="text-sm text-gray-600">Trend:</p>
          <span className={`text-lg font-bold ${getTrendColor()}`}>
            {getTrendIcon()} {Math.abs(data.trend_percentage).toFixed(1)}%
          </span>
          <span className="text-sm text-gray-500">
            {data.trend === 'increasing' ? 'increase' : data.trend === 'decreasing' ? 'decrease' : 'stable'}
          </span>
        </div>
      </div>

      <div>
        <p className="text-sm font-medium text-gray-700 mb-3">
          Breakdown by Agent
        </p>
        <div className="space-y-2">
          {data.breakdown_by_agent.map((agent) => (
            <div key={agent.agent_id} className="flex justify-between items-center">
              <span className="text-sm text-gray-600">
                {agent.agent_name}
              </span>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">
                  {agent.percentage_of_total.toFixed(1)}%
                </span>
                <span className="text-sm font-semibold text-gray-900">
                  ${agent.projected_cost.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CostProjectionsCard;
