/**
 * ToolMarketplace page tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ToolMarketplace } from '../ToolMarketplace';
import { useTools, useDeleteTool } from '../../hooks/useTools';
import { useToast } from '../../hooks/useToast';
import type { Tool } from '../../types/tool';

// Mock hooks
jest.mock('../../hooks/useTools');
jest.mock('../../hooks/useToast');

const mockUseTools = useTools as jest.MockedFunction<typeof useTools>;
const mockUseDeleteTool = useDeleteTool as jest.MockedFunction<typeof useDeleteTool>;
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>;

describe('ToolMarketplace', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const mockSuccess = jest.fn();
  const mockError = jest.fn();
  const mockMutateAsync = jest.fn();

  const mockTools: Tool[] = [
    {
      id: 1,
      name: 'Calculator',
      description: 'Performs mathematical calculations',
      tool_type: 'builtin',
      configuration: { precision: 10 },
      schema_definition: {},
      is_active: true,
      created_by_id: 1,
      created_at: '2025-01-08T12:00:00Z',
      updated_at: '2025-01-08T12:00:00Z',
    },
    {
      id: 2,
      name: 'Web Search',
      description: 'Search the web',
      tool_type: 'custom',
      configuration: null,
      schema_definition: null,
      is_active: true,
      created_by_id: 1,
      created_at: '2025-01-08T12:00:00Z',
      updated_at: '2025-01-08T12:00:00Z',
    },
  ];

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BrowserRouter>
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
    mockUseDeleteTool.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as any);
  });

  describe('Page rendering', () => {
    test('renders page title and description', () => {
      mockUseTools.mockReturnValue({
        data: [],
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      expect(screen.getByText('Tool Marketplace')).toBeInTheDocument();
      expect(screen.getByText('Create and manage tools for your AI agents')).toBeInTheDocument();
    });

    test('renders create tool button', () => {
      mockUseTools.mockReturnValue({
        data: [],
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const createButton = screen.getByRole('button', { name: /create tool/i });
      expect(createButton).toBeInTheDocument();
    });

    test('renders search input', () => {
      mockUseTools.mockReturnValue({
        data: [],
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      expect(searchInput).toBeInTheDocument();
    });

    test('renders type filter dropdown', () => {
      mockUseTools.mockReturnValue({
        data: [],
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const typeFilter = screen.getByRole('combobox');
      expect(typeFilter).toBeInTheDocument();
      expect(screen.getByText('All Types')).toBeInTheDocument();
    });
  });

  describe('Tool list display', () => {
    test('displays tools when data is available', () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      expect(screen.getByText('Calculator')).toBeInTheDocument();
      expect(screen.getByText('Web Search')).toBeInTheDocument();
    });

    test('displays empty state when no tools exist', () => {
      mockUseTools.mockReturnValue({
        data: [],
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      expect(screen.getByText('No tools found')).toBeInTheDocument();
      expect(
        screen.getByText(/create your first tool to get started/i)
      ).toBeInTheDocument();
    });

    test('displays tool count', () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      expect(screen.getByText('Showing 2 tools')).toBeInTheDocument();
    });

    test('uses singular form for single tool', () => {
      mockUseTools.mockReturnValue({
        data: [mockTools[0]],
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      expect(screen.getByText('Showing 1 tool')).toBeInTheDocument();
    });
  });

  describe('Search functionality', () => {
    test('updates search query on input change', () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'Calculator' } });

      expect((searchInput as HTMLInputElement).value).toBe('Calculator');
    });

    test('displays active search filter badge', async () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'Calculator' } });

      await waitFor(() => {
        expect(screen.getByText('Search: Calculator')).toBeInTheDocument();
      });
    });
  });

  describe('Type filtering', () => {
    test('updates selected type on dropdown change', () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const typeFilter = screen.getByRole('combobox');
      fireEvent.change(typeFilter, { target: { value: 'builtin' } });

      expect((typeFilter as HTMLSelectElement).value).toBe('builtin');
    });

    test('displays active type filter badge', async () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const typeFilter = screen.getByRole('combobox');
      fireEvent.change(typeFilter, { target: { value: 'custom' } });

      await waitFor(() => {
        expect(screen.getByText('Type: custom')).toBeInTheDocument();
      });
    });

    test('has all type options available', () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      expect(screen.getByText('All Types')).toBeInTheDocument();
      expect(screen.getByText('Built-in')).toBeInTheDocument();
      expect(screen.getByText('Custom')).toBeInTheDocument();
      expect(screen.getByText('LangGraph')).toBeInTheDocument();
    });
  });

  describe('Clear filters', () => {
    test('shows clear filters button when filters are active', async () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search tools/i);
      fireEvent.change(searchInput, { target: { value: 'test' } });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument();
      });
    });

    test('clears all filters when clear button clicked', async () => {
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const searchInput = screen.getByPlaceholderText(/search tools/i) as HTMLInputElement;
      const typeFilter = screen.getByRole('combobox') as HTMLSelectElement;

      fireEvent.change(searchInput, { target: { value: 'test' } });
      fireEvent.change(typeFilter, { target: { value: 'builtin' } });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument();
      });

      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      fireEvent.click(clearButton);

      expect(searchInput.value).toBe('');
      expect(typeFilter.value).toBe('');
    });
  });

  describe('Delete tool', () => {
    test('shows success message after successful deletion', async () => {
      mockMutateAsync.mockResolvedValueOnce(undefined);
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Tool')).toBeInTheDocument();
      });

      const confirmButton = screen.getAllByRole('button', { name: /delete/i })[0];
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockSuccess).toHaveBeenCalledWith('Tool "Calculator" deleted successfully');
      });
    });

    test('shows error message when deletion fails', async () => {
      mockMutateAsync.mockRejectedValueOnce({
        response: { data: { detail: 'Cannot delete tool in use' } },
      });
      mockUseTools.mockReturnValue({
        data: mockTools,
        isLoading: false,
        isError: false,
      } as any);

      render(<ToolMarketplace />, { wrapper });

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Delete Tool')).toBeInTheDocument();
      });

      // Find the confirmation button in the modal (different from the initial delete buttons)
      const confirmButton = screen.getByRole('button', { name: /^delete$/i });
      fireEvent.click(confirmButton);

      // Wait for mutateAsync to be called first
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });

      // Then wait for error to be called
      await waitFor(() => {
        expect(mockError).toHaveBeenCalledWith('Cannot delete tool in use');
      });
    });
  });
});
