import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import CostRecommendationsCard from '../CostRecommendationsCard';
import { CostRecommendations } from '../../../types/analytics';

describe('CostRecommendationsCard', () => {
  const mockData: CostRecommendations = {
    total_cost: 500.00,
    potential_savings: 75.50,
    recommendations: [
      {
        type: 'model_downgrade',
        description: 'Consider using GPT-3.5 instead of GPT-4 for simple tasks',
        agent_id: 1,
        estimated_savings: 45.00,
        impact: 'high',
      },
      {
        type: 'caching',
        description: 'Enable response caching for repeated queries',
        agent_id: null,
        estimated_savings: 30.50,
        impact: 'medium',
      },
    ],
  };

  it('renders recommendations', () => {
    render(<CostRecommendationsCard data={mockData} />);
    expect(screen.getByText(/Consider using GPT-3\.5/)).toBeInTheDocument();
    expect(screen.getByText(/Enable response caching/)).toBeInTheDocument();
  });

  it('shows savings', () => {
    render(<CostRecommendationsCard data={mockData} />);
    expect(screen.getByText(/\$75\.50/)).toBeInTheDocument();
    expect(screen.getByText(/Save \$45\.00\/mo/)).toBeInTheDocument();
  });

  it('color codes impact levels', () => {
    const { container } = render(<CostRecommendationsCard data={mockData} />);
    const highImpact = container.querySelector('.bg-red-100');
    expect(highImpact).toBeInTheDocument();
  });

  it('handles empty state (no recommendations)', () => {
    const emptyData = { ...mockData, recommendations: [] };
    render(<CostRecommendationsCard data={emptyData} />);
    expect(screen.getByText(/no cost optimization/i)).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<CostRecommendationsCard data={mockData} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles error state', () => {
    render(<CostRecommendationsCard data={mockData} error={new Error('Failed')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });
});
