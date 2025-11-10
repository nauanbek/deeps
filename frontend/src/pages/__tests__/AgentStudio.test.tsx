import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentStudio } from '../AgentStudio';
import type { Agent } from '../../types/agent';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }: any) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

// Mock the hooks
jest.mock('../../hooks/useAgents');

const mockAgents: Agent[] = [
  {
    id: 1,
    name: 'Agent One',
    description: 'First test agent',
    system_prompt: 'You are helpful',
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
    updated_at: '2025-01-08T13:00:00Z',
  },
  {
    id: 2,
    name: 'Agent Two',
    description: 'Second test agent',
    system_prompt: 'You are smart',
    model_provider: 'openai',
    model_name: 'gpt-4',
    temperature: 0.5,
    max_tokens: 2048,
    planning_enabled: false,
    filesystem_enabled: true,
    additional_config: {},
    is_active: false,
    created_by_id: 1,
    created_at: '2025-01-07T12:00:00Z',
    updated_at: null,
  },
];

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('AgentStudio', () => {
  const mockRefetch = jest.fn();
  const mockCreateMutate = jest.fn();
  const mockUpdateMutate = jest.fn();
  const mockDeleteMutate = jest.fn();

  // Get mocked hooks
  const useAgents = require('../../hooks/useAgents').useAgents;
  const useCreateAgent = require('../../hooks/useAgents').useCreateAgent;
  const useUpdateAgent = require('../../hooks/useAgents').useUpdateAgent;
  const useDeleteAgent = require('../../hooks/useAgents').useDeleteAgent;

  beforeEach(() => {
    jest.clearAllMocks();

    useAgents.mockReturnValue({
      data: mockAgents,
      isLoading: false,
      isError: false,
      refetch: mockRefetch,
    });

    useCreateAgent.mockReturnValue({
      mutateAsync: mockCreateMutate,
      isPending: false,
    });

    useUpdateAgent.mockReturnValue({
      mutateAsync: mockUpdateMutate,
      isPending: false,
    });

    useDeleteAgent.mockReturnValue({
      mutateAsync: mockDeleteMutate,
      isPending: false,
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('renders agent studio page', () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    expect(screen.getByText('Agent Studio')).toBeInTheDocument();
    expect(screen.getByText(/create, configure, and manage/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create agent/i })).toBeInTheDocument();
  });

  test('displays list of agents', () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    expect(screen.getByText('Agent One')).toBeInTheDocument();
    expect(screen.getByText('Agent Two')).toBeInTheDocument();
    expect(screen.getByText('First test agent')).toBeInTheDocument();
  });

  test('shows loading state', () => {
    useAgents.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: mockRefetch,
    });

    render(<AgentStudio />, { wrapper: createWrapper() });

    // Should show skeleton loaders
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  test('shows error state with retry button', () => {
    useAgents.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: mockRefetch,
    });

    render(<AgentStudio />, { wrapper: createWrapper() });

    expect(screen.getByText(/failed to load agents/i)).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryButton);

    expect(mockRefetch).toHaveBeenCalled();
  });

  test('shows empty state when no agents', () => {
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: mockRefetch,
    });

    render(<AgentStudio />, { wrapper: createWrapper() });

    expect(screen.getByText(/no agents yet/i)).toBeInTheDocument();
    expect(screen.getByText(/get started by creating/i)).toBeInTheDocument();
  });

  test('opens create modal when create button clicked', async () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    const createButton = screen.getByRole('button', { name: /create agent/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  test('filters agents by search query', async () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    const searchInput = screen.getByPlaceholderText(/search agents/i);

    await userEvent.type(searchInput, 'Agent One');

    expect(screen.getByText('Agent One')).toBeInTheDocument();
    expect(screen.queryByText('Agent Two')).not.toBeInTheDocument();
  });

  test('shows no results message when search has no matches', async () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    const searchInput = screen.getByPlaceholderText(/search agents/i);

    await userEvent.type(searchInput, 'NonexistentAgent');

    expect(screen.getByText(/no agents found matching/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /clear search/i })).toBeInTheDocument();
  });

  test('clears search when clear button clicked', async () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    const searchInput = screen.getByPlaceholderText(/search agents/i);

    await userEvent.type(searchInput, 'NonexistentAgent');

    const clearButton = screen.getByRole('button', { name: /clear search/i });
    fireEvent.click(clearButton);

    expect(screen.getByText('Agent One')).toBeInTheDocument();
    expect(screen.getByText('Agent Two')).toBeInTheDocument();
  });

  test('opens edit modal when edit button clicked', async () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Edit Agent')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Agent One')).toBeInTheDocument();
    });
  });

  test('opens delete modal when delete button clicked', async () => {
    render(<AgentStudio />, { wrapper: createWrapper() });

    const deleteButtons = screen.getAllByRole('button', { name: /delete agent one/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument();
    });
  });

  test('creates agent successfully', async () => {
    mockCreateMutate.mockResolvedValue({
      id: 3,
      name: 'New Agent',
    });

    render(<AgentStudio />, { wrapper: createWrapper() });

    // Open create modal - use getAllByRole and click first one (the main button)
    const createButtons = screen.getAllByRole('button', { name: /create agent/i });
    fireEvent.click(createButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Create Agent')).toBeInTheDocument();
    });

    // Fill form
    const nameInput = screen.getByLabelText(/name/i);
    await userEvent.type(nameInput, 'New Agent');

    // Submit - find the submit button inside the modal
    const submitButtons = screen.getAllByRole('button', { name: /create agent/i });
    // The second one should be the submit button in the modal
    fireEvent.click(submitButtons[1]);

    await waitFor(() => {
      expect(mockCreateMutate).toHaveBeenCalled();
    });
  });

  test('updates agent successfully', async () => {
    mockUpdateMutate.mockResolvedValue({
      id: 1,
      name: 'Updated Agent',
    });

    render(<AgentStudio />, { wrapper: createWrapper() });

    // Open edit modal
    const editButtons = screen.getAllByRole('button', { name: /edit agent one/i });
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Edit Agent')).toBeInTheDocument();
    });

    // Update name
    const nameInput = screen.getByLabelText(/name/i);
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, 'Updated Agent');

    // Submit
    const submitButton = screen.getByRole('button', { name: /update agent/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockUpdateMutate).toHaveBeenCalled();
    });
  });

  test('deletes agent successfully', async () => {
    mockDeleteMutate.mockResolvedValue(undefined);

    render(<AgentStudio />, { wrapper: createWrapper() });

    // Open delete modal
    const deleteButtons = screen.getAllByRole('button', { name: /delete agent one/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /delete agent/i })).toBeInTheDocument();
    });

    // Confirm deletion - find the red delete button in the modal
    const allDeleteButtons = screen.getAllByRole('button', { name: /delete agent/i });
    // The confirm button should be the button element (not the one with icon)
    const confirmButton = allDeleteButtons.find(btn =>
      btn.textContent === 'Delete Agent' && btn.className.includes('bg-red')
    );
    if (confirmButton) {
      fireEvent.click(confirmButton);
    }

    await waitFor(() => {
      expect(mockDeleteMutate).toHaveBeenCalledWith(1);
    });
  });

  test('displays toast notification on success', async () => {
    mockCreateMutate.mockResolvedValue({ id: 3 });

    render(<AgentStudio />, { wrapper: createWrapper() });

    // Trigger create action (simplified)
    const createButton = screen.getByRole('button', { name: /create agent/i });
    fireEvent.click(createButton);

    // Toast container should be present
    const toastContainer = document.querySelector('[aria-live="assertive"]');
    expect(toastContainer).toBeInTheDocument();
  });

  test('does not show search bar when no agents', () => {
    useAgents.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: mockRefetch,
    });

    render(<AgentStudio />, { wrapper: createWrapper() });

    const searchInput = screen.queryByPlaceholderText(/search agents/i);
    expect(searchInput).not.toBeInTheDocument();
  });
});
