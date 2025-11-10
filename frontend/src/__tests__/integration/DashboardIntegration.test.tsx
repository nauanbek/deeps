import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Dashboard from '../../pages/Dashboard';
import { monitoringApi } from '../../api/monitoring';
import { agentsApi } from '../../api/agents';
import { executionsApi } from '../../api/executions';
import * as analyticsApi from '../../api/analytics';

// Mock all API modules
jest.mock('../../api/monitoring', () => ({
  monitoringApi: {
    getSystemMetrics: jest.fn(),
    getDashboardOverview: jest.fn(),
    getAgentHealth: jest.fn(),
    getExecutionStats: jest.fn(),
    getTokenUsage: jest.fn(),
    getRecentExecutions: jest.fn(),
  },
}));

jest.mock('../../api/agents', () => ({
  agentsApi: {
    getAgents: jest.fn(),
    getAgent: jest.fn(),
    createAgent: jest.fn(),
    updateAgent: jest.fn(),
    deleteAgent: jest.fn(),
  },
}));

jest.mock('../../api/executions', () => ({
  executionsApi: {
    getExecutions: jest.fn(),
    getExecution: jest.fn(),
    executeAgent: jest.fn(),
  },
}));

jest.mock('../../api/analytics', () => ({
  getExecutionTimeSeries: jest.fn(),
  getAgentUsageRankings: jest.fn(),
  getCostProjections: jest.fn(),
  getSystemPerformance: jest.fn(),
  getTokenUsageBreakdown: jest.fn(),
  getErrorAnalysis: jest.fn(),
  getAgentPerformance: jest.fn(),
  getCostRecommendations: jest.fn(),
}));

