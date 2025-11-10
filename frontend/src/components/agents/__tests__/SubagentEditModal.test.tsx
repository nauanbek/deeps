/**
 * SubagentEditModal component tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SubagentEditModal from '../SubagentEditModal';
import { useUpdateSubagent } from '../../../hooks/useSubagents';
import type { Subagent } from '../../../types/subagent';
import type { Agent } from '../../../types/agent';

// Mock hooks
jest.mock('../../../hooks/useSubagents');

const mockUseUpdateSubagent = useUpdateSubagent as jest.MockedFunction<typeof useUpdateSubagent>;

describe('SubagentEditModal', () => {
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

  const mockSubagentAgent: Agent = {
    id: 2,
    name: 'Research Agent',
    description: 'Specialized research agent',
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

  const mockSubagent: Subagent = {
    id: 1,
    agent_id: 1,
    subagent_id: 2,
    delegation_prompt: 'You are a specialized research agent',
    priority: 10,
    created_at: '2025-01-08T12:00:00Z',
    subagent: mockSubagentAgent,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseUpdateSubagent.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    } as any);
  });

  test('renders with existing values pre-populated', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    expect(screen.getByRole('heading', { name: /edit subagent/i })).toBeInTheDocument();

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i) as HTMLTextAreaElement;
    const priorityInput = screen.getByLabelText(/priority/i) as HTMLInputElement;

    expect(delegationPrompt.value).toBe('You are a specialized research agent');
    expect(priorityInput.value).toBe('10');
  });

  test('shows subagent name as read-only', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    expect(screen.getByText('Research Agent')).toBeInTheDocument();
    // Should not have a select or input for subagent name
    expect(screen.queryByLabelText(/^subagent$/i)).not.toBeInTheDocument();
  });

  test('allows editing delegation prompt', async () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i) as HTMLTextAreaElement;

    await userEvent.clear(delegationPrompt);
    await userEvent.type(delegationPrompt, 'Updated delegation instructions');

    expect(delegationPrompt.value).toBe('Updated delegation instructions');
  });

  test('allows editing priority', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const priorityInput = screen.getByLabelText(/priority/i) as HTMLInputElement;

    fireEvent.change(priorityInput, { target: { value: '20' } });

    expect(priorityInput.value).toBe('20');
  });

  test('calls update mutation on submit', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      ...mockSubagent,
      delegation_prompt: 'Updated prompt',
      priority: 15,
    });

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i);
    const priorityInput = screen.getByLabelText(/priority/i);
    const submitButton = screen.getByRole('button', { name: /update/i });

    await userEvent.clear(delegationPrompt);
    await userEvent.type(delegationPrompt, 'Updated prompt');
    fireEvent.change(priorityInput, { target: { value: '15' } });

    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId: 1,
        subagentId: 2,
        data: {
          delegation_prompt: 'Updated prompt',
          priority: 15,
        },
      });
    });
  });

  test('displays backend errors', async () => {
    mockMutateAsync.mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Invalid priority value',
        },
      },
    });

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const submitButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid priority value/i)).toBeInTheDocument();
    });
  });

  test('closes modal after successful update', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      ...mockSubagent,
      delegation_prompt: 'Updated prompt',
    });

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const submitButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  test('does not render when closed', () => {
    render(
      <SubagentEditModal
        isOpen={false}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    expect(screen.queryByRole('heading', { name: /edit subagent/i })).not.toBeInTheDocument();
  });

  test('displays cancel button', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  test('closes modal when cancel button clicked', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('shows loading state when submitting', () => {
    mockUseUpdateSubagent.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any);

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const submitButton = screen.getByRole('button', { name: /updating/i });
    expect(submitButton).toBeDisabled();
  });

  test('validates priority range', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const priorityInput = screen.getByLabelText(/priority/i) as HTMLInputElement;

    expect(priorityInput).toHaveAttribute('max', '100');
    expect(priorityInput).toHaveAttribute('min', '-100');
  });

  test('handles empty delegation prompt', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      ...mockSubagent,
      delegation_prompt: '',
    });

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i);
    const submitButton = screen.getByRole('button', { name: /update/i });

    await userEvent.clear(delegationPrompt);
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId: 1,
        subagentId: 2,
        data: {
          delegation_prompt: '',
          priority: 10,
        },
      });
    });
  });

  test('handles null delegation prompt in initial data', () => {
    const subagentWithNullPrompt: Subagent = {
      ...mockSubagent,
      delegation_prompt: null,
    };

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={subagentWithNullPrompt}
      />,
      { wrapper }
    );

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i) as HTMLTextAreaElement;
    expect(delegationPrompt.value).toBe('');
  });

  test('disables form fields while submitting', () => {
    mockUseUpdateSubagent.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: true,
      isError: false,
      error: null,
    } as any);

    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i) as HTMLTextAreaElement;
    const priorityInput = screen.getByLabelText(/priority/i) as HTMLInputElement;

    expect(delegationPrompt).toBeDisabled();
    expect(priorityInput).toBeDisabled();
  });

  test('shows helper text for priority field', () => {
    render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    expect(screen.getByText(/higher priority subagents are called first/i)).toBeInTheDocument();
  });

  test('updates form when subagent prop changes', async () => {
    const { rerender } = render(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={mockSubagent}
      />,
      { wrapper }
    );

    const delegationPrompt = screen.getByLabelText(/delegation prompt/i) as HTMLTextAreaElement;
    expect(delegationPrompt.value).toBe('You are a specialized research agent');

    const updatedSubagent: Subagent = {
      ...mockSubagent,
      delegation_prompt: 'Different prompt',
      priority: 5,
    };

    rerender(
      <SubagentEditModal
        isOpen={true}
        onClose={mockOnClose}
        agentId={1}
        subagent={updatedSubagent}
      />
    );

    await waitFor(() => {
      const updatedDelegationPrompt = screen.getByLabelText(
        /delegation prompt/i
      ) as HTMLTextAreaElement;
      expect(updatedDelegationPrompt.value).toBe('Different prompt');
    });
  });
});
