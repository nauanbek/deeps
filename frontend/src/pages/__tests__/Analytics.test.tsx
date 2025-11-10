import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Analytics from '../Analytics';

// Mock the analytics hooks
jest.mock('../../hooks/useAnalytics', () => ({
  useExecutionTimeSeries: jest.fn(() => ({
    data: [],
    isLoading: false,
    error: null,
  })),
  useAgentUsageRankings: jest.fn(() => ({
    data: [],
    isLoading: false,
    error: null,
  })),
  useTokenUsageBreakdown: jest.fn(() => ({
    data: { total_tokens: 0, total_cost: 0, breakdown: [] },
    isLoading: false,
    error: null,
  })),
  useErrorAnalysis: jest.fn(() => ({
    data: [],
    isLoading: false,
    error: null,
  })),
  useSystemPerformance: jest.fn(() => ({
    data: {
      uptime_seconds: 86400,
      total_agents: 10,
      active_agents: 5,
      total_executions: 1000,
      executions_last_24h: 100,
      success_rate_last_24h: 0.95,
      avg_response_time_ms: 200,
      database_size_mb: 512,
      cache_hit_rate: 0.8,
    },
    isLoading: false,
    error: null,
  })),
  useCostRecommendations: jest.fn(() => ({
    data: { total_cost: 100, potential_savings: 20, recommendations: [] },
    isLoading: false,
    error: null,
  })),
  useCostProjections: jest.fn(() => ({
    data: {
      current_daily_cost: 10,
      projected_monthly_cost: 300,
      trend: 'stable',
      trend_percentage: 0,
      breakdown_by_agent: [],
    },
    isLoading: false,
    error: null,
  })),
}));

describe('Analytics Page', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  const renderWithClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
    );
  };

  it('renders all tabs', () => {
    renderWithClient(<Analytics />);
    expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /performance/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /costs/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /errors/i })).toBeInTheDocument();
  });

  it('switches between tabs', () => {
    renderWithClient(<Analytics />);

    const performanceTab = screen.getByRole('tab', { name: /performance/i });
    fireEvent.click(performanceTab);

    expect(performanceTab).toHaveAttribute('aria-selected', 'true');
  });

  it('renders date range picker', () => {
    renderWithClient(<Analytics />);
    expect(screen.getByLabelText(/date range/i)).toBeInTheDocument();
  });

  it('renders overview tab content by default', () => {
    renderWithClient(<Analytics />);
    // Check that we're on the overview tab
    const overviewTab = screen.getByRole('tab', { name: /overview/i });
    expect(overviewTab).toHaveAttribute('aria-selected', 'true');
  });

  it('renders performance tab content when selected', () => {
    renderWithClient(<Analytics />);

    const performanceTab = screen.getByRole('tab', { name: /performance/i });
    fireEvent.click(performanceTab);

    // Check that we have the group by selector
    expect(screen.getByLabelText(/group token usage by/i)).toBeInTheDocument();
  });

  it('renders costs tab content when selected', () => {
    renderWithClient(<Analytics />);

    const costsTab = screen.getByRole('tab', { name: /costs/i });
    fireEvent.click(costsTab);

    // Check that costs tab is selected
    expect(costsTab).toHaveAttribute('aria-selected', 'true');
  });

  it('renders errors tab content when selected', () => {
    renderWithClient(<Analytics />);

    const errorsTab = screen.getByRole('tab', { name: /errors/i });
    fireEvent.click(errorsTab);

    // Check that errors tab is selected
    expect(errorsTab).toHaveAttribute('aria-selected', 'true');
  });
});
