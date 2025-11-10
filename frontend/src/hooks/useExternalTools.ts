import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { externalToolsApi } from '../api/externalTools';
import type {
  ExternalToolConfigCreate,
  ExternalToolConfigUpdate,
  ExternalToolFilters,
  ConnectionTestRequest,
} from '../types/externalTool';

/**
 * Hook to fetch all external tool configurations
 */
export const useExternalTools = (filters?: ExternalToolFilters) => {
  return useQuery({
    queryKey: ['externalTools', filters],
    queryFn: () => externalToolsApi.getAll(filters),
  });
};

/**
 * Hook to fetch a single external tool configuration by ID
 */
export const useExternalTool = (id: number) => {
  return useQuery({
    queryKey: ['externalTools', id],
    queryFn: () => externalToolsApi.getById(id),
    enabled: !!id && id > 0,
  });
};

/**
 * Hook to create a new external tool configuration
 */
export const useCreateExternalTool = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExternalToolConfigCreate) => externalToolsApi.create(data),
    onSuccess: () => {
      // Invalidate all tool queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['externalTools'] });
      queryClient.invalidateQueries({ queryKey: ['toolCatalog'] });
    },
  });
};

/**
 * Hook to update an external tool configuration
 */
export const useUpdateExternalTool = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ExternalToolConfigUpdate }) =>
      externalToolsApi.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate the specific tool and the list
      queryClient.invalidateQueries({ queryKey: ['externalTools'] });
      queryClient.invalidateQueries({ queryKey: ['externalTools', variables.id] });
    },
  });
};

/**
 * Hook to delete an external tool configuration
 */
export const useDeleteExternalTool = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => externalToolsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['externalTools'] });
    },
  });
};

/**
 * Hook to test connection to an external tool
 */
export const useTestConnection = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: number; request?: ConnectionTestRequest }) =>
      externalToolsApi.testConnection(id, request),
    onSuccess: (_, variables) => {
      // Invalidate the specific tool to refresh test status
      queryClient.invalidateQueries({ queryKey: ['externalTools', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['externalTools'] });
    },
  });
};

/**
 * Hook to fetch tool catalog (marketplace)
 */
export const useToolCatalog = () => {
  return useQuery({
    queryKey: ['toolCatalog'],
    queryFn: externalToolsApi.getCatalog,
    // Cache for 5 minutes since catalog doesn't change often
    staleTime: 5 * 60 * 1000,
  });
};

/**
 * Hook to fetch tool usage analytics
 */
export const useToolAnalytics = (days: number = 30) => {
  return useQuery({
    queryKey: ['toolAnalytics', days],
    queryFn: () => externalToolsApi.getAnalytics(days),
    // Refetch every 30 seconds for analytics
    refetchInterval: 30000,
  });
};

/**
 * Hook to get count of external tools
 */
export const useExternalToolsCount = (filters?: ExternalToolFilters) => {
  return useQuery({
    queryKey: ['externalTools', 'count', filters],
    queryFn: () => externalToolsApi.getCount(filters),
  });
};

/**
 * Hook to fetch active external tools only
 */
export const useActiveExternalTools = () => {
  return useExternalTools({ is_active: true });
};

/**
 * Hook to fetch external tools by type
 */
export const useExternalToolsByType = (toolType: string) => {
  return useExternalTools({ tool_type: toolType as any });
};
