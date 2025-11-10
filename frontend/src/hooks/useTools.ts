/**
 * React Query hooks for Tool management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTools, getTool, createTool, updateTool, deleteTool, getToolCategories } from '../api/tools';
import type { ToolCreate, ToolUpdate, ToolFilters } from '../types/tool';

/**
 * Hook to fetch list of tools with optional filters
 */
export const useTools = (params?: ToolFilters) => {
  return useQuery({
    queryKey: ['tools', params],
    queryFn: () => getTools(params),
    staleTime: 30000, // Cache for 30 seconds
  });
};

/**
 * Hook to fetch a single tool by ID
 */
export const useTool = (id: number) => {
  return useQuery({
    queryKey: ['tools', id],
    queryFn: () => getTool(id),
    enabled: !!id && id > 0,
    staleTime: 60000, // Cache for 1 minute
  });
};

/**
 * Hook to fetch tool categories/types
 */
export const useToolCategories = () => {
  return useQuery({
    queryKey: ['tools', 'categories'],
    queryFn: getToolCategories,
    staleTime: 300000, // Cache for 5 minutes (categories rarely change)
  });
};

/**
 * Hook to create a new tool
 */
export const useCreateTool = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ToolCreate) => createTool(data),
    onSuccess: () => {
      // Invalidate all tool queries to refetch
      queryClient.invalidateQueries({ queryKey: ['tools'] });
    },
  });
};

/**
 * Hook to update an existing tool
 */
export const useUpdateTool = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ToolUpdate }) =>
      updateTool(id, data),
    onSuccess: (updatedTool) => {
      // Invalidate all tool queries
      queryClient.invalidateQueries({ queryKey: ['tools'] });
      // Optionally update the cache for the specific tool
      queryClient.setQueryData(['tools', updatedTool.id], updatedTool);
    },
  });
};

/**
 * Hook to delete a tool
 */
export const useDeleteTool = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, hardDelete }: { id: number; hardDelete?: boolean }) =>
      deleteTool(id, hardDelete),
    onSuccess: () => {
      // Invalidate all tool queries to refetch
      queryClient.invalidateQueries({ queryKey: ['tools'] });
    },
  });
};
