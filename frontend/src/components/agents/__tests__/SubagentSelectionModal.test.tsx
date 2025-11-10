/**
 * SubagentSelectionModal component tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SubagentSelectionModal from '../SubagentSelectionModal';
import { useAgents } from '../../../hooks/useAgents';
import { useAddSubagent } from '../../../hooks/useSubagents';
import type { Agent } from '../../../types/agent';

// Mock hooks
jest.mock('../../../hooks/useAgents');
jest.mock('../../../hooks/useSubagents');

const mockUseAgents = useAgents as jest.MockedFunction<typeof useAgents>;
const mockUseAddSubagent = useAddSubagent as jest.MockedFunction<typeof useAddSubagent>;

describe('SubagentSelectionModal', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const mockOnClose = jest.fn();
  const mockMutateAsync = jest.fn();

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  const mockAgent1: Agent = {
    id: 1,
    name: 'Parent Agent',
    description: 'Parent agent',
    system_prompt: 'You are a helpful assistant',
    model_provider: 'anthropic',
    model_name: 'claude-3-5-sonnet-20241022',
    temperature: 0.7,
    max_tokens: 4096,
    planning_enabled: true,
    filesystem_enabled: false,
    additional_config: {},
    is_active: true,
    created_by_id: 1,
    created_at: '2025-01-08T12:00:00Z',
    updated_at: '2025-01-08T12:00:00Z',
  };

  const mockAgent2: Agent = {
    id: 2,
    name: 'Research Agent',
    description: 'Research specialist',
    system_prompt: 'You are a research specialist',
    model_provider: 'anthropic',
    model_name: 'claude-3-5-sonnet-20241022',
    temperature: 0.7,
    max_tokens: 4096,
    planning_enabled: false,
    filesystem_enabled: false,
    additional_config: {},
    is_active: true,
    created_by_id: 1,
    created_at: '2025-01-08T12:00:00Z',
    updated_at: '2025-01-08T12:00:00Z',
  };

  const mockAgent3: Agent = {
    id: 3,
    name: 'Code Review Agent',
    description: 'Code reviewer',
    system_prompt: 'You are a code reviewer',
    model_provider: 'anthropic',
    model_name: 'claude-3-5-sonnet-20241022',
    temperature: 0.7,
    max_tokens: 4096,
    planning_enabled: false,
    filesystem_enabled: false,
    additional_config: {},
    is_active: true,
    created_by_id: 1,
    created_at: '2025-01-08T12:00:00Z',
    updated_at: '2025-01-08T12:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAgents.mockReturnValue({
      data: [mockAgent1, mockAgent2, mockAgent3],
      isLoading: false,
      isError: false,
    } as any);
    mockUseAddSubagent.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any);
  });

  test('renders when open', () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    expect(screen.getByRole('heading', { name: /add subagent/i })).toBeInTheDocument();
  });

  test('does not render when closed', () => {
    render(
      <SubagentSelectionModal isOpen={false} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    expect(screen.queryByRole('heading', { name: /add subagent/i })).not.toBeInTheDocument();
  });

  test('populates agent dropdown with available agents', () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const select = screen.getByRole('combobox', { name: /subagent/i });
    expect(select).toBeInTheDocument();

    // Should have placeholder and agent options
    expect(screen.getByRole('option', { name: /select an agent/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /research agent/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /code review agent/i })).toBeInTheDocument();
  });

  test('excludes current agent from dropdown', () => {
    render(
      <SubagentSelectionModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        currentAgentName="Parent Agent"
      />,
      { wrapper }
    );

    // Parent Agent (id: 1) should be excluded
    expect(screen.queryByRole('option', { name: /^parent agent$/i })).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: /research agent/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /code review agent/i })).toBeInTheDocument();
  });

  test('shows validation error for required subagent field', async () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const submitButton = screen.getByRole('button', { name: /add subagent/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/subagent is required/i)).toBeInTheDocument();
    });
  });

  test('calls add mutation on form submit with valid data', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      id: 1,
      agent_id: 1,
      subagent_id: 2,
      delegation_prompt: 'You are a specialized research agent',
      priority: 5,
      created_at: '2025-01-08T12:00:00Z',
      subagent: mockAgent2,
    });

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const subagentSelect = screen.getByRole('combobox', { name: /subagent/i });
    const delegationPrompt = screen.getByPlaceholderText(/provide custom instructions/i);
    const priorityInput = screen.getByRole('spinbutton', { name: /priority/i });
    const submitButton = screen.getByRole('button', { name: /add subagent/i });

    fireEvent.change(subagentSelect, { target: { value: '2' } });
    await userEvent.type(delegationPrompt, 'You are a specialized research agent');
    fireEvent.change(priorityInput, { target: { value: '5' } });

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId: 1,
        data: {
          subagent_id: 2,
          delegation_prompt: 'You are a specialized research agent',
          priority: 5,
        },
      });
    });
  });

  test('calls add mutation with default priority when not specified', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      id: 1,
      agent_id: 1,
      subagent_id: 2,
      delegation_prompt: null,
      priority: 0,
      created_at: '2025-01-08T12:00:00Z',
      subagent: mockAgent2,
    });

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const subagentSelect = screen.getByRole('combobox', { name: /subagent/i });
    const submitButton = screen.getByRole('button', { name: /add subagent/i });

    fireEvent.change(subagentSelect, { target: { value: '2' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId: 1,
        data: {
          subagent_id: 2,
          delegation_prompt: '',
          priority: 0,
        },
      });
    });
  });

  test('displays backend error for circular dependency', async () => {
    mockMutateAsync.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Circular dependency detected: adding this subagent would create a cycle',
        },
      },
    });

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const subagentSelect = screen.getByRole('combobox', { name: /subagent/i });
    const submitButton = screen.getByRole('button', { name: /add subagent/i });

    fireEvent.change(subagentSelect, { target: { value: '2' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/circular dependency/i)).toBeInTheDocument();
    });
  });

  test('closes modal after successful submission', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      id: 1,
      agent_id: 1,
      subagent_id: 2,
      delegation_prompt: null,
      priority: 0,
      created_at: '2025-01-08T12:00:00Z',
      subagent: mockAgent2,
    });

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const subagentSelect = screen.getByRole('combobox', { name: /subagent/i });
    const submitButton = screen.getByRole('button', { name: /add subagent/i });

    fireEvent.change(subagentSelect, { target: { value: '2' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  test('clears form on close', async () => {
    const { rerender } = render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const subagentSelect = screen.getByRole('combobox', { name: /subagent/i }) as HTMLSelectElement;
    const delegationPrompt = screen.getByPlaceholderText(/provide custom instructions/i) as HTMLTextAreaElement;

    fireEvent.change(subagentSelect, { target: { value: '2' } });
    await userEvent.type(delegationPrompt, 'Test prompt');

    // Close and reopen
    rerender(
      <SubagentSelectionModal isOpen={false} onClose={mockOnClose} agentId={1} />
    );
    rerender(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />
    );

    // Form should be reset
    const newSubagentSelect = screen.getByRole('combobox', { name: /subagent/i }) as HTMLSelectElement;
    const newDelegationPrompt = screen.getByPlaceholderText(/provide custom instructions/i) as HTMLTextAreaElement;

    expect(newSubagentSelect.value).toBe('');
    expect(newDelegationPrompt.value).toBe('');
  });

  test('validates priority range', async () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const priorityInput = screen.getByRole('spinbutton', { name: /priority/i }) as HTMLInputElement;

    // Test maximum constraint
    expect(priorityInput).toHaveAttribute('max', '100');
    expect(priorityInput).toHaveAttribute('min', '-100');
  });

  test('shows loading state when submitting', async () => {
    mockUseAddSubagent.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any);

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const submitButton = screen.getByRole('button', { name: /adding/i });
    expect(submitButton).toBeDisabled();
  });

  test('displays cancel button', () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    expect(cancelButton).toBeInTheDocument();
  });

  test('closes modal when cancel button clicked', () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('shows helper text for priority field', () => {
    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    expect(screen.getByText(/higher priority subagents are called first/i)).toBeInTheDocument();
  });

  test('handles empty agent list gracefully', () => {
    mockUseAgents.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    } as any);

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    const select = screen.getByRole('combobox', { name: /subagent/i }) as HTMLSelectElement;
    // Should only have the placeholder option
    expect(select.options.length).toBe(1);
  });

  test('shows loading state when agents are loading', () => {
    mockUseAgents.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as any);

    render(
      <SubagentSelectionModal isOpen={true} onClose={mockOnClose} agentId={1} />,
      { wrapper }
    );

    expect(screen.getByText(/loading agents/i)).toBeInTheDocument();
  });
});