describe('Dashboard Integration Tests', () => {
  let queryClient: QueryClient;

  const mockMonitoringData = {
    total_agents: 5,
    active_agents: 4,
    total_executions: 120,
    executions_today: 15,
    success_rate: 83.3,
    total_tokens_used: 1500000,
    estimated_total_cost: 25.50,
  };

  const mockAgents = [
    {
      id: 1,
      name: 'Research Agent',
      description: 'Conducts research',
      model: 'claude-3-5-sonnet-20241022',
      provider: 'anthropic',
      status: 'active',
      last_execution: '2025-01-08T10:00:00Z',
      total_executions: 50,
      success_rate: 0.96,
    },
    {
      id: 2,
      name: 'Data Analyzer',
      description: 'Analyzes data',
      model: 'gpt-4',
      provider: 'openai',
      status: 'active',
      last_execution: '2025-01-08T09:00:00Z',
      total_executions: 30,
      success_rate: 0.90,
    },
  ];

  const mockExecutions = [
    {
      id: 1,
      agent_id: 1,
      agent_name: 'Research Agent',
      input_text: 'Research AI trends',
      output_text: 'AI trends analysis...',
      status: 'completed',
      started_at: '2025-01-08T10:00:00Z',
      completed_at: '2025-01-08T10:00:30Z',
      duration_seconds: 30,
      tokens_used: 1500,
      error_message: null,
    },
    {
      id: 2,
      agent_id: 2,
      agent_name: 'Data Analyzer',
      input_text: 'Analyze sales data',
      output_text: null,
      status: 'running',
      started_at: '2025-01-08T10:05:00Z',
      completed_at: null,
      duration_seconds: null,
      tokens_used: null,
      error_message: null,
    },
    {
      id: 3,
      agent_id: 1,
      agent_name: 'Research Agent',
      input_text: 'Research competitors',
      output_text: null,
      status: 'failed',
      started_at: '2025-01-08T09:00:00Z',
      completed_at: '2025-01-08T09:00:15Z',
      duration_seconds: 15,
      tokens_used: 0,
      error_message: 'API rate limit exceeded',
    },
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
          staleTime: 0,
        },
      },
    });

    // Reset mocks
    jest.clearAllMocks();

    // Setup default mock responses - all monitoring API functions
    (monitoringApi.getSystemMetrics as jest.Mock).mockResolvedValue(
      mockMonitoringData
    );
    (monitoringApi.getDashboardOverview as jest.Mock).mockResolvedValue(
      mockMonitoringData
    );
    (monitoringApi.getAgentHealth as jest.Mock).mockResolvedValue(
      mockAgents.map(agent => ({
        agent_id: agent.id,
        agent_name: agent.name,
        total_executions: agent.total_executions,
        success_count: Math.floor(agent.total_executions * agent.success_rate),
        error_count: Math.floor(agent.total_executions * (1 - agent.success_rate)),
        success_rate: agent.success_rate,
        avg_execution_time: 12.5,
        last_execution_at: agent.last_execution,
      }))
    );
    (monitoringApi.getExecutionStats as jest.Mock).mockResolvedValue({
      by_status: {
        completed: 100,
        failed: 15,
        running: 5,
      },
      total: 120,
    });
    (monitoringApi.getTokenUsage as jest.Mock).mockResolvedValue({
      total_tokens: 1500000,
      estimated_cost: 25.50,
    });
    (monitoringApi.getRecentExecutions as jest.Mock).mockResolvedValue(
      mockExecutions
    );
    (agentsApi.getAgents as jest.Mock).mockResolvedValue({
      data: mockAgents,
      total: mockAgents.length,
    });
    (executionsApi.getExecutions as jest.Mock).mockResolvedValue({
      data: mockExecutions,
      total: mockExecutions.length,
    });

    // Mock analytics API functions
    (analyticsApi.getExecutionTimeSeries as jest.Mock).mockResolvedValue([]);
    (analyticsApi.getAgentUsageRankings as jest.Mock).mockResolvedValue([]);
    (analyticsApi.getCostProjections as jest.Mock).mockResolvedValue({
      current_monthly_cost: 100,
      projected_monthly_cost: 120,
      confidence: 0.85,
    });
    (analyticsApi.getSystemPerformance as jest.Mock).mockResolvedValue({
      avg_response_time: 250,
      avg_execution_time: 12.5,
      success_rate: 0.95,
      total_requests: 1000,
    });
  });

  const renderDashboard = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  it('loads and displays all dashboard metrics', async () => {
    renderDashboard();

    // Wait for dashboard overview to be called and data to load
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Check that metric cards are displayed
    await waitFor(() => {
      expect(screen.getByText('Total Agents')).toBeInTheDocument();
    });
    expect(screen.getByText('5')).toBeInTheDocument();

    expect(screen.getByText('Total Executions')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
  });

  it('displays agent health information', async () => {
    renderDashboard();

    // Wait for dashboard to load
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
      expect(monitoringApi.getAgentHealth).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText('Research Agent')).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByText('Data Analyzer')).toBeInTheDocument();

    // Should show success rates
    expect(screen.getByText(/96%/)).toBeInTheDocument();
    expect(screen.getByText(/90%/)).toBeInTheDocument();
  });

  it('shows recent activity feed', async () => {
    renderDashboard();

    // Wait for API calls
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
      expect(monitoringApi.getRecentExecutions).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText(/Research AI trends/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByText(/Analyze sales data/i)).toBeInTheDocument();

    // Should show status indicators
    expect(screen.getByText('completed')).toBeInTheDocument();
    expect(screen.getByText('running')).toBeInTheDocument();
    expect(screen.getByText('failed')).toBeInTheDocument();
  });

  it('displays token usage statistics', async () => {
    renderDashboard();

    // Wait for API calls
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
      expect(monitoringApi.getTokenUsage).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText('Token Usage')).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByText(/1,500,000/)).toBeInTheDocument();

    // Should show estimated cost
    expect(screen.getByText(/\$25\.50/)).toBeInTheDocument();
  });

  it('handles loading state correctly', () => {
    // Mock API calls to never resolve
    (monitoringApi.getDashboardOverview as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    renderDashboard();

    // Should show loading indicators
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    // Mock API errors
    (monitoringApi.getDashboardOverview as jest.Mock).mockRejectedValue(
      new Error('Failed to fetch metrics')
    );

    renderDashboard();

    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
    });

    // Should handle errors (exact error display depends on implementation)
    // The dashboard should not crash
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
  });

  it('displays execution statistics chart', async () => {
    renderDashboard();

    // Wait for API calls
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
      expect(monitoringApi.getExecutionStats).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText(/Execution Statistics/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Should show successful, failed, and running executions
    expect(screen.getByText('Successful')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('refreshes data when page loads', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalledTimes(1);
      expect(monitoringApi.getAgentHealth).toHaveBeenCalledTimes(1);
      expect(monitoringApi.getRecentExecutions).toHaveBeenCalledTimes(1);
    });
  });

  it('shows empty state when no agents exist', async () => {
    (monitoringApi.getAgentHealth as jest.Mock).mockResolvedValue([]);
    (monitoringApi.getDashboardOverview as jest.Mock).mockResolvedValue({
      ...mockMonitoringData,
      total_agents: 0,
      active_agents: 0,
    });

    renderDashboard();

    // Wait for API calls
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText('Total Agents')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Should show zero agents
    const totalAgentsCard = screen.getByText('Total Agents')
      .parentElement as HTMLElement;
    expect(totalAgentsCard).toHaveTextContent('0');
  });

  it('shows empty state when no executions exist', async () => {
    (monitoringApi.getRecentExecutions as jest.Mock).mockResolvedValue([]);

    renderDashboard();

    // Wait for API calls
    await waitFor(() => {
      expect(monitoringApi.getDashboardOverview).toHaveBeenCalled();
      expect(monitoringApi.getRecentExecutions).toHaveBeenCalled();
    }, { timeout: 3000 });

    // Wait for data to render
    await waitFor(() => {
      expect(screen.getByText(/Recent Activity/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
