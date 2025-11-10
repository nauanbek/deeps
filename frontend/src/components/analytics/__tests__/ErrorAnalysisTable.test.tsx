import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorAnalysisTable from '../ErrorAnalysisTable';
import { ErrorAnalysisItem } from '../../../types/analytics';

describe('ErrorAnalysisTable', () => {
  const mockData: ErrorAnalysisItem[] = [
    {
      error_pattern: 'Connection timeout',
      count: 45,
      affected_agents: [1, 2, 3],
      first_seen: '2024-01-01T00:00:00Z',
      last_seen: '2024-01-05T10:30:00Z',
    },
    {
      error_pattern: 'Invalid API key',
      count: 12,
      affected_agents: [4],
      first_seen: '2024-01-03T00:00:00Z',
      last_seen: '2024-01-04T15:00:00Z',
    },
  ];

  it('renders error patterns', () => {
    render(<ErrorAnalysisTable data={mockData} />);
    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
    expect(screen.getByText('Invalid API key')).toBeInTheDocument();
  });

  it('displays counts and dates', () => {
    render(<ErrorAnalysisTable data={mockData} />);
    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('shows affected agents count', () => {
    render(<ErrorAnalysisTable data={mockData} />);
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('handles empty state', () => {
    render(<ErrorAnalysisTable data={[]} />);
    expect(screen.getByText(/no errors/i)).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<ErrorAnalysisTable data={mockData} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles error state', () => {
    render(<ErrorAnalysisTable data={[]} error={new Error('Failed')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });
});
