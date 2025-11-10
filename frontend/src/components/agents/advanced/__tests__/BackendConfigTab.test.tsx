import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import BackendConfigTab from '../BackendConfigTab';

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
  loader: {
    init: jest.fn().mockResolvedValue({}),
    config: jest.fn(),
  },
}));

// Mock hooks
jest.mock('../../../../hooks/useAdvancedConfig', () => ({
  useBackendConfig: jest.fn(),
  useCreateBackendConfig: jest.fn(),
  useUpdateBackendConfig: jest.fn(),
  useDeleteBackendConfig: jest.fn(),
}));

import {
  useBackendConfig,
  useCreateBackendConfig,
  useUpdateBackendConfig,
  useDeleteBackendConfig,
} from '../../../../hooks/useAdvancedConfig';

const mockUseBackendConfig = useBackendConfig as jest.MockedFunction<typeof useBackendConfig>;
const mockUseCreateBackendConfig = useCreateBackendConfig as jest.MockedFunction<typeof useCreateBackendConfig>;
const mockUseUpdateBackendConfig = useUpdateBackendConfig as jest.MockedFunction<typeof useUpdateBackendConfig>;
const mockUseDeleteBackendConfig = useDeleteBackendConfig as jest.MockedFunction<typeof useDeleteBackendConfig>;

