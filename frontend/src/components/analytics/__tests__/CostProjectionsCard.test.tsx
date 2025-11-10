import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import CostProjectionsCard from '../CostProjectionsCard';
import { CostProjections } from '../../../types/analytics';

describe('CostProjectionsCard', () => {
  const mockData: CostProjections = {
    current_daily_cost: 12.50,
    projected_monthly_cost: 375.00,
    trend: 'increasing',
    trend_percentage: 15.5,
    breakdown_by_agent: [
      {
        agent_id: 1,
        agent_name: 'Agent 1',
        projected_cost: 200.00,
        percentage_of_total: 53.3,
      },
      {
        agent_id: 2,
        agent_name: 'Agent 2',
        projected_cost: 175.00,
        percentage_of_total: 46.7,
      },
    ],
  };

  it('displays costs correctly', () => {
    render(<CostProjectionsCard data={mockData} />);
    expect(screen.getByText('$12.50')).toBeInTheDocument();
    expect(screen.getByText('$375.00')).toBeInTheDocument();
  });

  it('shows trend indicator for increasing', () => {
    render(<CostProjectionsCard data={mockData} />);
    expect(screen.getByText(/15\.5%/)).toBeInTheDocument();
    expect(screen.getByText(/↑/)).toBeInTheDocument();
  });

  it('shows trend indicator for decreasing', () => {
    const decreasingData = { ...mockData, trend: 'decreasing' as const, trend_percentage: -10 };
    render(<CostProjectionsCard data={decreasingData} />);
    expect(screen.getByText(/↓/)).toBeInTheDocument();
  });

  it('shows trend indicator for stable', () => {
    const stableData = { ...mockData, trend: 'stable' as const, trend_percentage: 0 };
    render(<CostProjectionsCard data={stableData} />);
    expect(screen.getByText(/→/)).toBeInTheDocument();
  });

  it('renders breakdown by agent', () => {
    render(<CostProjectionsCard data={mockData} />);
    expect(screen.getByText('Agent 1')).toBeInTheDocument();
    expect(screen.getByText('Agent 2')).toBeInTheDocument();
    expect(screen.getByText('$200.00')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<CostProjectionsCard data={mockData} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles error state', () => {
    render(<CostProjectionsCard data={mockData} error={new Error('Failed')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });
});
