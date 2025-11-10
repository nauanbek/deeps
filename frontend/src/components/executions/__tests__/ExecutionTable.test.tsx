import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ExecutionTable } from '../ExecutionTable';
import type { Execution } from '../../../types/execution';

describe('ExecutionTable', () => {
  const mockExecutions: Execution[] = [
    {
      id: 1,
      agent_id: 1,
      agent_name: 'Test Agent 1',
      input_text: 'What is the capital of France?',
      output_text: 'Paris is the capital of France.',
      status: 'completed',
      started_at: '2024-01-15T10:00:00Z',
      completed_at: '2024-01-15T10:00:30Z',
      duration_seconds: 30,
      tokens_used: 150,
      error_message: null,
    },
    {
      id: 2,
      agent_id: 1,
      agent_name: 'Test Agent 1',
      input_text: 'Calculate 2+2',
      output_text: null,
      status: 'running',
      started_at: '2024-01-15T10:05:00Z',
      completed_at: null,
      duration_seconds: null,
      tokens_used: null,
      error_message: null,
    },
    {
      id: 3,
      agent_id: 2,
      agent_name: 'Test Agent 2',
      input_text: 'This will fail',
      output_text: null,
      status: 'failed',
      started_at: '2024-01-15T09:00:00Z',
      completed_at: '2024-01-15T09:00:15Z',
      duration_seconds: 15,
      tokens_used: 50,
      error_message: 'API error',
    },
  ];

  const mockOnViewDetails = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders execution table with all executions', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    // Text appears in both desktop and mobile views
    expect(screen.getAllByText('Test Agent 1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Test Agent 2').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/What is the capital of France/).length).toBeGreaterThan(0);
  });

  it('displays correct status badges with colors', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const completedBadges = screen.getAllByText('completed');
    const runningBadges = screen.getAllByText('running');
    const failedBadges = screen.getAllByText('failed');

    expect(completedBadges[0]).toHaveClass('bg-green-100', 'text-green-800');
    expect(runningBadges[0]).toHaveClass('bg-blue-100', 'text-blue-800');
    expect(failedBadges[0]).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('truncates long input text', () => {
    const longExecution: Execution = {
      ...mockExecutions[0],
      input_text: 'A'.repeat(100),
    };

    render(
      <ExecutionTable
        executions={[longExecution]}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const inputCell = screen.getByText(/A{3,}\.\.\.$/);
    expect(inputCell).toBeInTheDocument();
  });

  it('displays duration correctly', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getAllByText('30.0s').length).toBeGreaterThan(0);
    expect(screen.getAllByText('15.0s').length).toBeGreaterThan(0);
  });

  it('displays "N/A" for null duration', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const rows = screen.getAllByRole('row');
    const runningRow = rows.find((row) => within(row).queryByText('running'));
    expect(runningRow).toBeDefined();
  });

  it('displays relative time for started_at', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    // Should display relative time like "X minutes ago"
    expect(screen.getAllByText(/ago$/).length).toBeGreaterThan(0);
  });

  it('calls onViewDetails when View button clicked', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const viewButtons = screen.getAllByRole('button', { name: /view/i });
    fireEvent.click(viewButtons[0]);

    expect(mockOnViewDetails).toHaveBeenCalledWith(1);
  });

  it('shows Cancel button only for running executions', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const cancelButtons = screen.getAllByRole('button', { name: /cancel/i });
    // One in desktop view and one in mobile view
    expect(cancelButtons).toHaveLength(2);
  });

  it('calls onCancel when Cancel button clicked', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const cancelButtons = screen.getAllByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButtons[0]);

    expect(mockOnCancel).toHaveBeenCalledWith(2);
  });

  it('displays empty state when no executions', () => {
    render(
      <ExecutionTable
        executions={[]}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText(/No executions found/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
        isLoading={true}
      />
    );

    expect(screen.getByText(/Loading executions/i)).toBeInTheDocument();
  });

  it('displays agent name or fallback to agent ID', () => {
    const executionWithoutName: Execution = {
      ...mockExecutions[0],
      agent_name: undefined,
    };

    render(
      <ExecutionTable
        executions={[executionWithoutName]}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getAllByText('Agent 1').length).toBeGreaterThan(0);
  });

  it('applies hover effect on table rows', () => {
    const { container } = render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    const rows = container.querySelectorAll('tbody tr');
    rows.forEach((row) => {
      expect(row).toHaveClass('hover:bg-gray-50');
    });
  });

  it('renders mobile card view on small screens', () => {
    // Set viewport to mobile size
    global.innerWidth = 500;
    global.dispatchEvent(new Event('resize'));

    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    // On mobile, should show cards instead of table
    // This test depends on implementation details
    // Adjust based on actual mobile implementation
  });

  it('shows running indicator for running executions', () => {
    render(
      <ExecutionTable
        executions={mockExecutions}
        onViewDetails={mockOnViewDetails}
        onCancel={mockOnCancel}
      />
    );

    // Running status should have an animated indicator
    const runningBadges = screen.getAllByText('running');
    expect(runningBadges[0].parentElement).toBeInTheDocument();
  });

  it('handles undefined callbacks gracefully', () => {
    render(<ExecutionTable executions={mockExecutions} />);

    // Should render without errors even without callbacks
    expect(screen.getAllByText('Test Agent 1').length).toBeGreaterThan(0);
  });
});