describe('BackendConfigTab', () => {
  let queryClient: QueryClient;
  const mockOnSuccess = jest.fn();
  const mockOnError = jest.fn();
  const agentId = 1;

  beforeEach(() => {
    jest.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Default mock implementations
    mockUseBackendConfig.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    } as any);

    mockUseCreateBackendConfig.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    } as any);

    mockUseUpdateBackendConfig.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    } as any);

    mockUseDeleteBackendConfig.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({}),
      isPending: false,
    } as any);
  });

  const renderComponent = () =>
    render(
      <QueryClientProvider client={queryClient}>
        <BackendConfigTab
          agentId={agentId}
          onSuccess={mockOnSuccess}
          onError={mockOnError}
        />
      </QueryClientProvider>
    );

  test('renders loading state', () => {
    mockUseBackendConfig.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    } as any);

    renderComponent();

    expect(screen.getByText(/loading backend configuration/i)).toBeInTheDocument();
  });

  test('renders empty state when no config exists', () => {
    renderComponent();

    expect(screen.getByText(/backend storage configuration/i)).toBeInTheDocument();
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  test('renders existing backend config', () => {
    const existingConfig = {
      backend_type: 'filesystem',
      config: { root_dir: '/workspace', virtual_mode: true },
    };

    mockUseBackendConfig.mockReturnValue({
      data: existingConfig,
      isLoading: false,
      isError: false,
    } as any);

    renderComponent();

    expect(screen.getByText(/backend configuration is active/i)).toBeInTheDocument();
    // Check for the backend type in the JSON editor
    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    expect(editor.value).toContain('filesystem');
  });

  test('loads state example', async () => {
    renderComponent();

    const stateButton = screen.getByRole('button', { name: /state/i });
    await userEvent.click(stateButton);

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    await waitFor(() => {
      const value = editor.value;
      expect(value).toBeTruthy();
      const parsed = JSON.parse(value);
      expect(parsed.backend_type).toBe('state');
    });
  });

  test('loads filesystem example', async () => {
    renderComponent();

    const filesystemButton = screen.getByRole('button', { name: /filesystem/i });
    await userEvent.click(filesystemButton);

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    await waitFor(() => {
      const value = editor.value;
      expect(value).toBeTruthy();
      const parsed = JSON.parse(value);
      expect(parsed.backend_type).toBe('filesystem');
    });
  });

  test('loads store example', async () => {
    renderComponent();

    const storeButton = screen.getByRole('button', { name: /store/i });
    await userEvent.click(storeButton);

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    await waitFor(() => {
      const value = editor.value;
      expect(value).toBeTruthy();
      const parsed = JSON.parse(value);
      expect(parsed.backend_type).toBe('store');
    });
  });

  test('loads composite example', async () => {
    renderComponent();

    const compositeButton = screen.getByRole('button', { name: /composite/i });
    await userEvent.click(compositeButton);

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    await waitFor(() => {
      const value = editor.value;
      expect(value).toBeTruthy();
      const parsed = JSON.parse(value);
      expect(parsed.backend_type).toBe('composite');
    });
  });

  test('creates new backend config on save', async () => {
    const mockMutateAsync = jest.fn().mockResolvedValue({});
    mockUseCreateBackendConfig.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);

    renderComponent();

    // Load an example
    const stateButton = screen.getByRole('button', { name: /state/i });
    await userEvent.click(stateButton);

    // Save
    const saveButton = screen.getByRole('button', { name: /create configuration/i });
    await userEvent.click(saveButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId,
        data: expect.objectContaining({ backend_type: 'state' }),
      });
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  test('updates existing backend config', async () => {
    const existingConfig = {
      backend_type: 'state',
      config: {},
    };

    mockUseBackendConfig.mockReturnValue({
      data: existingConfig,
      isLoading: false,
      isError: false,
    } as any);

    const mockMutateAsync = jest.fn().mockResolvedValue({});
    mockUseUpdateBackendConfig.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);

    renderComponent();

    // Load filesystem example
    const filesystemButton = screen.getByRole('button', { name: /filesystem/i });
    await userEvent.click(filesystemButton);

    // Save (should update)
    const saveButton = screen.getByRole('button', { name: /update configuration/i });
    await userEvent.click(saveButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        agentId,
        data: expect.objectContaining({ backend_type: 'filesystem' }),
      });
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  test('deletes backend config', async () => {
    const existingConfig = {
      backend_type: 'filesystem',
      config: {},
    };

    mockUseBackendConfig.mockReturnValue({
      data: existingConfig,
      isLoading: false,
      isError: false,
    } as any);

    const mockMutateAsync = jest.fn().mockResolvedValue({});
    mockUseDeleteBackendConfig.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);

    // Mock window.confirm
    global.confirm = jest.fn().mockReturnValue(true);

    renderComponent();

    const deleteButton = screen.getByRole('button', { name: /delete configuration/i });
    await userEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(agentId);
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  test('resets editor to initial state', async () => {
    renderComponent();

    // Load an example
    const filesystemButton = screen.getByRole('button', { name: /filesystem/i });
    await userEvent.click(filesystemButton);

    // Reset
    const resetButton = screen.getByRole('button', { name: /reset/i });
    await userEvent.click(resetButton);

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    await waitFor(() => {
      const value = editor.value;
      expect(value).toBeTruthy();
      const parsed = JSON.parse(value);
      expect(parsed.backend_type).toBe('state');
    });
  });

  test('handles save error', async () => {
    const mockMutateAsync = jest.fn().mockRejectedValue({
      response: { data: { detail: 'Save failed' } },
    });
    mockUseCreateBackendConfig.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);

    renderComponent();

    const stateButton = screen.getByRole('button', { name: /state/i });
    await userEvent.click(stateButton);

    const saveButton = screen.getByRole('button', { name: /create configuration/i });
    await userEvent.click(saveButton);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('Save failed');
    });
  });

  test('disables save button for invalid JSON', async () => {
    renderComponent();

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;

    // Directly set invalid JSON without userEvent to avoid special char issues
    fireEvent.change(editor, { target: { value: 'invalid json' } });

    const saveButton = screen.getByRole('button', { name: /create configuration/i });
    await waitFor(() => {
      expect(saveButton).toBeDisabled();
    });
  });

  test('shows info boxes for backend types', () => {
    renderComponent();

    expect(screen.getByText(/backend types:/i)).toBeInTheDocument();
    expect(screen.getByText(/state:/i)).toBeInTheDocument();
    expect(screen.getByText(/filesystem:/i)).toBeInTheDocument();
    expect(screen.getByText(/store:/i)).toBeInTheDocument();
    expect(screen.getByText(/composite:/i)).toBeInTheDocument();
  });
});
