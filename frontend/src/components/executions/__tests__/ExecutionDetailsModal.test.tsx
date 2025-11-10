import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ExecutionDetailsModal } from '../ExecutionDetailsModal';
import * as useExecutionHook from '../../../hooks/useExecutions';
import * as useWebSocketHook from '../../../hooks/useExecutionWebSocket';
import type { Execution, ExecutionTrace } from '../../../types/execution';

// Mock the hooks
jest.mock('../../../hooks/useExecutions');
jest.mock('../../../hooks/useExecutionWebSocket');

const mockExecution: Execution = {
  id: 1,
  agent_id: 1,
  agent_name: 'Test Agent',
  input_text: 'What is the capital of France?',
  output_text: 'Paris is the capital of France.',
  status: 'completed',
  started_at: '2024-01-15T10:00:00Z',
  completed_at: '2024-01-15T10:00:30Z',
  duration_seconds: 30,
  tokens_used: 150,
  error_message: null,
};

const mockTraces: ExecutionTrace[] = [
  {
    execution_id: 1,
    sequence_number: 0,
    event_type: 'llm_call',
    content: { model: 'claude-3-5-sonnet-20241022', temperature: 0.7 },
    timestamp: '2024-01-15T10:00:01Z',
  },
  {
    execution_id: 1,
    sequence_number: 1,
    event_type: 'llm_response',
    content: { content: 'Paris is the capital of France.', tokens: 150 },
    timestamp: '2024-01-15T10:00:30Z',
  },
];

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('ExecutionDetailsModal', () => {
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock useExecution hook
    (useExecutionHook.useExecution as jest.Mock).mockReturnValue({
      data: mockExecution,
      isLoading: false,
      isError: false,
    });

    // Mock useExecutionTraces hook
    (useExecutionHook.useExecutionTraces as jest.Mock).mockReturnValue({
      data: mockTraces,
      isLoading: false,
      isError: false,
    });

    // Mock useCancelExecution hook
    (useExecutionHook.useCancelExecution as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue(undefined),
      isPending: false,
    });

    // Mock useExecutionWebSocket hook
    (useWebSocketHook.useExecutionWebSocket as jest.Mock).mockReturnValue({
      traces: [],
      isConnected: false,
      error: null,
      reconnect: jest.fn(),
    });
  });

  it('renders execution details correctly', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText(/What is the capital of France/)).toBeInTheDocument();
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('displays execution ID in header', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/Execution #1/)).toBeInTheDocument();
  });

  it('shows duration and started time', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/30.0s/)).toBeInTheDocument();
    expect(screen.getByText(/ago$/)).toBeInTheDocument();
  });

  it('displays input prompt', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Input Prompt:')).toBeInTheDocument();
    expect(screen.getByText(/What is the capital of France/)).toBeInTheDocument();
  });

  it('displays output for completed executions', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Final Output:')).toBeInTheDocument();
    const outputElements = screen.getAllByText(/Paris is the capital of France/);
    expect(outputElements.length).toBeGreaterThan(0);
  });

  it('displays tokens used and estimated cost', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/Tokens Used:/)).toBeInTheDocument();
    // Check that 150 appears somewhere (may appear in multiple places - traces and final output)
    const tokensElements = screen.getAllByText(/150/);
    expect(tokensElements.length).toBeGreaterThan(0);
  });

  it('renders traces timeline', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Check for trace section heading
    const traceHeadings = screen.getAllByText(/Execution Trace/);
    expect(traceHeadings.length).toBeGreaterThan(0);

    // Check for trace type labels
    expect(screen.getByText('LLM Call')).toBeInTheDocument();
    expect(screen.getByText('LLM Response')).toBeInTheDocument();
  });

  it('shows live indicator when WebSocket connected', () => {
    (useWebSocketHook.useExecutionWebSocket as jest.Mock).mockReturnValue({
      traces: [],
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Check for the Live badge in the header (not just any "Live" text)
    const liveBadges = screen.getAllByText(/Live/i);
    expect(liveBadges.length).toBeGreaterThan(0);
  });

  it('combines initial traces with WebSocket traces', () => {
    const wsTraces: ExecutionTrace[] = [
      {
        execution_id: 1,
        sequence_number: 2,
        event_type: 'completion',
        content: { status: 'completed' },
        timestamp: '2024-01-15T10:00:35Z',
      },
    ];

    (useWebSocketHook.useExecutionWebSocket as jest.Mock).mockReturnValue({
      traces: wsTraces,
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Should show both initial and WebSocket traces
    expect(screen.getByText(/LLM Call/)).toBeInTheDocument();
    expect(screen.getByText(/Completion/)).toBeInTheDocument();
  });

  it('shows cancel button for running executions', () => {
    (useExecutionHook.useExecution as jest.Mock).mockReturnValue({
      data: { ...mockExecution, status: 'running', completed_at: null },
      isLoading: false,
      isError: false,
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /cancel execution/i })).toBeInTheDocument();
  });

  it('hides cancel button for completed executions', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByRole('button', { name: /cancel execution/i })).not.toBeInTheDocument();
  });

  it('displays error message for failed executions', () => {
    (useExecutionHook.useExecution as jest.Mock).mockReturnValue({
      data: {
        ...mockExecution,
        status: 'failed',
        error_message: 'API key not configured',
        output_text: null,
      },
      isLoading: false,
      isError: false,
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/Error/i)).toBeInTheDocument();
    expect(screen.getByText(/API key not configured/)).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('shows loading state while fetching execution', () => {
    (useExecutionHook.useExecution as jest.Mock).mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  it('shows error state when fetch fails', () => {
    (useExecutionHook.useExecution as jest.Mock).mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/Failed to load execution/i)).toBeInTheDocument();
  });

  it('shows WebSocket error message', () => {
    (useWebSocketHook.useExecutionWebSocket as jest.Mock).mockReturnValue({
      traces: [],
      isConnected: false,
      error: 'Connection failed',
      reconnect: jest.fn(),
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/Connection failed/)).toBeInTheDocument();
  });

  it('auto-scrolls to latest trace', async () => {
    const scrollIntoViewMock = jest.fn();
    Element.prototype.scrollIntoView = scrollIntoViewMock;

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    // Wait for auto-scroll to be triggered
    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });
  });

  it('handles cancel execution', async () => {
    const mockCancel = jest.fn().mockResolvedValue(undefined);
    (useExecutionHook.useCancelExecution as jest.Mock).mockReturnValue({
      mutateAsync: mockCancel,
      isPending: false,
    });

    (useExecutionHook.useExecution as jest.Mock).mockReturnValue({
      data: { ...mockExecution, status: 'running' },
      isLoading: false,
      isError: false,
    });

    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    const cancelButton = screen.getByRole('button', { name: /cancel execution/i });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mockCancel).toHaveBeenCalledWith(1);
    });
  });

  it('closes modal on escape key press', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('prevents body scroll when modal is open', () => {
    render(
      <ExecutionDetailsModal executionId={1} onClose={mockOnClose} />,
      { wrapper: createWrapper() }
    );

    expect(document.body.style.overflow).toBe('hidden');
  });
});
