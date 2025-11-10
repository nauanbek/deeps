/**
 * ToolFormModal component tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ToolFormModal from '../ToolFormModal';
import { useCreateTool, useUpdateTool } from '../../../hooks/useTools';
import { useToast } from '../../../hooks/useToast';
import type { Tool } from '../../../types/tool';

// Mock hooks
jest.mock('../../../hooks/useTools');
jest.mock('../../../hooks/useToast');

const mockUseCreateTool = useCreateTool as jest.MockedFunction<typeof useCreateTool>;
const mockUseUpdateTool = useUpdateTool as jest.MockedFunction<typeof useUpdateTool>;
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>;

describe('ToolFormModal', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const mockSuccess = jest.fn();
  const mockError = jest.fn();
  const mockOnClose = jest.fn();
  const mockMutateAsync = jest.fn();

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseToast.mockReturnValue({
      toasts: [],
      addToast: jest.fn(),
      removeToast: jest.fn(),
      success: mockSuccess,
      error: mockError,
      info: jest.fn(),
      warning: jest.fn(),
    });
    mockUseCreateTool.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);
    mockUseUpdateTool.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);
  });

  test('renders create modal title when no tool provided', () => {
    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });
    expect(screen.getByText('Create Tool')).toBeInTheDocument();
  });

  test('renders edit modal title when tool provided', () => {
    const mockTool: Tool = {
      id: 1,
      name: 'Calculator',
      description: 'Math tool',
      tool_type: 'builtin',
      configuration: {},
      schema_definition: {},
      is_active: true,
      created_by_id: 1,
      created_at: '2025-01-08T12:00:00Z',
      updated_at: '2025-01-08T12:00:00Z',
    };

    render(<ToolFormModal isOpen={true} tool={mockTool} onClose={mockOnClose} />, { wrapper });
    expect(screen.getByText('Edit Tool')).toBeInTheDocument();
  });

  test('renders all form fields', () => {
    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  test('renders required field indicators', () => {
    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const requiredIndicators = screen.getAllByText('*');
    expect(requiredIndicators.length).toBeGreaterThan(0);
  });

  test('populates form fields when editing existing tool', () => {
    const mockTool: Tool = {
      id: 1,
      name: 'Calculator',
      description: 'Math tool',
      tool_type: 'custom',
      configuration: {},
      schema_definition: {},
      is_active: true,
      created_by_id: 1,
      created_at: '2025-01-08T12:00:00Z',
      updated_at: '2025-01-08T12:00:00Z',
    };

    render(<ToolFormModal isOpen={true} tool={mockTool} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
    const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement;
    const typeSelect = screen.getByLabelText(/type/i) as HTMLSelectElement;

    expect(nameInput.value).toBe('Calculator');
    expect(descriptionInput.value).toBe('Math tool');
    expect(typeSelect.value).toBe('custom');
  });

  test('displays validation error when name is empty', async () => {
    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /create/i });

    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    });
  });

  test('calls createTool when creating new tool', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      id: 1,
      name: 'New Tool',
      description: 'Test description',
      tool_type: 'custom',
    });

    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const submitButton = screen.getByRole('button', { name: /create/i });

    fireEvent.change(nameInput, { target: { value: 'New Tool' } });
    fireEvent.change(descriptionInput, { target: { value: 'Test description' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        name: 'New Tool',
        description: 'Test description',
        tool_type: 'custom',
        configuration: {},
        schema_definition: {},
      });
    });
  });

  test('calls updateTool when editing existing tool', async () => {
    const mockTool: Tool = {
      id: 1,
      name: 'Calculator',
      description: 'Math tool',
      tool_type: 'builtin',
      configuration: {},
      schema_definition: {},
      is_active: true,
      created_by_id: 1,
      created_at: '2025-01-08T12:00:00Z',
      updated_at: '2025-01-08T12:00:00Z',
    };

    mockMutateAsync.mockResolvedValueOnce(mockTool);

    render(<ToolFormModal isOpen={true} tool={mockTool} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /update/i });

    fireEvent.change(nameInput, { target: { value: 'Updated Calculator' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        id: 1,
        data: expect.objectContaining({
          name: 'Updated Calculator',
        }),
      });
    });
  });

  test('shows success message after creating tool', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      id: 1,
      name: 'New Tool',
      tool_type: 'custom',
    });

    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /create/i });

    fireEvent.change(nameInput, { target: { value: 'New Tool' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSuccess).toHaveBeenCalledWith('Tool created successfully');
    });
  });

  test('shows success message after updating tool', async () => {
    const mockTool: Tool = {
      id: 1,
      name: 'Calculator',
      description: null,
      tool_type: 'builtin',
      configuration: null,
      schema_definition: null,
      is_active: true,
      created_by_id: 1,
      created_at: '2025-01-08T12:00:00Z',
      updated_at: '2025-01-08T12:00:00Z',
    };

    mockMutateAsync.mockResolvedValueOnce(mockTool);

    render(<ToolFormModal isOpen={true} tool={mockTool} onClose={mockOnClose} />, { wrapper });

    const submitButton = screen.getByRole('button', { name: /update/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSuccess).toHaveBeenCalledWith('Tool updated successfully');
    });
  });

  test('shows error message when create fails', async () => {
    mockMutateAsync.mockRejectedValueOnce({
      response: { data: { detail: 'Tool already exists' } },
    });

    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /create/i });

    fireEvent.change(nameInput, { target: { value: 'Duplicate Tool' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockError).toHaveBeenCalledWith('Tool already exists');
    });
  });

  test('closes modal after successful submission', async () => {
    mockMutateAsync.mockResolvedValueOnce({
      id: 1,
      name: 'New Tool',
      tool_type: 'custom',
    });

    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i);
    const submitButton = screen.getByRole('button', { name: /create/i });

    fireEvent.change(nameInput, { target: { value: 'New Tool' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  test('calls onClose when cancel button clicked', () => {
    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('disables form inputs while submitting', async () => {
    mockMutateAsync.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({} as any), 100))
    );

    render(<ToolFormModal isOpen={true} onClose={mockOnClose} />, { wrapper });

    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
    const submitButton = screen.getByRole('button', { name: /create/i });

    fireEvent.change(nameInput, { target: { value: 'Test Tool' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(nameInput).toBeDisabled();
    });
  });
});
