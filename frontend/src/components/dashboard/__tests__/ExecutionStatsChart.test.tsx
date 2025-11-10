import { render, screen } from '@testing-library/react';
import { ExecutionStatsChart } from '../ExecutionStatsChart';
import type { ExecutionStats } from '../../../types/monitoring';

describe('ExecutionStatsChart', () => {
  const mockStats: ExecutionStats = {
    by_status: {
      pending: 5,
      running: 2,
      completed: 120,
      failed: 8,
      cancelled: 1,
    },
    period_days: 7,
  };

  it('renders chart title', () => {
    render(<ExecutionStatsChart stats={mockStats} />);

    expect(screen.getByText('Execution Statistics')).toBeInTheDocument();
  });

  it('renders component successfully with data', () => {
    const { container } = render(<ExecutionStatsChart stats={mockStats} />);

    expect(screen.getByText('Execution Statistics')).toBeInTheDocument();
    expect(container.querySelector('.bg-white')).toBeInTheDocument();
  });

  it('handles zero values gracefully', () => {
    const statsWithZeros: ExecutionStats = {
      by_status: {
        pending: 0,
        running: 0,
        completed: 100,
        failed: 0,
        cancelled: 0,
      },
      period_days: 7,
    };

    render(<ExecutionStatsChart stats={statsWithZeros} />);

    expect(screen.getByText('Execution Statistics')).toBeInTheDocument();
  });

  it('handles all zero values and shows empty state', () => {
    const allZeroStats: ExecutionStats = {
      by_status: {
        pending: 0,
        running: 0,
        completed: 0,
        failed: 0,
        cancelled: 0,
      },
      period_days: 7,
    };

    render(<ExecutionStatsChart stats={allZeroStats} />);

    expect(screen.getByText('Execution Statistics')).toBeInTheDocument();
    expect(screen.getByText('No execution data available')).toBeInTheDocument();
  });

  it('applies correct styling to container', () => {
    const { container } = render(<ExecutionStatsChart stats={mockStats} />);

    const chartContainer = container.querySelector('.bg-white.rounded-lg.p-6.shadow');
    expect(chartContainer).toBeInTheDocument();
  });
});
