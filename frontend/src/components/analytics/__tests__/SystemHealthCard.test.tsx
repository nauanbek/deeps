import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import SystemHealthCard from '../SystemHealthCard';
import { SystemPerformance } from '../../../types/analytics';

describe('SystemHealthCard', () => {
  const mockData: SystemPerformance = {
    uptime_seconds: 8640000, // 100 days
    total_agents: 25,
    active_agents: 18,
    total_executions: 50000,
    executions_last_24h: 1500,
    success_rate_last_24h: 0.94,
    avg_response_time_ms: 250,
    database_size_mb: 1024,
    cache_hit_rate: 0.85,
  };

  it('displays all metrics', () => {
    render(<SystemHealthCard data={mockData} />);
    expect(screen.getByText(/18 \/ 25/)).toBeInTheDocument();
    expect(screen.getByText('50,000')).toBeInTheDocument();
  });

  it('formats uptime correctly', () => {
    render(<SystemHealthCard data={mockData} />);
    // Should show "100d" for 100 days
    expect(screen.getByText(/100d/)).toBeInTheDocument();
  });

  it('displays success rate indicator', () => {
    render(<SystemHealthCard data={mockData} />);
    expect(screen.getByText('94.0%')).toBeInTheDocument();
  });

  it('shows database size and cache hit rate', () => {
    render(<SystemHealthCard data={mockData} />);
    expect(screen.getByText(/1024/)).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    render(<SystemHealthCard data={mockData} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('handles error state', () => {
    render(<SystemHealthCard data={mockData} error={new Error('Failed')} />);
    expect(screen.getByText(/error loading/i)).toBeInTheDocument();
  });
});
