// Mock useNavigate before all imports
const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => {
  const RouterDOM = jest.requireActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...RouterDOM,
    useNavigate: () => mockNavigate,
  };
});

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ExecuteAgentModal } from '../ExecuteAgentModal';
import * as useExecutionsHook from '../../../hooks/useExecutions';
import type { Agent } from '../../../types/agent';

const mockAgent: Agent = {
  id: 1,
  name: 'Test Agent',
  description: 'A test agent',
  system_prompt: 'You are a helpful assistant.',
  model_provider: 'anthropic',
  model_name: 'claude-3-5-sonnet-20241022',
  temperature: 0.7,
  max_tokens: 2000,
  planning_enabled: true,
  filesystem_enabled: false,
  additional_config: {},
  is_active: true,
  created_by_id: 1,
  created_at: '2024-01-15T10:00:00Z',
  updated_at: null,
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('ExecuteAgentModal', () => {
  const mockOnClose = jest.fn();
  const mockMutateAsync = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    jest.spyOn(useExecutionsHook, 'useExecuteAgent').mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
      data: undefined,
      reset: jest.fn(),
      isIdle: true,
      isSuccess: false,
      mutate: jest.fn(),
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      status: 'idle',
      submittedAt: 0,
      isPaused: false,
    } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders modal when open', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Execute Agent: Test Agent')).toBeInTheDocument();
  });

  it('renders close button', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const closeButton = screen.getByLabelText(/close/i);
    expect(closeButton).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const closeButton = screen.getByLabelText(/close/i);
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('renders prompt textarea', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    expect(promptTextarea).toBeInTheDocument();
  });

  it('allows typing in prompt textarea', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: 'Test prompt' } });

    expect(promptTextarea).toHaveValue('Test prompt');
  });

  it('disables execute button when prompt is empty', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    expect(executeButton).toBeDisabled();
  });

  it('enables execute button when prompt is provided', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: 'Test prompt' } });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    expect(executeButton).toBeEnabled();
  });

  it('calls mutateAsync with correct data when execute is clicked', async () => {
    const mockExecution = { id: 1, status: 'pending' };
    mockMutateAsync.mockResolvedValue(mockExecution);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: 'Test prompt' } });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId: 1,
        prompt: 'Test prompt',
      });
    });
  });

  it('navigates to execution page after successful execution', async () => {
    const mockExecution = { id: 123, status: 'pending' };
    mockMutateAsync.mockResolvedValue(mockExecution);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: 'Test prompt' } });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/executions/123');
    });
  });

  it('closes modal after successful execution', async () => {
    const mockExecution = { id: 123, status: 'pending' };
    mockMutateAsync.mockResolvedValue(mockExecution);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: 'Test prompt' } });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('shows loading state during execution', async () => {
    jest.spyOn(useExecutionsHook, 'useExecuteAgent').mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
      data: undefined,
      reset: jest.fn(),
      isIdle: false,
      isSuccess: false,
      mutate: jest.fn(),
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      status: 'pending',
      submittedAt: 0,
      isPaused: false,
    } as any);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText(/executing/i)).toBeInTheDocument();
  });

  it('displays agent information', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByText(/model:/i)).toBeInTheDocument();
    expect(screen.getByText(/claude-3-5-sonnet-20241022/i)).toBeInTheDocument();
  });

  it('handles execution errors gracefully', async () => {
    const mockError = new Error('Execution failed');
    mockMutateAsync.mockRejectedValue(mockError);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: 'Test prompt' } });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalled();
    });

    // Should not close modal on error
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('trims whitespace from prompt before submission', async () => {
    const mockExecution = { id: 1, status: 'pending' };
    mockMutateAsync.mockResolvedValue(mockExecution);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const promptTextarea = screen.getByPlaceholderText(/enter your prompt/i);
    fireEvent.change(promptTextarea, { target: { value: '  Test prompt  ' } });

    const executeButton = screen.getByRole('button', { name: /execute/i });
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId: 1,
        prompt: 'Test prompt',
      });
    });
  });

  it('disables execute button during execution', () => {
    jest.spyOn(useExecutionsHook, 'useExecuteAgent').mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
      data: undefined,
      reset: jest.fn(),
      isIdle: false,
      isSuccess: false,
      mutate: jest.fn(),
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      status: 'pending',
      submittedAt: 0,
      isPaused: false,
    } as any);

    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const executeButton = screen.getByRole('button', { name: /executing/i });
    expect(executeButton).toBeDisabled();
  });

  it('renders cancel button', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    expect(cancelButton).toBeInTheDocument();
  });

  it('calls onClose when cancel button is clicked', () => {
    render(<ExecuteAgentModal agent={mockAgent} onClose={mockOnClose} />, {
      wrapper: createWrapper(),
    });

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });
});
