import React from 'react';
import { CostRecommendations } from '../../types/analytics';

interface CostRecommendationsCardProps {
  data: CostRecommendations;
  isLoading?: boolean;
  error?: Error | null;
}

const CostRecommendationsCard: React.FC<CostRecommendationsCardProps> = ({
  data,
  isLoading = false,
  error = null,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Cost Recommendations
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
          Cost Recommendations
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-red-500">Error loading recommendations: {error.message}</div>
        </div>
      </div>
    );
  }

  const getImpactColor = (impact: string) => {
    switch (impact.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!data.recommendations || data.recommendations.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Cost Recommendations
        </h3>
        <div className="h-64 flex items-center justify-center">
          <div className="text-green-500">
            No cost optimization recommendations at this time - You're doing great!
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4 text-gray-900">
        Cost Recommendations
      </h3>

      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-600 mb-1">Potential Monthly Savings</p>
        <p className="text-2xl font-bold text-blue-600">
          ${data.potential_savings.toFixed(2)}
        </p>
        <p className="text-xs text-gray-500 mt-1">
          from current cost of ${data.total_cost.toFixed(2)}
        </p>
      </div>

      <div className="space-y-4">
        {data.recommendations.map((rec, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg p-4"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <p className="text-sm text-gray-900 font-medium">
                  {rec.description}
                </p>
                {rec.agent_id && (
                  <p className="text-xs text-gray-500 mt-1">
                    Agent ID: {rec.agent_id}
                  </p>
                )}
              </div>
              <span
                className={`ml-3 px-2 py-1 text-xs font-semibold rounded ${getImpactColor(
                  rec.impact
                )}`}
              >
                {rec.impact.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-gray-500">
                Type: {rec.type.replace(/_/g, ' ')}
              </span>
              <span className="text-sm font-bold text-green-600">
                Save ${rec.estimated_savings.toFixed(2)}/mo
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CostRecommendationsCard;
