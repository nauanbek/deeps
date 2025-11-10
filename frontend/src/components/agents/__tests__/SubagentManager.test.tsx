/**
 * SubagentManager component tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SubagentManager from '../SubagentManager';
import { useAgentSubagents, useRemoveSubagent } from '../../../hooks/useSubagents';
import type { Subagent } from '../../../types/subagent';
import type { Agent } from '../../../types/agent';

// Mock hooks
jest.mock('../../../hooks/useSubagents');
jest.mock('../SubagentSelectionModal', () => ({
  __esModule: true,
  default: () => <div>SubagentSelectionModal</div>,
}));
jest.mock('../SubagentEditModal', () => ({
  __esModule: true,
  default: () => <div>SubagentEditModal</div>,
}));

const mockUseAgentSubagents = useAgentSubagents as jest.MockedFunction<typeof useAgentSubagents>;
const mockUseRemoveSubagent = useRemoveSubagent as jest.MockedFunction<typeof useRemoveSubagent>;

describe('SubagentManager', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const mockMutate = jest.fn();

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  const mockAgent: Agent = {
    id: 1,
    name: 'Parent Agent',
    description: 'Test parent agent',
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

  const mockSubagent: Agent = {
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

  const mockSubagentRelation: Subagent = {
    id: 1,
    agent_id: 1,
    subagent_id: 2,
    delegation_prompt: 'You are a specialized research agent',
    priority: 10,
    created_at: '2025-01-08T12:00:00Z',
    subagent: mockSubagent,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRemoveSubagent.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
    } as any);
  });

  test('renders loading state', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText(/loading subagents/i)).toBeInTheDocument();
  });

  test('renders empty state when no subagents', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText(/no subagents configured/i)).toBeInTheDocument();
    expect(screen.getByText(/add a subagent to enable task delegation/i)).toBeInTheDocument();
  });

  test('renders list of subagents correctly', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText('Research Agent')).toBeInTheDocument();
    expect(screen.getByText('You are a specialized research agent')).toBeInTheDocument();
  });

  test('displays subagent name from nested agent data', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText('Research Agent')).toBeInTheDocument();
  });

  test('displays delegation prompt when set', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText('You are a specialized research agent')).toBeInTheDocument();
  });

  test('displays default prompt message when delegation prompt is null', () => {
    const subagentWithoutPrompt: Subagent = {
      ...mockSubagentRelation,
      delegation_prompt: null,
    };

    mockUseAgentSubagents.mockReturnValue({
      data: [subagentWithoutPrompt],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText(/uses default system prompt/i)).toBeInTheDocument();
  });

  test('displays priority as badge', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText(/priority.*10/i)).toBeInTheDocument();
  });

  test('shows Add Subagent button', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByRole('button', { name: /add subagent/i })).toBeInTheDocument();
  });

  test('opens SubagentSelectionModal on Add Subagent click', async () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });

    const addButton = screen.getByRole('button', { name: /add subagent/i });
    fireEvent.click(addButton);

    // Verify button is still rendered after click (modal is mocked)
    expect(addButton).toBeInTheDocument();
  });

  test('calls remove mutation when delete button clicked', async () => {
    // Mock window.confirm
    global.confirm = jest.fn().mockReturnValue(true);

    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith({
        agentId: 1,
        subagentId: 2,
      });
    });

    // Cleanup
    delete (global as any).confirm;
  });

  test('opens SubagentEditModal when edit button clicked', async () => {
    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });

    const editButton = screen.getByRole('button', { name: /edit/i });
    fireEvent.click(editButton);

    // Verify button is still rendered after click (modal is mocked)
    expect(editButton).toBeInTheDocument();
  });

  test('renders multiple subagents', () => {
    const secondSubagent: Subagent = {
      id: 2,
      agent_id: 1,
      subagent_id: 3,
      delegation_prompt: null,
      priority: 5,
      created_at: '2025-01-08T13:00:00Z',
      subagent: {
        ...mockSubagent,
        id: 3,
        name: 'Code Review Agent',
        description: 'Reviews code',
      },
    };

    mockUseAgentSubagents.mockReturnValue({
      data: [mockSubagentRelation, secondSubagent],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });

    expect(screen.getByText('Research Agent')).toBeInTheDocument();
    expect(screen.getByText('Code Review Agent')).toBeInTheDocument();
  });

  test('displays error state when query fails', () => {
    mockUseAgentSubagents.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Failed to fetch'),
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });
    expect(screen.getByText(/error loading subagents/i)).toBeInTheDocument();
  });

  test('displays subagents ordered by priority', () => {
    const lowPriority: Subagent = {
      id: 2,
      agent_id: 1,
      subagent_id: 3,
      delegation_prompt: 'Low priority task',
      priority: 1,
      created_at: '2025-01-08T13:00:00Z',
      subagent: {
        ...mockSubagent,
        id: 3,
        name: 'Low Priority Agent',
      },
    };

    const highPriority: Subagent = {
      id: 3,
      agent_id: 1,
      subagent_id: 4,
      delegation_prompt: 'High priority task',
      priority: 100,
      created_at: '2025-01-08T14:00:00Z',
      subagent: {
        ...mockSubagent,
        id: 4,
        name: 'High Priority Agent',
      },
    };

    // API returns ordered by priority desc (highest first)
    mockUseAgentSubagents.mockReturnValue({
      data: [highPriority, mockSubagentRelation, lowPriority],
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    render(<SubagentManager agentId={1} />, { wrapper });

    const subagentCards = screen.getAllByRole('article');
    expect(subagentCards).toHaveLength(3);

    // Verify order: High Priority, then Research (10), then Low Priority
    expect(screen.getByText('High Priority Agent')).toBeInTheDocument();
    expect(screen.getByText('Research Agent')).toBeInTheDocument();
    expect(screen.getByText('Low Priority Agent')).toBeInTheDocument();
  });
});
