import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AgentRankingsTable from '../AgentRankingsTable';
import { AgentUsageRanking } from '../../../types/analytics';

describe('AgentRankingsTable', () => {
  const mockData: AgentUsageRanking[] = [
    {
      agent_id: 1,
      agent_name: 'Customer Support Bot',
      execution_count: 150,
      success_rate: 0.95,
      total_tokens: 50000,
      estimated_cost: 2.50,
      avg_duration_seconds: 12.5,
    },
    {
      agent_id: 2,
      agent_name: 'Data Analyzer',
      execution_count: 80,
      success_rate: 0.88,
      total_tokens: 30000,
      estimated_cost: 1.50,
      avg_duration_seconds: 25.3,
    },
  ];

  it('renders all columns', () => {
    render(<AgentRankingsTable data={mockData} />);
    expect(screen.getByText(/agent name/i)).toBeInTheDocument();
    expect(screen.getByText(/executions/i)).toBeInTheDocument();
    expect(screen.getByText(/success rate/i)).toBeInTheDocument();
    expect(screen.getByText(/tokens/i)).toBeInTheDocument();
    expect(screen.getByText(/cost/i)).toBeInTheDocument();
  });

  it('renders agent data', () => {
    render(<AgentRankingsTable data={mockData} />);
    expect(screen.getByText('Customer Support Bot')).toBeInTheDocument();
    expect(screen.getByText('Data Analyzer')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('95.0%')).toBeInTheDocument();
  });

  it('handles empty data', () => {
    render(<AgentRankingsTable data={[]} />);
    expect(screen.getByText(/no agent data/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<AgentRankingsTable data={mockData} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<AgentRankingsTable data={[]} error={new Error('Failed')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });

  it('calls onAgentClick when row is clicked', () => {
    const mockOnClick = jest.fn();
    render(<AgentRankingsTable data={mockData} onAgentClick={mockOnClick} />);

    const row = screen.getByText('Customer Support Bot').closest('tr');
    if (row) fireEvent.click(row);

    expect(mockOnClick).toHaveBeenCalledWith(1);
  });

  it('formats currency correctly', () => {
    render(<AgentRankingsTable data={mockData} />);
    expect(screen.getByText('$2.50')).toBeInTheDocument();
    expect(screen.getByText('$1.50')).toBeInTheDocument();
  });

  it('formats duration correctly', () => {
    render(<AgentRankingsTable data={mockData} />);
    expect(screen.getByText('12.5s')).toBeInTheDocument();
    expect(screen.getByText('25.3s')).toBeInTheDocument();
  });
});
