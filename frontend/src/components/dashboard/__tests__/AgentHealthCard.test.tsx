import { render, screen } from '@testing-library/react';
import { AgentHealthCard } from '../AgentHealthCard';
import type { AgentHealth } from '../../../types/monitoring';

describe('AgentHealthCard', () => {
  const mockHealth: AgentHealth = {
    agent_id: 1,
    agent_name: 'Customer Support Agent',
    total_executions: 45,
    success_count: 43,
    error_count: 2,
    success_rate: 95.6,
    avg_execution_time: 2.5,
    last_execution_at: '2025-01-08T10:30:00',
  };

  it('renders agent information', () => {
    render(<AgentHealthCard health={mockHealth} />);

    expect(screen.getByText('Customer Support Agent')).toBeInTheDocument();
    expect(screen.getByText('ID: 1')).toBeInTheDocument();
  });

  it('renders high success rate badge with green styling', () => {
    render(<AgentHealthCard health={mockHealth} />);

    const badge = screen.getByText('95.6% success');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('renders medium success rate badge with yellow styling', () => {
    const mediumHealth: AgentHealth = {
      ...mockHealth,
      success_rate: 65.5,
    };

    render(<AgentHealthCard health={mediumHealth} />);

    const badge = screen.getByText('65.5% success');
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('renders low success rate badge with red styling', () => {
    const lowHealth: AgentHealth = {
      ...mockHealth,
      success_rate: 35.2,
    };

    render(<AgentHealthCard health={lowHealth} />);

    const badge = screen.getByText('35.2% success');
    expect(badge).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('renders execution metrics', () => {
    render(<AgentHealthCard health={mockHealth} />);

    expect(screen.getByText('Executions')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();

    expect(screen.getByText('Avg Time')).toBeInTheDocument();
    expect(screen.getByText('2.5s')).toBeInTheDocument();
  });

  it('renders success and error counts', () => {
    render(<AgentHealthCard health={mockHealth} />);

    expect(screen.getByText('Success')).toBeInTheDocument();
    const successCount = screen.getByText('43');
    expect(successCount).toBeInTheDocument();
    expect(successCount).toHaveClass('text-green-600');

    expect(screen.getByText('Errors')).toBeInTheDocument();
    const errorCount = screen.getByText('2');
    expect(errorCount).toBeInTheDocument();
    expect(errorCount).toHaveClass('text-red-600');
  });

  it('renders last execution time when available', () => {
    render(<AgentHealthCard health={mockHealth} />);

    const lastExecution = screen.getByText(/Last run:/);
    expect(lastExecution).toBeInTheDocument();
  });

  it('does not render last execution time when null', () => {
    const healthWithoutLastExecution: AgentHealth = {
      ...mockHealth,
      last_execution_at: null,
    };

    render(<AgentHealthCard health={healthWithoutLastExecution} />);

    expect(screen.queryByText(/Last run:/)).not.toBeInTheDocument();
  });

  it('formats execution time to one decimal place', () => {
    const healthWithPreciseTime: AgentHealth = {
      ...mockHealth,
      avg_execution_time: 3.456789,
    };

    render(<AgentHealthCard health={healthWithPreciseTime} />);

    expect(screen.getByText('3.5s')).toBeInTheDocument();
  });

  it('formats success rate to one decimal place', () => {
    const healthWithPreciseRate: AgentHealth = {
      ...mockHealth,
      success_rate: 87.654321,
    };

    render(<AgentHealthCard health={healthWithPreciseRate} />);

    expect(screen.getByText('87.7% success')).toBeInTheDocument();
  });
});
