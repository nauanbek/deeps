import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExecutionTrendsChart from '../ExecutionTrendsChart';
import { TimeSeriesDataPoint } from '../../../types/analytics';

describe('ExecutionTrendsChart', () => {
  const mockData: TimeSeriesDataPoint[] = [
    {
      timestamp: '2024-01-01T00:00:00Z',
      total_executions: 100,
      successful: 80,
      failed: 15,
      cancelled: 5,
      avg_duration_seconds: 12.5,
      total_tokens: 5000,
      estimated_cost: 0.25,
    },
    {
      timestamp: '2024-01-02T00:00:00Z',
      total_executions: 120,
      successful: 100,
      failed: 15,
      cancelled: 5,
      avg_duration_seconds: 10.2,
      total_tokens: 6000,
      estimated_cost: 0.30,
    },
  ];

  it('renders chart with data', () => {
    render(<ExecutionTrendsChart data={mockData} />);
    expect(screen.getByText(/execution trends/i)).toBeInTheDocument();
  });

  it('handles empty data', () => {
    render(<ExecutionTrendsChart data={[]} />);
    expect(screen.getByText(/no execution data/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ExecutionTrendsChart data={mockData} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<ExecutionTrendsChart data={[]} error={new Error('Failed to fetch')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });

  it('displays chart title', () => {
    render(<ExecutionTrendsChart data={mockData} />);
    expect(screen.getByText(/execution trends/i)).toBeInTheDocument();
  });

  it('renders chart container with data', () => {
    const { container } = render(<ExecutionTrendsChart data={mockData} />);
    // Check that the component renders without error
    expect(container.querySelector('.recharts-responsive-container')).toBeTruthy();
  });
});
