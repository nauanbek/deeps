import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TokenUsageChart from '../TokenUsageChart';
import { TokenBreakdown } from '../../../types/analytics';

describe('TokenUsageChart', () => {
  const mockData: TokenBreakdown = {
    total_tokens: 15000,
    total_cost: 0.75,
    breakdown: [
      {
        group_key: 'Agent 1',
        prompt_tokens: 3000,
        completion_tokens: 2000,
        total_tokens: 5000,
        estimated_cost: 0.25,
      },
      {
        group_key: 'Agent 2',
        prompt_tokens: 6000,
        completion_tokens: 4000,
        total_tokens: 10000,
        estimated_cost: 0.50,
      },
    ],
  };

  it('renders chart with data', () => {
    render(<TokenUsageChart data={mockData} groupBy="agent" />);
    expect(screen.getByText(/token usage/i)).toBeInTheDocument();
  });

  it('handles empty breakdown', () => {
    const emptyData: TokenBreakdown = {
      total_tokens: 0,
      total_cost: 0,
      breakdown: [],
    };
    render(<TokenUsageChart data={emptyData} groupBy="agent" />);
    expect(screen.getByText(/no token usage/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<TokenUsageChart data={mockData} groupBy="agent" isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    const emptyData: TokenBreakdown = {
      total_tokens: 0,
      total_cost: 0,
      breakdown: [],
    };
    render(<TokenUsageChart data={emptyData} groupBy="agent" error={new Error('Failed')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });

  it('displays total tokens and cost', () => {
    render(<TokenUsageChart data={mockData} groupBy="agent" />);
    expect(screen.getByText(/15,000/)).toBeInTheDocument();
    expect(screen.getByText(/\$0\.75/)).toBeInTheDocument();
  });

  it('renders chart container with data', () => {
    const { container } = render(<TokenUsageChart data={mockData} groupBy="agent" />);
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy();
  });

  it('displays groupBy label correctly', () => {
    render(<TokenUsageChart data={mockData} groupBy="model" />);
    expect(screen.getByText(/token usage by model/i)).toBeInTheDocument();
  });
});
